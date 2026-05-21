import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 解决中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 超大画布，宽松布局
fig, ax = plt.subplots(figsize=(16, 5), dpi=300)
ax.set_xlim(0, 16)
ax.set_ylim(0, 4)
ax.axis('off')

# 流程步骤（只留标题，彻底不重叠）
steps = ['参数配置', '批量运行', '轨迹落盘', '图表分析']
x = [2, 5.5, 9, 12.5]
y = 2
w = 2.5
h = 1.2

# 画方框
for xi, name in zip(x, steps):
    box = mpatches.FancyBboxPatch(
        (xi - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.1",
        facecolor='white',
        edgecolor='#333333',
        linewidth=1.2
    )
    ax.add_patch(box)
    ax.text(xi, y, name, fontsize=14, ha='center', va='center', weight='bold')

# 画箭头
arrow = dict(arrowstyle='->', color='#333', lw=1.5)
ax.annotate('', (5.5 - w/2-0.05, 2), (2 + w/2+0.05, 2), arrowprops=arrow)
ax.annotate('', (9 - w/2-0.05, 2), (5.5 + w/2+0.05, 2), arrowprops=arrow)
ax.annotate('', (12.5 - w/2-0.05, 2), (9 + w/2+0.05, 2), arrowprops=arrow)

# 总标题
ax.text(8, 3.2, 'PruneComm-HS 实验流程图', fontsize=16, ha='center', weight='bold')

plt.savefig('experiment_flow.png', dpi=300, bbox_inches='tight')
plt.show()