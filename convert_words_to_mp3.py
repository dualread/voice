#!/usr/bin/env python3
"""
使用 Edge-TTS 将单词列表文件转换为 MP3 文件
输入格式: 中文 英文 (每行一个单词，中文和英文用空格分隔)
输出: 与输入文件同名的 MP3 文件
"""

import asyncio
import edge_tts
import os
import sys
import argparse
from pathlib import Path


# 语音设置
CHINESE_VOICE = "zh-CN-XiaoxiaoNeural"  # 中文女声
ENGLISH_VOICE = "en-US-JennyNeural"      # 英文女声

# 语速设置 (可调整: -50% 到 +50%)
RATE = "-10%"

# 单词之间的停顿时间（毫秒）
PAUSE_BETWEEN_WORDS = 800
# 中英文之间的停顿时间（毫秒）
PAUSE_BETWEEN_LANGUAGES = 500

# 重试次数
MAX_RETRIES = 3


async def text_to_speech(text: str, voice: str, output_file: str):
    """将文本转换为语音并保存为文件，带重试机制"""
    for attempt in range(MAX_RETRIES):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=RATE)
            await communicate.save(output_file)
            return True
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"    重试 ({attempt + 1}/{MAX_RETRIES}): {text}")
                await asyncio.sleep(1)  # 等待1秒后重试
            else:
                print(f"    警告: 无法生成音频 '{text}': {e}")
                # 生成一个静音文件作为替代
                await generate_silence(output_file, 100)
                return False
    return False


async def generate_word_audio(chinese: str, english: str, output_file: str, temp_dir: str):
    """生成单个单词的音频（中文 + 英文）"""
    chinese_file = os.path.join(temp_dir, "chinese_temp.mp3")
    english_file = os.path.join(temp_dir, "english_temp.mp3")
    
    # 生成中文和英文音频
    await asyncio.gather(
        text_to_speech(chinese, CHINESE_VOICE, chinese_file),
        text_to_speech(english, ENGLISH_VOICE, english_file)
    )
    
    return chinese_file, english_file


def parse_word_file(file_path: str) -> list:
    """解析单词文件，返回 [(中文, 英文), ...] 列表
    如果一行只有中文（如文件标题），则英文部分为None
    """
    words = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):  # 跳过空行和注释
                continue
            
            # 用空格分割，第一部分是中文，其余是英文
            parts = line.split(None, 1)  # 最多分成2部分
            if len(parts) >= 2:
                chinese, english = parts[0], parts[1]
                words.append((chinese, english))
            elif len(parts) == 1:
                # 只有中文（如文件标题），英文为None
                words.append((parts[0], None))
    
    return words


async def convert_file_to_mp3(input_file: str, output_file: str = None):
    """将单词列表文件转换为 MP3"""
    import tempfile
    import subprocess
    
    # 确定输出文件名
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".mp3"
    
    print(f"正在处理: {input_file}")
    print(f"输出文件: {output_file}")
    
    # 解析单词文件
    words = parse_word_file(input_file)
    if not words:
        print("错误: 文件中没有有效的单词")
        return False
    
    print(f"共找到 {len(words)} 个单词")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_files = []
        silence_file = os.path.join(temp_dir, "silence.mp3")
        short_silence_file = os.path.join(temp_dir, "short_silence.mp3")
        
        # 生成静音文件
        await generate_silence(silence_file, PAUSE_BETWEEN_WORDS)
        await generate_silence(short_silence_file, PAUSE_BETWEEN_LANGUAGES)
        
        # 处理每个单词
        for i, (chinese, english) in enumerate(words):
            if english is None:
                # 只有中文（如文件标题）
                print(f"处理中 ({i+1}/{len(words)}): {chinese}")
                chinese_file = os.path.join(temp_dir, f"word_{i}_zh.mp3")
                await text_to_speech(chinese, CHINESE_VOICE, chinese_file)
                audio_files.append(chinese_file)
            else:
                # 中英双语
                print(f"处理中 ({i+1}/{len(words)}): {chinese} - {english}")
                chinese_file = os.path.join(temp_dir, f"word_{i}_zh.mp3")
                english_file = os.path.join(temp_dir, f"word_{i}_en.mp3")
                
                # 生成中英文音频
                await asyncio.gather(
                    text_to_speech(chinese, CHINESE_VOICE, chinese_file),
                    text_to_speech(english, ENGLISH_VOICE, english_file)
                )
                
                # 添加到文件列表: 中文 + 短停顿 + 英文
                audio_files.append(chinese_file)
                audio_files.append(short_silence_file)
                audio_files.append(english_file)
            
            # 单词之间加长停顿（最后一个除外）
            if i < len(words) - 1:
                audio_files.append(silence_file)
        
        # 合并所有音频文件
        print("正在合并音频文件...")
        await merge_audio_files(audio_files, output_file, temp_dir)
    
    print(f"转换完成: {output_file}")
    return True


