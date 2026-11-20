"""把 UCI SMS Spam Collection 原始数据转换成项目需要的 comments.csv。

数据来源：UCI Machine Learning Repository, SMS Spam Collection
链接：https://archive.ics.uci.edu/dataset/228/sms+spam+collection
许可证：CC BY 4.0
引用：Almeida, T. & Hidalgo, J. (2011). SMS Spam Collection [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CC84

处理步骤（每一步都写进报告的数据说明）：
1. 原始文件每行格式为 `标签<TAB>短信正文`
2. ham 映射为 normal，spam 映射为 spam
3. 合并连续空白、去掉首尾空白，不改动短信内容
4. 去掉完全重复的短信，避免训练/测试集出现同一条导致指标虚高
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "SMSSpamCollection"
OUTPUT = ROOT / "data" / "comments.csv"
SOURCE = "UCI SMS Spam Collection (CC BY 4.0)"


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError(f"找不到原始数据：{RAW}，请先下载 UCI 数据集")

    rows = []
    seen = set()
    duplicates = 0
    empty = 0

    with RAW.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if "\t" not in line:
                empty += 1
                continue
            raw_label, raw_text = line.split("\t", 1)
            text = " ".join(raw_text.split())
            if not text:
                empty += 1
                continue
            if text in seen:
                duplicates += 1
                continue
            seen.add(text)
            label = "normal" if raw_label == "ham" else "spam"
            rows.append({"text": text, "label": label, "source": SOURCE})

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "source"])
        writer.writeheader()
        writer.writerows(rows)

    spam = sum(1 for r in rows if r["label"] == "spam")
    normal = len(rows) - spam
    print(f"已生成 {OUTPUT}")
    print(f"保留 {len(rows)} 条：normal={normal}, spam={spam}")
    print(f"去除完全重复 {duplicates} 条；跳过空行/格式异常 {empty} 条")


if __name__ == "__main__":
    main()
