# 第四章 实验结果及分析

## 4.1 实验目标与分析问题

本章围绕 PruneComm-HS 的核心目标展开：在多智能体协作推理中，通信策略是否能够在保证准确率的同时降低 Token 开销。结合前文方法设计，本章重点回答三个问题：

1. 在相同实验预算下，不同通信策略的准确率与成本表现如何。
2. 策略切换对二轮重答质量有何影响，是否带来有效纠错。
3. 异步推理与向量同步提取机制是否在工程层面提升了效率与一致性。

本章实验结果均来自固定轮数（100 轮）、固定智能体规模（8 个）的可复现实验轨迹。

## 4.2 实验配置与评价指标

### 4.2.1 对比策略

主实验采用三种策略：

1. similar：优先连接高相似度参考对象。
2. dissimilar：优先连接低相似度参考对象。
3. hybrid：基于一致性动态切换 similar、mixed 与 dissimilar_then_similar。

### 4.2.2 指标定义

本章使用以下指标进行统一评估：

1. Final Accuracy：最终累计准确率。
2. Total Tokens：100 轮总 Token。
3. Avg Token per Round：平均每轮 Token。
4. Token Efficiency：Final Accuracy / (Total Tokens / 1000)。
5. Cost@0.65 与 Cost@0.70：首次达到阈值时的累计 Token。

## 4.3 主实验结果对比

### 4.3.1 数值结果

表 4-1 给出了三种策略在同等实验设置下的主结果。

表 4-1 三种通信策略主结果对比

| 策略 | Final Accuracy | Total Tokens | Avg Token per Round | Token Efficiency | Cost@0.65 | Cost@0.70 |
|---|---:|---:|---:|---:|---:|---:|
| similar | 0.90 | 1,056,530 | 10,565.30 | 0.0008518 | 9,572 | 9,572 |
| hybrid | 0.92 | 1,049,922 | 10,499.22 | 0.0008763 | 9,044 | 9,044 |
| dissimilar | 0.85 | 901,997 | 9,019.97 | 0.0009424 | 7,710 | 7,710 |

从结果看，hybrid 在准确率上最高（0.92），similar 次之（0.90），dissimilar 相对较低（0.85）。但 dissimilar 的总 Token 最低，仅为 901,997，相比 similar 下降约 14.63%。因此，若以单位 Token 收益衡量，dissimilar 的 Token Efficiency 最高，说明其在“成本优先”场景中具备明显优势。

### 4.3.2 准确率与成本曲线分析

在 100 轮轨迹上，三种策略表现出稳定差异：

1. 准确率维度：hybrid 整体更高，具备较好的上限与稳定性。
2. 成本维度：dissimilar 曲线整体更低，体现更强降本能力。
3. 折中维度：hybrid 在准确率接近最优的同时，成本略低于 similar，适合作为默认工程策略。

【插图位置 1】建议插在本节“数值结果”后，直观展示三策略累计准确率对比。

![图4-1 三策略准确率曲线对比](acc_compare.png)

【插图位置 2】建议紧接图4-1之后，展示 Token 成本差异。

![图4-2 三策略 Token 成本对比](token_compare.png)

【插图位置 3】建议放在本小节末尾，作为“准确率-成本联合视图”总结图。

![图4-3 三策略综合对比图](three_experiments_compare.png)

## 4.4 二轮协作行为分析

为分析第二轮参考机制是否有效，本节基于 first_second_round_summary.json 对“答案变化、纠错、错误迁移”进行统计。

表 4-2 二轮行为统计结果

| 策略 | 策略分布 | Answer Change Rate | Correction Rate | Wrong Change Rate | Two-round Same Rate |
|---|---|---:|---:|---:|---:|
| similar | similar: 100 | 0.40125 | 0.33750 | 0.06375 | 0.59875 |
| hybrid | similar:77, mixed:11, dissimilar_then_similar:12 | 0.38750 | 0.31625 | 0.07125 | 0.61250 |
| dissimilar | dissimilar: 100 | 0.41250 | 0.27875 | 0.13375 | 0.58750 |

