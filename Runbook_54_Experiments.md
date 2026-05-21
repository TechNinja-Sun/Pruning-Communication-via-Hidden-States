# Runbook: 54 组实验手工执行清单

## 1. 目标

本清单用于手工执行 54 组对照实验，验证 PruneComm-HS 在多模型协作下的 Token 降本优势。

总实验数计算：

- 3 个通信策略
- 3 个模型池
- 2 个温度
- 3 次重复

总计：3 x 3 x 2 x 3 = 54 组。

---

## 2. 全局固定参数

每组实验除指定字段外，其余参数保持一致：

```dotenv
NUMS_AGENTS=8
MAX_ROUNDS=100
DEFAULT_MAX_TOKENS=512
DEFAULT_NUM_COMPLETIONS=1
```

执行前确认以下文件已可用：

- PruneComm/system/exp.py
- model.env

执行命令统一为：

```bash
python PruneComm/system/exp.py
```

---

## 3. 三个模型池

### Pool-A: Strong-Homo

```dotenv
LLM_NAME_LIST="qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus,qwen-plus"
```

### Pool-B: Balanced-Hetero

```dotenv
LLM_NAME_LIST="qwen-plus,qwen-turbo,qwen2.5-14b-instruct,qwen2.5-7b-instruct,qwen1.5-1.8b-chat,deepseek-r1-distill-qwen-14b,deepseek-r1-distill-qwen-7b,qwen-plus"
```

### Pool-C: Wide-Hetero

```dotenv
LLM_NAME_LIST="qwen-plus,qwen-max,qwen-flash,deepseek-v3,glm-5,kimi-k2.5,qwen2.5-32b-instruct,qwen3-14b"
```

说明：Pool-C 覆盖更广模型族，若某模型被过滤不可调用，按系统日志记录并继续跑。

---

## 4. 组合维度

### 4.1 通信策略

- dissimilar
- similar
- random

### 4.2 温度

- 0.3
- 0.5

### 4.3 重复次数

- Repeat-1
- Repeat-2
- Repeat-3

---

## 5. 手工执行步骤（每组）

1. 打开 model.env。
2. 写入当前组的 LLM_NAME_LIST。
3. 写入当前组的 COMM_MODE。
4. 写入当前组的 DEFAULT_TEMPERATURE。
5. 确认固定参数未变化。
6. 执行：python PruneComm/system/exp.py。
7. 记录本组输出目录与关键指标。

建议记录路径：exp/result_时间戳/模式名。

---

## 6. 54 组执行清单

| ID | Pool | COMM_MODE | TEMP | Repeat |
|---|---|---|---:|---:|
| 01 | A | dissimilar | 0.3 | 1 |
| 02 | A | dissimilar | 0.3 | 2 |
| 03 | A | dissimilar | 0.3 | 3 |
| 04 | A | dissimilar | 0.5 | 1 |
| 05 | A | dissimilar | 0.5 | 2 |
| 06 | A | dissimilar | 0.5 | 3 |
| 07 | A | similar | 0.3 | 1 |
| 08 | A | similar | 0.3 | 2 |
| 09 | A | similar | 0.3 | 3 |
| 10 | A | similar | 0.5 | 1 |
| 11 | A | similar | 0.5 | 2 |
| 12 | A | similar | 0.5 | 3 |
| 13 | A | random | 0.3 | 1 |
| 14 | A | random | 0.3 | 2 |
| 15 | A | random | 0.3 | 3 |
| 16 | A | random | 0.5 | 1 |
| 17 | A | random | 0.5 | 2 |
| 18 | A | random | 0.5 | 3 |
| 19 | B | dissimilar | 0.3 | 1 |
| 20 | B | dissimilar | 0.3 | 2 |
| 21 | B | dissimilar | 0.3 | 3 |
| 22 | B | dissimilar | 0.5 | 1 |
| 23 | B | dissimilar | 0.5 | 2 |
| 24 | B | dissimilar | 0.5 | 3 |
| 25 | B | similar | 0.3 | 1 |
| 26 | B | similar | 0.3 | 2 |
| 27 | B | similar | 0.3 | 3 |
| 28 | B | similar | 0.5 | 1 |
| 29 | B | similar | 0.5 | 2 |
| 30 | B | similar | 0.5 | 3 |
| 31 | B | random | 0.3 | 1 |
| 32 | B | random | 0.3 | 2 |
| 33 | B | random | 0.3 | 3 |
| 34 | B | random | 0.5 | 1 |
| 35 | B | random | 0.5 | 2 |
| 36 | B | random | 0.5 | 3 |
| 37 | C | dissimilar | 0.3 | 1 |
| 38 | C | dissimilar | 0.3 | 2 |
| 39 | C | dissimilar | 0.3 | 3 |
| 40 | C | dissimilar | 0.5 | 1 |
| 41 | C | dissimilar | 0.5 | 2 |
| 42 | C | dissimilar | 0.5 | 3 |
| 43 | C | similar | 0.3 | 1 |
| 44 | C | similar | 0.3 | 2 |
| 45 | C | similar | 0.3 | 3 |
| 46 | C | similar | 0.5 | 1 |
| 47 | C | similar | 0.5 | 2 |
| 48 | C | similar | 0.5 | 3 |
| 49 | C | random | 0.3 | 1 |
| 50 | C | random | 0.3 | 2 |
| 51 | C | random | 0.3 | 3 |
| 52 | C | random | 0.5 | 1 |
| 53 | C | random | 0.5 | 2 |
| 54 | C | random | 0.5 | 3 |

---

## 7. 每组结果记录模板

建议把每组结果填到你自己的总表里，最少记录这些字段：

| ID | OutputDir | FinalAccuracy | TotalTokens | AvgTokenPerRound | TokenEfficiency | Cost@0.65 | Cost@0.70 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 01 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

其中：

- TokenEfficiency = FinalAccuracy / (TotalTokens / 1000)
- Cost@Acc* 从 trace 中按首次达到阈值的轮次累计 token 读取

---

## 8. 汇总结论建议

执行完成后，优先回答三个问题：

1. 哪个策略在同等准确率下最省 Token？
2. 异构模型池（B/C）是否比同构池（A）更能发挥 dissimilar 优势？
3. 温度从 0.3 到 0.5 时，准确率增益是否值得额外 Token 成本？

如果结论稳定，可以将主结论写成：

- 在 54 组对照中，dissimilar 在 Token Efficiency 和 Cost@Acc* 上持续优于 similar/random，验证了语义分歧驱动的通信剪枝能有效降低协作成本。
