import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
# D:\毕设\PruneComm-HS\exp\result_20260420_104708\dissimilar\trace_20260420_104708.json
# D:\毕设\PruneComm-HS\exp\result_20260420_123926\similar\trace_20260420_123926.json
trace_path = Path(r"D:\毕设\PruneComm-HS\exp\result_20260420_123926\similar\trace_20260420_123926.json")
out_dir = trace_path.parent

with trace_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

rounds = [item.get("round", i + 1) for i, item in enumerate(data)]
acc = [float(item.get("acc", 0.0)) for item in data]

token_per_round = []
for item in data:
    token_obj = item.get("tokens", {})
    total = 0
    for agent_usage in token_obj.values():
        total += int(agent_usage.get("first", 0)) + int(agent_usage.get("final", 0))
    token_per_round.append(total)

cumulative = []
running = 0
for t in token_per_round:
    running += t
    cumulative.append(running)


def moving_average(values, window=7):
    if not values:
        return []
    half = window // 2
    out = []
    n = len(values)
    for i in range(n):
        left = max(0, i - half)
        right = min(n, i + half + 1)
        chunk = values[left:right]
        out.append(sum(chunk) / len(chunk))
    return out


acc_pct = [v * 100.0 for v in acc]
token_ma = moving_average(token_per_round, window=7)

plt.style.use("seaborn-v0_8-whitegrid")

bg = "#f8fafc"
grid = "#e2e8f0"

# ACC figure
fig, ax = plt.subplots(figsize=(11, 5.8), facecolor=bg)
ax.set_facecolor(bg)

ax.fill_between(rounds, acc_pct, [0] * len(rounds), color="#8ecae6", alpha=0.25, zorder=1)
ax.plot(rounds, acc_pct, color="#0ea5e9", linewidth=2.8, zorder=3)
ax.scatter(rounds, acc_pct, color="#0284c7", s=16, alpha=0.85, zorder=4)

final_round = rounds[-1]
final_acc = acc_pct[-1]
ax.scatter([final_round], [final_acc], color="#0369a1", s=42, zorder=5)
ax.annotate(
    f"Final: {final_acc:.2f}%",
    xy=(final_round, final_acc),
    xytext=(-85, 18),
    textcoords="offset points",
    fontsize=10,
    color="#0f172a",
    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#bae6fd", alpha=0.95),
    arrowprops=dict(arrowstyle="->", color="#0ea5e9", lw=1.2),
)

ax.set_title("Accuracy Over Rounds", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
ax.set_xlabel("Round", fontsize=11)
ax.set_ylabel("Accuracy (%)", fontsize=11)
ax.set_ylim(0, 102)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(color=grid, linewidth=0.9, alpha=0.75)
for spine in ax.spines.values():
    spine.set_color("#cbd5e1")

acc_path = out_dir / "acc_from_trace.png"
fig.tight_layout()
fig.savefig(acc_path, dpi=320)
plt.close(fig)

# Token figure
fig, ax1 = plt.subplots(figsize=(11, 5.8), facecolor=bg)
ax1.set_facecolor(bg)

bars = ax1.bar(
    rounds,
    token_per_round,
    color="#fda4af",
    edgecolor="#fb7185",
    linewidth=0.5,
    alpha=0.55,
    label="Token per Round",
    zorder=2,
)

ax1.plot(rounds, token_ma, color="#e11d48", linewidth=2.6, label="Smoothed per Round", zorder=4)
ax1.set_xlabel("Round", fontsize=11)
ax1.set_ylabel("Token per Round", color="#be123c", fontsize=11)
ax1.tick_params(axis="y", labelcolor="#be123c")
ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
ax1.grid(color=grid, linewidth=0.9, alpha=0.75)

ax2 = ax1.twinx()
ax2.fill_between(rounds, cumulative, [0] * len(rounds), color="#fde68a", alpha=0.25, zorder=1)
ax2.plot(rounds, cumulative, color="#f59e0b", linewidth=2.4, label="Cumulative Token", zorder=5)
ax2.set_ylabel("Cumulative Token", color="#b45309", fontsize=11)
ax2.tick_params(axis="y", labelcolor="#b45309")

total_token = cumulative[-1]
ax2.annotate(
    f"Total: {total_token:,}",
    xy=(rounds[-1], cumulative[-1]),
    xytext=(-95, 16),
    textcoords="offset points",
    fontsize=10,
    color="#451a03",
    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#fcd34d", alpha=0.95),
    arrowprops=dict(arrowstyle="->", color="#f59e0b", lw=1.2),
)

for spine in ax1.spines.values():
    spine.set_color("#cbd5e1")
for spine in ax2.spines.values():
    spine.set_color("#cbd5e1")

handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", frameon=True, framealpha=0.92)

plt.title("Token Cost per Round and Cumulative Growth", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
fig.tight_layout()
token_path = out_dir / "token_from_trace.png"
fig.savefig(token_path, dpi=320)
plt.close(fig)

print(f"Saved: {acc_path}")
print(f"Saved: {token_path}")
