import matplotlib.pyplot as plt
import networkx as nx

# -------------------------- 配置参数（论文风格）--------------------------
plt.rcParams['font.sans-serif'] = ['Times New Roman']  # 论文字体
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300  # 高清
node_color = "#1f77b4"            # 科技蓝
edge_color = "#7f7f7f"            # 灰色线条
node_size = 1500
font_size = 14

# -------------------------- 构建全连接图 --------------------------
N = 5  # 智能体数量，可自由修改 3/4/5/6
G = nx.complete_graph(N)

# 圆形布局（论文最常用）
pos = nx.circular_layout(G)

# -------------------------- 绘图 --------------------------
plt.figure(figsize=(6, 6))
# 画节点
nx.draw_networkx_nodes(G, pos, node_color=node_color, node_size=node_size, edgecolors="black", linewidths=1.5)
# 画全连接边
nx.draw_networkx_edges(G, pos, edge_color=edge_color, alpha=0.6, width=1.2)
# 画标签 a1,a2...aN
labels = {i: f"$a_{i+1}$" for i in range(N)}
nx.draw_networkx_labels(G, pos, labels, font_size=font_size, font_weight="bold", font_color="white")

# 关闭坐标轴（论文图必须干净）
plt.axis("off")
plt.title("Fully Connected Communication Topology\n(Traditional Multi-Agent System)", fontsize=16, pad=20)
plt.tight_layout()
plt.savefig("fully_connected_topology.png", bbox_inches='tight')