可见，similar 在本次实验中具有更高的纠错率与更低的错误迁移率，表现为“保守但稳定”的重答行为；dissimilar 虽然变化率最高，能引入更多信息多样性，但错误迁移也更高；hybrid 处于两者之间，说明动态切换机制在探索与收敛之间取得了一定平衡。

【插图位置 4】建议放在本节末尾，用于说明 hybrid 的动态切换比例。

![图4-4 Hybrid策略比例变化曲线](exp/result_20260421_173629/hybrid/metrics/strategy_ratio_curve.png)

## 4.5 通信结构与语义分布可视化分析

从机制角度，dissimilar 倾向于建立跨语义簇连接，有助于引入互补信息；similar 倾向连接局部高相似节点，利于快速收敛但可能增加信息冗余。该差异可通过通信图与相似度热力图直观展示。

【插图位置 5】建议放在本节开头，先展示 dissimilar 的通信拓扑。

![图4-5 Dissimilar通信图（第1轮）](exp/result_20260422_115739/dissimilar/round_1/comm_graph.png)

【插图位置 6】建议紧接图4-5，用于对照 similar 的通信拓扑。

![图4-6 Similar通信图（第1轮）](exp/result_20260421_210635/similar/round_1/comm_graph.png)

【插图位置 7】建议放在本节后半部分，说明语义空间分布。

![图4-7 Dissimilar相似度热力图（第1轮）](exp/result_20260422_115739/dissimilar/round_1/sim_heatmap.png)

【插图位置 8】建议作为对照补图，展示 hybrid 场景下语义结构。

![图4-8 Hybrid相似度热力图（第1轮）](exp/result_20260421_173629/hybrid/round_1/sim_heatmap.png)

## 4.6 异步推理与同步向量提取的工程收益

本系统采用单次请求返回文本结果与语义向量的一体化异步机制。相较“先文本、再单独请求向量”的串行方式，该机制具有以下工程优势：

1. 减少网络往返与数据格式转换开销。
2. 保证推理输出与分析输入时间对齐，降低版本不一致风险。
3. 在高并发多智能体场景下可显著缩短端到端统计路径。

【插图位置 9】建议放在本节末尾，作为机制说明图。

![图4-9 异步推理与向量同步提取示意图](async_inference_vector_pipeline.png)

## 4.7 本章结论

基于以上实验结果，本章得到以下结论：

1. 若优先追求准确率上限，hybrid 表现最佳（0.92）。
2. 若优先追求成本效率，dissimilar 具备显著优势（总 Token 最低，单位 Token 收益最高）。
3. similar 在二轮纠错上更稳定，适合低风险收敛场景。
4. hybrid 通过动态切换在“准确率-成本”之间形成有效折中，具备较好的工程实用性。
5. 异步推理与向量同步提取机制为后续相似度计算和图构建提供了低延迟、强一致的数据基础。

综上，PruneComm-HS 在多智能体协作中验证了通信策略对性能与成本的联合影响，且通过异步一体化处理机制提升了系统级执行效率。

---

## 附：本章插图放置总表

| 图号 | 建议插入位置 | 图片文件 |
|---|---|---|
| 图4-1 | 4.3.2 开头（主结果后） | acc_compare.png |
| 图4-2 | 图4-1之后 | token_compare.png |
| 图4-3 | 4.3.2 末尾总结 | three_experiments_compare.png |
| 图4-4 | 4.4 末尾 | exp/result_20260421_173629/hybrid/metrics/strategy_ratio_curve.png |
| 图4-5 | 4.5 开头 | exp/result_20260422_115739/dissimilar/round_1/comm_graph.png |
| 图4-6 | 图4-5之后（对照） | exp/result_20260421_210635/similar/round_1/comm_graph.png |
| 图4-7 | 4.5 后半部分 | exp/result_20260422_115739/dissimilar/round_1/sim_heatmap.png |
| 图4-8 | 图4-7之后（对照） | exp/result_20260421_173629/hybrid/round_1/sim_heatmap.png |
| 图4-9 | 4.6 末尾 | async_inference_vector_pipeline.png |
