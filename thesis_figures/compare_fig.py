import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# -------------------------- 论文绘图参数配置（核心，确保科研风格）--------------------------
plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 论文标准字体
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300  # 高清输出（论文要求≥300dpi）
plt.rcParams['figure.figsize'] = (15, 5)  # 三栏布局，适配论文宽度
plt.rcParams['font.size'] = 12  # 正文字体大小
plt.rcParams['axes.titlepad'] = 15  # 标题间距
plt.rcParams['axes.linewidth'] = 1.0  # 坐标轴线条粗细（论文标准）

# 颜色配置（科研常用配色，差异化明显，不花哨）
color_similar = "#1f77b4"    # 相似策略：科技蓝
color_dissimilar = "#d62728" # 反相似策略：深红
color_random = "#2ca02c"     # 随机策略：深绿
node_color = "#f0f0f0"       # 智能体节点颜色（浅灰，突出链路）
edge_width = 1.5             # 通信链路粗细
node_size = 1200             # 智能体节点大小

# -------------------------- 通用参数（可修改）--------------------------
N = 5  # 智能体数量，与前文实验场景一致，可修改为3/4/6
agents = [f"$a_{i+1}$" for i in range(N)]  # 智能体标签（与公式一致）

# 模拟语义相似度矩阵（符合论文逻辑，仅用于可视化，可根据实际数据修改）
np.random.seed(42)  # 固定随机种子，保证可重复
S = np.random.rand(N, N)  # 随机生成[0,1]相似度
np.fill_diagonal(S, 0)  # 对角线为0（自身不通信）
S = (S + S.T) / 2  # 对称矩阵（相似度双向一致）

# -------------------------- 定义绘图函数--------------------------
def plot_strategy(ax, strategy_name, color, select_func, S_matrix, agents, N):
    # 构建图
    G = nx.Graph()
    G.add_nodes_from(range(N))
    
    # 圆形布局（论文最常用，清晰整洁）
    pos = nx.circular_layout(G)
    
    # 绘制智能体节点（带标签，与公式一致）
    nx.draw_networkx_nodes(G, pos, node_color=node_color, node_size=node_size, 
                           edgecolors="black", linewidths=1.2, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=dict(zip(range(N), agents)), 
                           font_size=14, font_weight="bold", ax=ax)
    
    # 选择参考对象（模拟每个智能体的参考逻辑）
    edges = []
    for i in range(N):
        # 排除自身，获取其他智能体索引
        others = [j for j in range(N) if j != i]
        # 根据策略选择参考对象j
        if strategy_name == "Similar":
            # 相似策略：选择S_ij最大的j
            j = others[np.argmax(S_matrix[i, others])]
        elif strategy_name == "Dissimilar":
            # 反相似策略：选择S_ij最小的j
            j = others[np.argmin(S_matrix[i, others])]
        else:  # Random
            # 随机策略：均匀随机选择j
            j = np.random.choice(others)
        edges.append((i, j))
    
    # 绘制通信链路（突出显示）
    nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color, 
                           width=edge_width, alpha=0.8, ax=ax)
    
    # 标注策略名称和核心函数（与前文公式完全一致）
    if strategy_name == "Similar":
        func_text = r"$f(i)=\arg\max_{j\neq i}S_{ij}$"
    elif strategy_name == "Dissimilar":
        func_text = r"$f(i)=\arg\min_{j\neq i}S_{ij}$"
    else:
        func_text = r"$f(i)\sim\mathrm{Uniform}({j\neq i})$"
    
    ax.text(0.5, -0.25, func_text, ha='center', va='center', transform=ax.transAxes,
            fontsize=14, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.1))
    
    # 设置标题和坐标轴
    ax.set_title(f"{strategy_name} Strategy", fontsize=16, fontweight='bold', pad=20)
    ax.axis("off")  # 关闭坐标轴（论文图必备）
    
    # 标注相似度关联（辅助理解）
    if strategy_name == "Similar":
        ax.text(0.5, -0.15, r"Select agent with maximum $S_{ij}$", ha='center', va='center', 
                transform=ax.transAxes, fontsize=11)
    elif strategy_name == "Dissimilar":
        ax.text(0.5, -0.15, r"Select agent with minimum $S_{ij}$", ha='center', va='center', 
                transform=ax.transAxes, fontsize=11)
    else:
        ax.text(0.5, -0.15, r"Randomly select agent (independent of $S_{ij}$)", ha='center', va='center', 
                transform=ax.transAxes, fontsize=11)

# -------------------------- 绘制三栏对比图--------------------------
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex=True, sharey=True)

# 绘制三类策略
plot_strategy(ax1, "Similar", color_similar, "max", S, agents, N)
plot_strategy(ax2, "Dissimilar", color_dissimilar, "min", S, agents, N)
plot_strategy(ax3, "Random", color_random, "random", S, agents, N)

# 整体标题（适配论文章节，可修改）
fig.suptitle("Comparison of Three Communication Strategies", fontsize=18, fontweight='bold', y=0.98)

# 调整布局，避免拥挤（论文排版关键）
plt.tight_layout()
plt.subplots_adjust(top=0.85, bottom=0.3)

# 保存图片（论文常用格式，可直接插入）
plt.savefig("communication_strategy_comparison.png", dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("示意图已生成，保存为 communication_strategy_comparison.png")
print("说明：图片为高清300dpi，无背景，可直接插入论文，智能体数量N可自由修改")
