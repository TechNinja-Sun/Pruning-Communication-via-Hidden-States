# PruneComm-HS 实验设计（面向 Token 降本）

## 1. 实验目标

本实验围绕一个核心问题展开：

在保持或接近基线准确率的前提下，PruneComm-HS 是否能够显著降低多智能体协作中的 Token 总开销。

因此，实验不只比较最终准确率，更强调以下两个结论：

1. 相同或相近准确率下，系统的总 Token 是否更少。
2. 在相同 Token 预算下，系统是否能获得更高的准确率。

---

## 2. 当前可调用模型与角色划分

根据代码实现，当前可调用的模型均为聊天模型，统一通过 OpenAI 兼容接口调用，并共享同一个 embedding 接口 `text-embedding-v2`。真正影响实验差异的是“模型能力层级”和“回答风格差异”，而不是接口形式。

### 2.1 可调用模型

当前代码已经注册并可实例化的模型如下：

1. `qwen-plus`
2. `qwen-turbo`
3. `qwen2.5-14b-instruct`
4. `qwen2.5-7b-instruct`
5. `qwen1.5-1.8b-chat`
6. `deepseek-r1-distill-qwen-14b`
7. `deepseek-r1-distill-qwen-7b`

### 2.2 模型分层建议

为了让实验更有解释力，建议把模型按“强 / 中 / 轻量”分层，而不是简单随机混搭：

1. 强模型：`qwen-plus`, `qwen2.5-14b-instruct`, `deepseek-r1-distill-qwen-14b`
2. 中模型：`qwen-turbo`, `qwen2.5-7b-instruct`, `deepseek-r1-distill-qwen-7b`
3. 轻量模型：`qwen1.5-1.8b-chat`

其中，强模型更适合做“参考锚点”，轻量模型更容易制造低成本但不完全一致的答案分歧。

---

## 3. 核心假设

### H1：异构模型 + 剪枝策略能降低 Token 成本

在相同数据集和相同轮数下，`dissimilar` 策略应比 `similar` 和 `random` 具有更高的 Token Efficiency。

### H2：同等准确率下，dissimilar 的 Cost@Acc* 更低

当系统达到某个准确率阈值时，`dissimilar` 所需累计 Token 应更少。

### H3：模型异构性越强，剪枝收益越明显

与同构模型相比，强中轻混合的异构模型组合更容易形成有效分歧，从而让通信剪枝更能发挥作用。

---

## 4. 实验总设计

实验分为四组：

1. 主实验：比较三种通信策略的 Token 成本和准确率。
2. 消融实验：比较同构模型与异构模型。
3. 预算实验：比较不同 Token 上限或温度设置下的成本曲线。
4. 稳定性实验：重复运行，统计均值和标准差。

---

## 5. 推荐的 8-Agent 配置

你当前代码支持 8 个 Agent，并且会按 `LLM_NAME_LIST` 循环分配模型。建议实验中使用下面这组混合配置：

```dotenv
LLM_NAME_LIST="qwen-plus,qwen-turbo,qwen2.5-14b-instruct,qwen2.5-7b-instruct,qwen1.5-1.8b-chat,deepseek-r1-distill-qwen-14b,deepseek-r1-distill-qwen-7b,qwen-plus"
```

这个配置的好处是：

1. 保留一个强模型作为稳定锚点。
2. 中模型提供主要分歧来源。
3. 轻量模型降低整体成本，并增加互补性。
4. 循环分配后，8 个 Agent 的角色分布不会完全一致。

---

## 6. 评价指标

本实验只保留与“降本增效”直接相关的指标。

### 6.1 主指标

1. `Final Accuracy`
2. `Total Tokens`
3. `Avg Token / Round`
4. `Token Efficiency`

定义为：

`Token Efficiency = Final Accuracy / (Total Tokens / 1000)`

### 6.2 关键成本指标

1. `Cost@0.65`
2. `Cost@0.70`

含义是：达到准确率阈值 0.65 或 0.70 时所需的累计 Token。

### 6.3 稳定性指标

1. `Mean Accuracy`
2. `Std Accuracy`
3. `Mean Tokens`
4. `Std Tokens`

---

## 7. 主实验设计

### 7.1 对照组

固定模型列表和超参数，仅切换通信策略：

1. `COMM_MODE="dissimilar"`
2. `COMM_MODE="similar"`
3. `COMM_MODE="random"`

### 7.2 目的

比较三种通信方式在：

1. 最终准确率
2. 总 Token
3. Token Efficiency
4. Cost@Acc*

上的差异。

### 7.3 预期结论

如果你的系统确实有“剪枝降本”的优势，最应该出现的现象是：

1. `dissimilar` 的准确率不低于 `similar`。
2. `dissimilar` 的总 Token 更低，或在相近准确率下更省 Token。
3. `random` 作为无策略基线，通常介于两者之间或波动更大。

---

## 8. 消融实验设计

### 8.1 同构 vs 异构

固定 `COMM_MODE="dissimilar"`，只改变模型组合：

#### 同构组

```dotenv
LLM_NAME_LIST="qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus"
```

#### 异构组

```dotenv
LLM_NAME_LIST="qwen-plus,qwen-turbo,qwen2.5-14b-instruct,qwen2.5-7b-instruct,qwen1.5-1.8b-chat,deepseek-r1-distill-qwen-14b,deepseek-r1-distill-qwen-7b,qwen-plus"
```

### 8.2 目的

