# 失败案例（真实测试集）

以下案例来自主模型在测试集上的真实误判，按置信度最高的误判挑选。
分析栏由人工根据短信内容填写，不编造事实。

## 假阳性：正常被判为垃圾

- 输入：`Please protect yourself from e-threats. SIB never asks for sensitive information like Passwords,ATM/SMS PIN thru email. Never share your password with anybody.`
- 真实标签：normal
- 预测标签：spam
- 置信度：0.8697
- 初步分析：这是银行/机构发出的**安全提醒**，内容在劝用户不要泄露密码，但词袋模型只看到 `Passwords`、`PIN`、`sensitive information`、`Never share` 等词——这些词在诈骗短信里也很常见。模型忽略了 `never asks` 这类否定结构，属于**特征表示与语义上下文不足**导致的误报。改进方向：加入否定短语特征或补充安全提醒类正常样本。

## 假阴性：垃圾被判为正常

- 输入：`Sorry I missed your call let's talk when you have the time. I'm on 07090201529`
- 真实标签：spam
- 预测标签：normal
- 置信度：1.0000
- 初步分析：这条短信表面像“错过来电、回头再聊”的正常私人消息，只带了一个电话号码；数据集把它标为垃圾，判断依据很可能依赖该号码的历史行为，而这些上下文**不在文本里**。模型因此过度自信地判错，属于**数据标注依赖外部信息 / 任务边界模糊**，不是单纯分词问题。改进方向：对含可疑号码的短信增加规则复核，不让高置信度结果直接自动处理。
