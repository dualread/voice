#!/usr/bin/env python3
"""
使用NLTK的WordNet对朗文3000词汇进行语义分类
将单词按词义分类，每个类别最多60个单词，保存到以中文命名的文件中
包含中英双语翻译
"""

import os
import json
from collections import defaultdict

# 使用nltk进行词义分析
try:
    import nltk
    from nltk.corpus import wordnet as wn
except ImportError:
    print("正在安装nltk...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'nltk'])
    import nltk
    from nltk.corpus import wordnet as wn

# 使用deep_translator进行翻译（免费且稳定）
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("正在安装deep_translator...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator

# 下载必要的wordnet数据
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

# 定义WordNet顶级语义域到中文的映射
# WordNet使用lexicographer files来组织同义词集
LEXNAME_TO_CHINESE = {
    # 名词类别
    'noun.Tops': '基础概念',
    'noun.act': '行为动作',
    'noun.animal': '动物',
    'noun.artifact': '人造物品',
    'noun.attribute': '属性特征',
    'noun.body': '身体部位',
    'noun.cognition': '认知思维',
    'noun.communication': '交流通讯',
    'noun.event': '事件',
    'noun.feeling': '情感感受',
    'noun.food': '食物饮品',
    'noun.group': '群体组织',
    'noun.location': '地点位置',
    'noun.motive': '动机目的',
    'noun.object': '自然物体',
    'noun.person': '人物角色',
    'noun.phenomenon': '自然现象',
    'noun.plant': '植物',
    'noun.possession': '财产所有',
    'noun.process': '过程变化',
    'noun.quantity': '数量度量',
    'noun.relation': '关系',
    'noun.shape': '形状',
    'noun.state': '状态情况',
    'noun.substance': '物质材料',
    'noun.time': '时间',
    # 动词类别
    'verb.body': '身体动作',
    'verb.change': '变化改变',
    'verb.cognition': '思考认知',
    'verb.communication': '言语交流',
    'verb.competition': '竞争比赛',
    'verb.consumption': '消费使用',
    'verb.contact': '接触动作',
    'verb.creation': '创造制作',
    'verb.emotion': '情感表达',
    'verb.motion': '移动运动',
    'verb.perception': '感知感觉',
    'verb.possession': '拥有获取',
    'verb.social': '社会交往',
    'verb.stative': '状态描述',
    'verb.weather': '天气相关',
    # 形容词类别
    'adj.all': '形容词通用',
    'adj.pert': '形容词关系',
    'adj.ppl': '分词形容词',
    # 副词类别
    'adv.all': '副词',
}

# 合并相似类别的映射
CATEGORY_MERGE = {
    '基础概念': '基础词汇',
    '行为动作': '行为动作',
    '动物': '动物自然',
    '人造物品': '日常物品',
    '属性特征': '属性特征',
    '身体部位': '身体健康',
    '认知思维': '思维认知',
    '交流通讯': '语言交流',
    '事件': '事件活动',
    '情感感受': '情感心理',
    '食物饮品': '食物饮品',
    '群体组织': '社会组织',
    '地点位置': '地点场所',
    '动机目的': '思维认知',
    '自然物体': '自然环境',
    '人物角色': '人物职业',
    '自然现象': '自然环境',
    '植物': '动物自然',
    '财产所有': '经济商业',
    '过程变化': '变化发展',
    '数量度量': '数量度量',
    '关系': '关系连接',
    '形状': '形状外观',
    '状态情况': '状态情况',
    '物质材料': '物质材料',
    '时间': '时间',
    '身体动作': '身体健康',
    '变化改变': '变化发展',
    '思考认知': '思维认知',
    '言语交流': '语言交流',
    '竞争比赛': '竞争比赛',
    '消费使用': '日常生活',
    '接触动作': '行为动作',
    '创造制作': '创造艺术',
    '情感表达': '情感心理',
    '移动运动': '运动出行',
    '感知感觉': '感知感觉',
    '拥有获取': '经济商业',
    '社会交往': '社会组织',
    '状态描述': '状态情况',
    '天气相关': '自然环境',
    '形容词通用': '描述形容',
    '形容词关系': '描述形容',
    '分词形容词': '描述形容',
    '副词': '程度方式',
}


def get_word_category(word):
    """获取单词的语义类别"""
    # 处理多词短语
    word_clean = word.replace(' ', '_')
    
    synsets = wn.synsets(word_clean)
    if not synsets:
        # 尝试去掉下划线
        synsets = wn.synsets(word.replace(' ', ''))
    
    if not synsets:
        return None
    
    # 获取最常用的词义（第一个synset）
    primary_synset = synsets[0]
    lexname = primary_synset.lexname()
    
    # 映射到中文类别
    chinese_cat = LEXNAME_TO_CHINESE.get(lexname, '其他')
    # 合并到更大的类别
    merged_cat = CATEGORY_MERGE.get(chinese_cat, chinese_cat)
    
    return merged_cat


def load_words(filepath):
    """从文件加载单词列表，去除重复"""
    words = []
    seen = set()
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig 自动处理BOM
        for line in f:
            word = line.strip()
            if word and word not in seen:
                words.append(word)
                seen.add(word)
    return words


def translate_words(words, cache_file=None):
    """翻译单词列表，支持缓存"""
    translations = {}
    
    # 尝试加载缓存
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            print(f"从缓存加载了 {len(translations)} 个翻译")
        except:
            pass
    
    # 找出需要翻译的单词
    words_to_translate = [w for w in words if w not in translations]
    
    if words_to_translate:
        print(f"正在翻译 {len(words_to_translate)} 个单词...")
        translator = GoogleTranslator(source='en', target='zh-CN')
        
        # 批量翻译，每批50个
        batch_size = 50
        for i in range(0, len(words_to_translate), batch_size):
            batch = words_to_translate[i:i+batch_size]
            try:
                # 用换行符连接进行批量翻译
                text = '\n'.join(batch)
                result = translator.translate(text)
                translated = result.split('\n')
                
                for word, trans in zip(batch, translated):
                    translations[word] = trans.strip()
                
                if (i + batch_size) % 200 == 0:
                    print(f"  已翻译 {min(i + batch_size, len(words_to_translate))} / {len(words_to_translate)}")
            except Exception as e:
                print(f"批量翻译失败，尝试逐个翻译: {e}")
                # 逐个翻译
                for word in batch:
                    try:
                        trans = translator.translate(word)
                        translations[word] = trans
                    except:
                        translations[word] = word  # 翻译失败则保留原文
        
        # 保存缓存
        if cache_file:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)
            print(f"翻译缓存已保存到 {cache_file}")
    
    return translations


def categorize_words(words):
    """将单词分类"""
    categories = defaultdict(list)
    uncategorized = []
    
    for word in words:
        category = get_word_category(word)
        if category:
            categories[category].append(word)
        else:
            uncategorized.append(word)
    
    return categories, uncategorized


def split_large_categories(categories, max_size=60):
    """将超过max_size的类别拆分"""
    result = {}
    
    for cat_name, words in categories.items():
        if len(words) <= max_size:
            result[cat_name] = words
        else:
            # 拆分成多个子类别
            num_parts = (len(words) + max_size - 1) // max_size
            for i in range(num_parts):
                start = i * max_size
                end = min((i + 1) * max_size, len(words))
                sub_words = words[start:end]
                if num_parts > 1:
                    sub_name = f"{cat_name}_{i+1}"
                else:
                    sub_name = cat_name
                result[sub_name] = sub_words
    
    return result


def save_categories(categories, output_dir, translations):
    """保存分类结果到文件，包含标题和双语翻译"""
    os.makedirs(output_dir, exist_ok=True)
    
    for cat_name, words in categories.items():
        filename = os.path.join(output_dir, f"{cat_name}.txt")
        # 生成显示用的标题（去掉下划线，用于文件头）
        display_name = cat_name.replace('_', '')
        
        with open(filename, 'w', encoding='utf-8') as f:
            # 写入文件标题
            f.write(display_name + '\n')
            # 写入双语单词列表
            for word in sorted(words):
                chinese = translations.get(word, word)
                f.write(f"{chinese} {word}\n")
        print(f"保存 {cat_name}.txt: {len(words)} 个单词")


def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 输入文件
    input_file = os.path.join(script_dir, 'allwords.txt')
    
    # 输出目录
    output_dir = os.path.join(script_dir, 'categories')
    
    # 翻译缓存文件
    cache_file = os.path.join(script_dir, 'translations_cache.json')
    
    print("正在加载单词...")
    words = load_words(input_file)
    print(f"共加载 {len(words)} 个单词")
    
    print("\n正在翻译单词...")
    translations = translate_words(words, cache_file)
    
    print("\n正在分析单词词义并分类...")
    categories, uncategorized = categorize_words(words)
    
    print(f"\n分类统计:")
    for cat_name, cat_words in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  {cat_name}: {len(cat_words)} 个单词")
    
    if uncategorized:
        print(f"  未分类: {len(uncategorized)} 个单词")
        categories['未分类词汇'] = uncategorized
    
    print("\n正在拆分大类别（每类不超过60个）...")
    final_categories = split_large_categories(categories, max_size=60)
    
    print(f"\n最终分类数量: {len(final_categories)}")
    
    print("\n正在保存分类结果...")
    save_categories(final_categories, output_dir, translations)
    
    print(f"\n完成！分类结果已保存到 {output_dir} 目录")


if __name__ == '__main__':
    main()
