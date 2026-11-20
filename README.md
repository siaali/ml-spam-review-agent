# 基于词袋模型与朴素贝叶斯的垃圾短消息审核 Agent

本项目是《机器学习》课程期末项目。系统接收一条短消息，输出垃圾/正常标签、预测置信度、处理动作以及三条相似历史消息，用于辅助人工复核。

## 功能

- 标签：`spam`（垃圾）/ `normal`（正常）
- 置信度：模型对判别结果的概率估计
- 处理动作：`通过` / `隐藏` / `转人工复核`
- 相似消息检索：从本地消息库返回 Top3 相似文本及其标签

置信度低于 0.65 时，系统不直接自动处置，而是转入人工复核。

## 数据

`data/comments.csv` 由公开数据集 UCI SMS Spam Collection 转换得到：

- 来源：https://archive.ics.uci.edu/dataset/228/sms+spam+collection
- 许可证：CC BY 4.0
- 原始 5574 条，去除 414 条完全重复后保留 5160 条
- 类别分布：normal 4518 条，spam 642 条
- 转换脚本：`src/prepare_uci_data.py`
- 来源、隐私与划分说明：`data/说明.md`

## 方法

实验比较了多数类基线、词袋 + 朴素贝叶斯、TF-IDF + 朴素贝叶斯，以及关闭 jieba 分词的消融版本。

| 方法 | Macro-F1 |
| --- | --- |
| 多数类基线 | 0.4669 |
| 词袋 + 朴素贝叶斯（主模型） | 0.9705 |
| TF-IDF + 朴素贝叶斯 | 0.8586 |
| TF-IDF + 朴素贝叶斯（无分词） | 0.9309 |

主模型采用词袋 + 朴素贝叶斯。TF-IDF 组关闭 jieba 后指标反而上升，原因是该数据集为英文短信，jieba 的中文分词优势无法体现，属于组件与任务语言不匹配。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `src/prepare_uci_data.py` | UCI 原始数据转换为项目 CSV |
| `src/train.py` | 分词函数与模型流水线 |
| `src/evaluate.py` | 基线、主模型、对照、消融与失败案例生成 |
| `src/agent.py` | 命令行 Agent：输入校验、分类、置信度闸门、相似检索、JSON 输出 |
| `src/capture_demo.py` | 实际运行 Agent 并保存终端记录 |
| `src/make_run_screenshot.py` | 将运行记录渲染为截图 |
| `data/` | 正式数据、原始数据与数据说明 |
| `experiments/` | 实验结果、运行记录、失败案例与截图 |
| `report/` | 报告正文、组件清单、AI 使用声明与 PDF 生成脚本 |

## 运行环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

jieba 的缓存目录已指向项目内 `.tmp/`，避免依赖系统临时目录。换机器后如遇临时目录错误，删除 `.tmp/jieba.cache` 让其重建。

## 运行

```bash
# 从原始数据重新生成 CSV
python src/prepare_uci_data.py

# 重新运行评估
python src/evaluate.py

# 垃圾消息
python src/agent.py "Free entry in 2 a wkly comp to win FA Cup final tkts"

# 低置信度演示
python src/agent.py "Nokia phone is lovly.."

# 批量读取标准输入
python src/agent.py --stdin
```

运行记录见 `experiments/demo_run.md`，截图见 `experiments/run_demo.png`。

## 复用组件与学术规范

- jieba 0.42.1，MIT；scikit-learn 1.9.1，BSD-3-Clause；UCI SMS Spam Collection，CC BY 4.0。
- 组件来源、版本、许可证、用途与适配工作见 `report/复用组件清单.md`。
- 生成式 AI 的参与环节见 `report/AI使用声明.md`。
- 报告 PDF 见 `report/期末报告.pdf`。
