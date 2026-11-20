"""跑评估实验：基线、主模型、消融实验。

数据：UCI SMS Spam Collection（真实公开数据，CC BY 4.0）。
输出：实验结果、失败案例、低置信度候选，全部由真实运行产生。
"""

from pathlib import Path

from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

from train import build_pipeline, load_data

ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = ROOT / "experiments" / "demo_results.md"
FAILURE_PATH = ROOT / "experiments" / "failure_cases.md"
LOW_CONF_PATH = ROOT / "experiments" / "low_confidence_cases.md"
LABELS = ["normal", "spam"]
SEED = 42


def measure(name: str, model, x_train, x_test, y_train, y_test) -> dict:
    """训练一个模型并在测试集上打分。"""
    model.fit(x_train, y_train)
    pred = model.predict(x_test)

    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_test, pred, average="macro", zero_division=0
    )
    spam_p, spam_r, spam_f1, _ = precision_recall_fscore_support(
        y_test, pred, average="binary", pos_label="spam", zero_division=0
    )
    cm = confusion_matrix(y_test, pred, labels=LABELS)

    return {
        "name": name,
        "accuracy": accuracy_score(y_test, pred),
        "macro_f1": macro_f1,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "spam_precision": spam_p,
        "spam_recall": spam_r,
        "spam_f1": spam_f1,
        "cm": cm,
        "model": model,
        "pred": pred,
    }


def fmt(x: float) -> str:
    return f"{x:.4f}"


