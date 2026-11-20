# 演示运行记录（真实数据上的真实输出）

> 以下输出来自 UCI SMS Spam Collection 数据上训练后的 Agent 真实运行。

## 运行 1：垃圾短消息命中

命令：

```bash
python src/agent.py "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question"
```

输出（节选）：

```json
{
  "label": "spam",
  "confidence": 1.0,
  "action": "隐藏",
  "reason": "模型有把握判断这是垃圾广告。",
  "input": "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question",
  "similar_comments": [
    {"text": "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question(std txt rate)T&C's apply 08452810075over18's", "label": "spam", "similarity": 0.8726},
    {"text": "Free entry in 2 a weekly comp for a chance to win an ipod. Txt POD to 80182 to get entry (std txt rate) T&C's apply 08452810073 for details 18+", "label": "spam", "similarity": 0.2907}
  ]
}
```

## 运行 2：正常短消息通过

命令：

```bash
python src/agent.py "Ok lar... Joking wif u oni..."
```

输出（节选）：

```json
{
  "label": "normal",
  "confidence": 1.0,
  "action": "通过",
  "reason": "模型有把握判断这是正常评论。",
  "input": "Ok lar... Joking wif u oni...",
  "similar_comments": [
    {"text": "Ok lar... Joking wif u oni...", "label": "normal", "similarity": 1.0},
    {"text": "Ok...", "label": "normal", "similarity": 0.428},
    {"text": "Anything lar...", "label": "normal", "similarity": 0.3921}
  ]
}
```

## 运行 3：低置信度转人工复核

命令：

```bash
python src/agent.py "Nokia phone is lovly.."
```

输出（节选）：

```json
{
  "label": "spam",
  "confidence": 0.523,
  "action": "转人工复核",
  "reason": "置信度低于阈值 0.65，模型自己不敢拍板。",
  "input": "Nokia phone is lovly..",
  "similar_comments": [
    {"text": "Nokia phone is lovly..", "label": "normal", "similarity": 1.0},
    {"text": "My phone", "label": "normal", "similarity": 0.3208},
    {"text": "Ok..", "label": "normal", "similarity": 0.1969}
  ]
}
```

说明：模型将该消息判为 `spam`，但置信度只有 **0.523**，低于阈值 0.65，因此 Agent 未直接隐藏，而是转入人工复核。检索到的完全一致样本标签为 `normal`，说明该输入处于模型与历史标签不一致的边界区域，需要人工判断。该运行验证了低置信度转人工与相似消息复核机制。

## 运行 4：异常输入兜底

命令：

```bash
python src/agent.py ""
```

输出：

```json
{
  "input": "",
  "error": "输入为空，请提供一条短消息。"
}
```