验证“模型异构性”是否会放大剪枝策略的收益。

### 8.3 预期结论

1. 同构组更稳定，但分歧较小。
2. 异构组更容易形成有用分歧，因此 `dissimilar` 更能体现优势。
3. 若异构组在准确率接近的前提下 Token 更少，则说明系统确实实现了“低成本协作”。

---

## 9. 预算实验设计

为了进一步证明“减少 Token 花销”，建议加入预算扫描。

### 9.1 扫描参数

1. `DEFAULT_MAX_TOKENS = 256, 512, 1024`
2. `DEFAULT_TEMPERATURE = 0.3, 0.5, 0.7`

### 9.2 目的

观察在不同生成预算下：

1. 准确率变化是否平滑。
2. Token 开销是否与参数单调相关。
3. `dissimilar` 是否在较低 Token 预算下仍保持较优效率。

### 9.3 推荐优先级

如果 API 预算有限，优先扫温度；如果预算充足，再扫 `max_tokens`。

---

## 10. 稳定性实验设计

每组实验至少重复 3 次，条件如下完全一致：

1. 相同数据顺序
2. 相同模型列表
3. 相同温度和 `max_tokens`
4. 相同 `MAX_ROUNDS`

统计：

1. 平均准确率
2. 平均 Token
3. 标准差

这样可以排除单次题目分布偶然性。

---

## 11. 推荐参数

### 11.1 主实验参数

```dotenv
NUMS_AGENTS=8
MAX_ROUNDS=100
DEFAULT_MAX_TOKENS=512
DEFAULT_TEMPERATURE=0.5
DEFAULT_NUM_COMPLETIONS=1
```

### 11.2 说明

1. `MAX_ROUNDS=100` 用于正式统计。
2. `DEFAULT_MAX_TOKENS=512` 是比 1024 更合适的降本起点。
3. `DEFAULT_TEMPERATURE=0.5` 保持适度分歧，便于检验剪枝策略。
4. `DEFAULT_NUM_COMPLETIONS=1` 保持单次输出，避免额外 Token 浪费。

---

## 12. 实验流程

### 12.1 主实验流程

1. 固定 8-Agent 异构配置。
2. 分别运行 `dissimilar`、`similar`、`random`。
3. 每次记录 `trace_*.json` 和 `metrics/*.png`。
4. 汇总 `Final Accuracy`、`Total Tokens`、`Token Efficiency`、`Cost@Acc*`。

### 12.2 消融流程

1. 固定 `COMM_MODE="dissimilar"`。
2. 运行同构组。
3. 运行异构组。
4. 比较两组结果。

### 12.3 预算流程

1. 固定模型列表和 `COMM_MODE`。
2. 扫描温度或 `max_tokens`。
3. 记录 Token 与准确率曲线。

---

## 13. 结果表模板

### 13.1 主结果表

| Strategy | Final Accuracy | Total Tokens | Avg Token / Round | Token Efficiency | Cost@0.65 | Cost@0.70 |
|---|---:|---:|---:|---:|---:|---:|
| dissimilar | TODO | TODO | TODO | TODO | TODO | TODO |
| similar | TODO | TODO | TODO | TODO | TODO | TODO |
| random | TODO | TODO | TODO | TODO | TODO | TODO |

### 13.2 同构 vs 异构表

| Setting | COMM_MODE | Final Accuracy | Total Tokens | Token Efficiency |
|---|---|---:|---:|---:|
| Homogeneous (all qwen-plus) | dissimilar | TODO | TODO | TODO |
| Heterogeneous (mixed 8 agents) | dissimilar | TODO | TODO | TODO |

### 13.3 预算扫描表

| Temperature | Max Tokens | Strategy | Final Accuracy | Total Tokens | Token Efficiency |
|---:|---:|---|---:|---:|---:|
| 0.3 | 256 | dissimilar | TODO | TODO | TODO |
| 0.5 | 512 | dissimilar | TODO | TODO | TODO |
| 0.7 | 1024 | dissimilar | TODO | TODO | TODO |

---

## 14. 结果解读口径

### 14.1 如果 dissimilar 最优

可以得出结论：语义分歧驱动的通信剪枝策略更适合多智能体协作，因为它能在引入互补信息的同时避免冗余传播，从而降低 Token 成本。

### 14.2 如果异构优于同构

可以得出结论：模型能力分层与语义剪枝存在正向协同，模型多样性会提升通信剪枝的可用性。

### 14.3 如果随机策略波动大

可以说明：没有结构的通信方式不稳定，难以在相同 Token 预算下持续取得稳定收益。

---

## 15. 实验注意事项

1. 当前所有模型都走同一个 chat 接口，所以实验差异主要来自模型能力，而不是接口差异。
2. embedding 一律使用同一模型 `text-embedding-v2`，因此相似度比较是公平的。
3. 某些模型虽然在可用列表里出现，也可能因账号权限不可调用，建议先做短轮试跑。
4. 若某次实验中某模型返回空内容，代码会用 `[EMPTY_RESPONSE]` 兜底，但仍建议保留日志。

---

## 16. 最终建议

如果你想优先证明“减少 Token 花销”，推荐最终论文主实验采用：

1. 8-Agent 异构配置
2. `COMM_MODE="dissimilar"` 作为主方法
3. `similar` 和 `random` 作为对照
4. 以 `Cost@Acc*` 和 `Token Efficiency` 作为核心结论指标

这样你的实验叙事会更聚焦，也更容易证明系统的实际价值。
