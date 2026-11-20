"""训练相关的公共函数。

大白话：
- “向量化”= 把中文评论变成一串数字，模型只认识数字不认识汉字。
- TF-IDF = 一个词出现得越多、在别的评论里越少出现，它就越能代表这条评论。
- 朴素贝叶斯 = 根据证据算概率的广告门卫。
"""

import csv
from pathlib import Path

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "comments.csv"


def load_data(path: Path = DATA_PATH):
    """读评论数据。返回两个列表：文本和标签。"""
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"数据文件是空的：{path}")
    return [r["text"] for r in rows], [r["label"] for r in rows]


def make_tokenizer(use_jieba: bool):
    """造一个分词函数。

    use_jieba=True：用 jieba 把句子切成词，例如“加微信领资料”→“加/微信/领/资料”。
    use_jieba=False：只按单个字切，例如“加/微/信/领/资/料”。
    两者对比就是“消融实验”：拆掉分词这个零件，看模型还灵不灵。
    """
    def tokenizer(text: str):
        text = (text or "").strip()
        if not text:
            return []
        if use_jieba:
            import jieba
            # 告诉 jieba 把词典缓存放项目内，避免它去问系统临时目录
            cache_dir = Path(__file__).resolve().parent.parent / ".tmp"
            cache_dir.mkdir(parents=True, exist_ok=True)
            jieba.dt.tmp_dir = str(cache_dir)
            return [w for w in jieba.lcut(text) if w.strip()]
        return [ch for ch in text if not ch.isspace()]

    return tokenizer


def build_pipeline(vectorizer: str = "tfidf", use_jieba: bool = True) -> Pipeline:
    """搭一条流水线：文本 → 数字特征 → 朴素贝叶斯分类。

    流水线（Pipeline）的好处：训练和预测用同一套处理步骤，
    不会出现“训练时分词、预测时不分词”这种低级错误。
    """
    tokenizer = make_tokenizer(use_jieba)

    if vectorizer == "count":
        # 词袋：只数词出现了几次，最简单的参照物
        vec = CountVectorizer(tokenizer=tokenizer, token_pattern=None)
    else:
        # TF-IDF：考虑词的重要性，通常是更靠谱的主模型
        vec = TfidfVectorizer(tokenizer=tokenizer, token_pattern=None)

    return Pipeline([
        ("vec", vec),
        ("clf", MultinomialNB(alpha=1.0)),  # alpha 是平滑项，防止没见过的词把概率算成 0
    ])