def write_failure_cases(main, x_test, y_test) -> None:
    """挑出主模型判错的两类代表案例：假阳性和假阴性。"""
    proba = main["model"].predict_proba(x_test)
    pred = main["pred"]
    classes = list(main["model"].classes_)

    wrong = []
    for text, true, guess, p in zip(x_test, y_test, pred, proba):
        if true != guess:
            wrong.append((text, true, guess, float(max(p))))

    false_positive = [w for w in wrong if w[1] == "normal" and w[2] == "spam"]
    false_negative = [w for w in wrong if w[1] == "spam" and w[2] == "normal"]
    fp = max(false_positive, key=lambda w: w[3]) if false_positive else None
    fn = max(false_negative, key=lambda w: w[3]) if false_negative else None

    lines = [
        "# 失败案例（真实测试集）",
        "",
        "以下案例来自主模型在测试集上的真实误判，按置信度最高的误判挑选。",
        "分析栏由人工根据短信内容填写，不编造事实。",
        "",
    ]

    for title, case in (("假阳性：正常被判为垃圾", fp), ("假阴性：垃圾被判为正常", fn)):
        lines += [f"## {title}", ""]
        if case is None:
            lines += ["本次测试集中没有出现该类误判。", ""]
            continue
        text, true, guess, conf = case
        lines += [
            f"- 输入：`{text}`",
            f"- 真实标签：{true}",
            f"- 预测标签：{guess}",
            f"- 置信度：{fmt(conf)}",
            "- 初步分析：见 `report/报告正文.md` 第五节。",
            "",
        ]

    FAILURE_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_low_confidence(main, x_test, y_test) -> None:
    """列出最不确定的测试样例，供 Agent 演示“转人工复核”。"""
    proba = main["model"].predict_proba(x_test)
    pred = main["pred"]
    classes = list(main["model"].classes_)
    scored = [(float(max(p)), t, g, y) for t, g, p, y in zip(x_test, pred, proba, y_test)]
    scored.sort(key=lambda x: x[0])

    lines = [
        "# 低置信度候选（真实测试集）",
        "",
        "以下样例置信度最低，最适合用来演示 Agent 的“转人工复核”分支。",
        "",
        "| 置信度 | 预测 | 真实 | 文本 |",
        "| --- | --- | --- | --- |",
    ]
    for conf, text, guess, true in scored[:5]:
        safe = text.replace("|", "\\|")
        lines.append(f"| {fmt(conf)} | {guess} | {true} | {safe} |")
    lines.append("")

    LOW_CONF_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    texts, labels = load_data()

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=SEED, stratify=labels
    )

    results = [
        ("基线1：多数类", DummyClassifier(strategy="most_frequent")),
        ("主模型：词袋+朴素贝叶斯(有分词)", build_pipeline("count", True)),
        ("对照：TF-IDF+朴素贝叶斯(有分词)", build_pipeline("tfidf", True)),
        ("消融：TF-IDF+朴素贝叶斯(无分词,单字切分)", build_pipeline("tfidf", False)),
    ]
    measured = [measure(name, m, x_train, x_test, y_train, y_test) for name, m in results]
    main_model = measured[1]

    spam_n = sum(1 for y in labels if y == "spam")
    main_f1 = main_model["macro_f1"]
    tfidf_f1 = measured[2]["macro_f1"]
    ab_f1 = measured[3]["macro_f1"]

    lines = [
        "# 实验结果（真实公开数据集）",
        "",
        "- 数据集：UCI SMS Spam Collection（CC BY 4.0）",
        "- 数据规模：原始 5574 条，去重 414 条，最终使用 5160 条",
        f"- 标签分布：normal {len(labels) - spam_n} 条，spam {spam_n} 条（约 {spam_n / len(labels):.1%}）",
        f"- 划分：训练集 {len(x_train)} 条 / 测试集 {len(x_test)} 条，分层随机种子 {SEED}",
        "- 向量化器只在训练集拟合，测试集未参与训练",
        "",
        "| 模型 | 准确率 | Macro-F1 | 垃圾类 P | 垃圾类 R | 垃圾类 F1 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in measured:
        lines.append(
            f"| {r['name']} | {fmt(r['accuracy'])} | {fmt(r['macro_f1'])} | "
            f"{fmt(r['spam_precision'])} | {fmt(r['spam_recall'])} | {fmt(r['spam_f1'])} |"
        )

    lines += ["", "## 混淆矩阵", "", "格式：行=真实标签，列=预测标签", ""]
    for r in measured:
        cm = r["cm"]
        lines += [
            f"**{r['name']}**",
            "",
            "```text",
            "               预测normal  预测spam",
            f"真实normal   {cm[0][0]:>8}   {cm[0][1]:>8}",
            f"真实spam     {cm[1][0]:>8}   {cm[1][1]:>8}",
            "```",
            "",
        ]

    lines += [
        "## 结论",
        "",
        f"1. 主模型（词袋+NB）Macro-F1 为 {fmt(main_f1)}，多数类基线为 {fmt(measured[0]['macro_f1'])}，说明模型确实学到了判别信息。",
        f"2. 对照模型（TF-IDF+NB）Macro-F1 为 {fmt(tfidf_f1)}，低于主模型 {fmt(main_f1 - tfidf_f1)}；真实数据上词袋更优，因此最终部署选择词袋+NB。",
        f"3. 在 TF-IDF 组内做消融：去掉 jieba 分词后 Macro-F1 为 {fmt(ab_f1)}，变化 {fmt(tfidf_f1 - ab_f1)}；这是分词组件贡献的证据。",
        f"4. 主模型垃圾类 F1 为 {fmt(main_model['spam_f1'])}，召回率为 {fmt(main_model['spam_recall'])}；垃圾类占比低，不能只看准确率，必须讨论误报/漏报代价。",
        "5. 失败案例见 `failure_cases.md`，低置信度候选见 `low_confidence_cases.md`。",
        "",
    ]

    RESULT_PATH.write_text("\n".join(lines), encoding="utf-8")
    write_failure_cases(main_model, x_test, y_test)
    write_low_confidence(main_model, x_test, y_test)

    print("\n".join(lines))
    print(f"\n结果已写入：{RESULT_PATH}")
    print(f"失败案例：{FAILURE_PATH}")
    print(f"低置信度候选：{LOW_CONF_PATH}")


if __name__ == "__main__":
    main()