async def generate_silence(output_file: str, duration_ms: int):
    """生成指定时长的静音文件"""
    # 使用 ffmpeg 生成静音
    import subprocess
    duration_sec = duration_ms / 1000
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-q:a", "9",
        output_file
    ]
    subprocess.run(cmd, capture_output=True, check=True)


async def merge_audio_files(audio_files: list, output_file: str, temp_dir: str):
    """使用 ffmpeg 合并多个音频文件"""
    import subprocess
    
    # 创建文件列表
    list_file = os.path.join(temp_dir, "filelist.txt")
    with open(list_file, 'w', encoding='utf-8') as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")
    
    # 使用 ffmpeg 合并
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_file
    ]
    subprocess.run(cmd, capture_output=True, check=True)


async def process_directory(directory: str):
    """处理目录下所有的 .txt 文件"""
    txt_files = list(Path(directory).glob("*.txt"))
    if not txt_files:
        print(f"在目录 {directory} 中没有找到 .txt 文件")
        return
    
    print(f"找到 {len(txt_files)} 个 txt 文件")
    
    for txt_file in txt_files:
        await convert_file_to_mp3(str(txt_file))
        print()


async def main():
    global CHINESE_VOICE, ENGLISH_VOICE
    
    parser = argparse.ArgumentParser(
        description="使用 Edge-TTS 将单词列表文件转换为 MP3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s words.txt              # 转换单个文件
  %(prog)s -d ./wordlists         # 转换目录下所有 txt 文件
  %(prog)s words.txt -o output.mp3  # 指定输出文件名

输入文件格式 (每行一个单词):
  苹果 apple
  香蕉 banana
  橙子 orange
        """
    )
    parser.add_argument("input", nargs="?", help="输入的 txt 文件路径")
    parser.add_argument("-d", "--directory", help="处理整个目录下的所有 txt 文件")
    parser.add_argument("-o", "--output", help="输出文件路径 (默认与输入文件同名)")
    parser.add_argument("--zh-voice", default=CHINESE_VOICE, help=f"中文语音 (默认: {CHINESE_VOICE})")
    parser.add_argument("--en-voice", default=ENGLISH_VOICE, help=f"英文语音 (默认: {ENGLISH_VOICE})")
    parser.add_argument("--list-voices", action="store_true", help="列出所有可用的语音")
    
    args = parser.parse_args()
    
    # 列出可用语音
    if args.list_voices:
        print("正在获取可用语音列表...")
        voices = await edge_tts.list_voices()
        print("\n中文语音:")
        for v in voices:
            if v["Locale"].startswith("zh"):
                print(f"  {v['ShortName']}: {v['FriendlyName']}")
        print("\n英文语音:")
        for v in voices:
            if v["Locale"].startswith("en"):
                print(f"  {v['ShortName']}: {v['FriendlyName']}")
        return
    
    # 更新语音设置
    CHINESE_VOICE = args.zh_voice
    ENGLISH_VOICE = args.en_voice
    
    # 处理目录
    if args.directory:
        await process_directory(args.directory)
        return
    
    # 处理单个文件
    if not args.input:
        parser.print_help()
        return
    
    if not os.path.exists(args.input):
        print(f"错误: 文件不存在: {args.input}")
        sys.exit(1)
    
    await convert_file_to_mp3(args.input, args.output)


if __name__ == "__main__":
    asyncio.run(main())
