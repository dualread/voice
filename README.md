# Edge-TTS 单词列表转 MP3 工具

使用 Microsoft Edge TTS 将中英文单词列表文件转换为 MP3 音频文件，适合语言学习和背单词。

## 功能特点

- 🎯 自动朗读中文和英文
- 🔊 高质量 Microsoft Edge 神经网络语音
- ⏸️ 单词之间自动添加停顿
- 📁 支持批量转换整个目录
- 🎛️ 可自定义语音和语速

## 安装依赖

```bash
pip install edge-tts
```

还需要安装 ffmpeg（用于合并音频）：

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 ffmpeg 并添加到 PATH
```

## 使用方法

### 基本用法

```bash
# 转换单个文件（生成同名 .mp3 文件）
python convert_words_to_mp3.py words.txt

# 输出：words.mp3
```

### 批量转换

```bash
# 转换目录下所有 txt 文件
python convert_words_to_mp3.py -d ./wordlists
```

### 指定输出文件

```bash
python convert_words_to_mp3.py words.txt -o output.mp3
```

### 查看可用语音

```bash
python convert_words_to_mp3.py --list-voices
```

### 自定义语音

```bash
# 使用男声
python convert_words_to_mp3.py words.txt --zh-voice zh-CN-YunxiNeural --en-voice en-US-GuyNeural
```

## 输入文件格式

每行一个单词，格式为 `中文 英文`（用空格分隔）：

```
苹果 apple
香蕉 banana
橙子 orange
葡萄 grape
西瓜 watermelon
```

- 支持 `#` 开头的注释行
- 自动跳过空行
- 支持 UTF-8 编码

## 输出格式

生成的 MP3 音频按以下顺序朗读：

```
中文 → [短停顿] → 英文 → [长停顿] → 下一个单词...
```

## 默认语音设置

| 语言 | 默认语音 |
|------|----------|
| 中文 | zh-CN-XiaoxiaoNeural (女声) |
| 英文 | en-US-JennyNeural (女声) |

## 常用中文语音

- `zh-CN-XiaoxiaoNeural` - 晓晓（女声，默认）
- `zh-CN-YunxiNeural` - 云希（男声）
- `zh-CN-YunjianNeural` - 云健（男声）
- `zh-CN-XiaoyiNeural` - 晓伊（女声）

## 常用英文语音

- `en-US-JennyNeural` - Jenny（女声，默认）
- `en-US-GuyNeural` - Guy（男声）
- `en-US-AriaNeural` - Aria（女声）
- `en-GB-SoniaNeural` - Sonia（英式女声）

## 示例

```bash
# 创建单词文件
cat > my_words.txt << EOF
你好 hello
谢谢 thank you
再见 goodbye
EOF

# 转换为 MP3
python convert_words_to_mp3.py my_words.txt

# 播放生成的音频
ffplay my_words.mp3
```

## License

MIT
