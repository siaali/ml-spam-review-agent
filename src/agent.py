"""短消息审核 Agent 的命令行入口。

处理流程：
1. 输入校验：拦截空输入与超过 500 字的输入
2. 模型判别：输出垃圾/正常标签与置信度
3. 置信度闸门：低于阈值时转人工复核
4. 相似消息检索：从本地消息库返回 Top3 相似文本

输出为 JSON，包含标签、置信度、处理动作、判定理由、输入文本和相似消息。
"""

import argparse
import json
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from train import DATA_PATH, build_pipeline, load_data, make_tokenizer

CONFIDENCE_THRESHOLD = 0.65
MAX_LENGTH = 500


class AgentError(Exception):
    """输入或环境异常，以明确错误信息返回。"""


def check_input(text: str) -> str:
    """校验输入文本。"""
    text = (text or "").strip()
    if not text:
        raise AgentError("输入为空，请提供一条短消息。")
    if len(text) > MAX_LENGTH:
        raise AgentError(f"评论太长了（{len(text)} 字），请控制在 {MAX_LENGTH} 字以内。")
    return text


def build_system():
    """启动时准备模型与检索库。

    实验评估阶段使用固定划分的训练集与测试集；部署阶段使用全部已标注数据训练。
    """
    if not DATA_PATH.exists():
        raise AgentError(f"找不到数据文件：{DATA_PATH}，请先运行 src/prepare_uci_data.py")

    texts, labels = load_data()
    if len(set(labels)) < 2:
        raise AgentError("数据里只有一种标签，没法训练分类器。")

    # 根据真实数据实验结果，词袋+朴素贝叶斯优于 TF-IDF+NB，因此部署用主模型
    model = build_pipeline(vectorizer="count", use_jieba=True)
    model.fit(texts, labels)

    tokenizer = make_tokenizer(use_jieba=True)
    retriever = TfidfVectorizer(tokenizer=tokenizer, token_pattern=None)
    corpus_matrix = retriever.fit_transform(texts)

    return model, retriever, corpus_matrix, texts, labels


def decide(label: str, confidence: float) -> dict:
    """根据标签和置信度决定怎么处理。"""
    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "label": label,
            "confidence": round(confidence, 4),
            "action": "转人工复核",
            "reason": f"置信度低于阈值 {CONFIDENCE_THRESHOLD}，模型自己不敢拍板。",
        }
    if label == "spam":
        return {
            "label": label,
            "confidence": round(confidence, 4),
            "action": "隐藏",
            "reason": "模型有把握判断这是垃圾广告。",
        }
    return {
        "label": label,
        "confidence": round(confidence, 4),
        "action": "通过",
        "reason": "模型有把握判断这是正常评论。",
    }


def find_similar(text: str, retriever, corpus_matrix, texts, labels, top_k: int = 3):
    """从本地评论库里找最像的几条，给人工复核当参考。"""
    query_vec = retriever.transform([text])
    scores = linear_kernel(query_vec, corpus_matrix).ravel()
    order = scores.argsort()[::-1][:top_k]
    return [
        {
            "text": texts[i],
            "label": labels[i],
            "similarity": round(float(scores[i]), 4),
        }
        for i in order
    ]


def handle_one(text: str, system) -> dict:
    """处理一条评论，返回结构化结果。"""
    text = check_input(text)
    model, retriever, corpus_matrix, texts, labels = system

    proba = model.predict_proba([text])[0]
    classes = list(model.classes_)
    best_idx = int(proba.argmax())
    label = classes[best_idx]
    confidence = float(proba[best_idx])

    result = decide(label, confidence)
    result["input"] = text
    result["similar_comments"] = find_similar(
        text, retriever, corpus_matrix, texts, labels
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="评论审核 Agent（命令行版）")
    parser.add_argument("text", nargs="*", help="要审核的评论文本")
    parser.add_argument("--stdin", action="store_true", help="从标准输入逐行读取评论")
    args = parser.parse_args()

    try:
        system = build_system()
    except AgentError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)

    inputs = []
    if args.stdin:
        inputs = [line.strip() for line in sys.stdin if line.strip()]
    elif args.text:
        inputs = [" ".join(args.text)]
    else:
        print(json.dumps({"error": "请给一条评论，或用 --stdin 输入多行。"},
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    outputs = []
    for text in inputs:
        try:
            outputs.append(handle_one(text, system))
        except AgentError as e:
            outputs.append({"input": text, "error": str(e)})

    print(json.dumps(outputs if len(outputs) > 1 else outputs[0],
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
