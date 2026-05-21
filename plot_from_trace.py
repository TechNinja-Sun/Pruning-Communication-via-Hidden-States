import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

traces = [
    {
        "label": "similar",
        "path": Path(r"D:\毕设\PruneComm-HS\exp\result_20260421_210635\similar\trace_20260421_210635.json"),
    },
    {
        "label": "hybrid",
        "path": Path(r"D:\毕设\PruneComm-HS\exp\result_20260421_173629\hybrid\trace_20260421_173629.json"),
    },
    {
        "label": "dissimilar",
        "path": Path(r"D:\毕设\PruneComm-HS\exp\result_20260422_115739\dissimilar\trace_20260422_115739.json"),
    },
]

out_dir = Path(__file__).resolve().parent


def load_trace(trace_file):
    with trace_file.open("r", encoding="utf-8") as f:
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

    cumulative_tokens = []
    running_total = 0
    for token_count in token_per_round:
        running_total += token_count
        cumulative_tokens.append(running_total)

    cumulative_acc = []
    running_acc = 0.0
    for index, value in enumerate(acc, start=1):
        running_acc += value
        cumulative_acc.append(running_acc / index)

    return {
        "label": trace_file.parent.name,
        "rounds": rounds,
        "acc_pct": [value * 100.0 for value in acc],
        "token_per_round": token_per_round,
        "cumulative_tokens": cumulative_tokens,
        "cumulative_acc": [value * 100.0 for value in cumulative_acc],
        "final_acc": acc[-1] * 100.0 if acc else 0.0,
        "final_token_total": cumulative_tokens[-1] if cumulative_tokens else 0,
    }


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


series_list = [load_trace(item["path"]) for item in traces]

acc_colors = ["#0ea5e9", "#f97316", "#16a34a"]
acc_fill_colors = ["#8ecae6", "#fdba74", "#86efac"]
token_colors = ["#e11d48", "#7c3aed", "#16a34a"]
token_fill_colors = ["#fda4af", "#ddd6fe", "#86efac"]

plt.style.use("seaborn-v0_8-whitegrid")

bg = "#f8fafc"
grid = "#e2e8f0"

fig_acc, ax_acc = plt.subplots(figsize=(13, 5.8), facecolor=bg)
fig_token, ax_token = plt.subplots(figsize=(13, 5.8), facecolor=bg)

fig_acc.patch.set_facecolor(bg)
fig_token.patch.set_facecolor(bg)
ax_acc.set_facecolor(bg)
ax_token.set_facecolor(bg)

for index, series in enumerate(series_list):
    rounds = series["rounds"]
    acc_pct = series["acc_pct"]
    acc_ma = moving_average(acc_pct, window=7)
    color = acc_colors[index % len(acc_colors)]
    fill_color = acc_fill_colors[index % len(acc_fill_colors)]
    label = series["label"]

    ax_acc.fill_between(rounds, acc_pct, [0] * len(rounds), color=fill_color, alpha=0.16, zorder=1)
    ax_acc.plot(rounds, acc_pct, color=color, linewidth=2.6, label=f"{label} ACC", zorder=3)
    ax_acc.scatter(rounds, acc_pct, color=color, s=14, alpha=0.8, zorder=4)
    ax_acc.plot(rounds, acc_ma, color=color, linestyle="--", linewidth=2.0, label=f"{label} 7-round avg", zorder=5)

    final_round = rounds[-1]
    final_acc = acc_pct[-1]
    ax_acc.scatter([final_round], [final_acc], color=color, s=42, zorder=6)
    ax_acc.annotate(
        f"{label} final: {final_acc:.2f}%",
        xy=(final_round, final_acc),
        xytext=(-110, 18 + index * 18),
        textcoords="offset points",
        fontsize=9,
        color="#0f172a",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=fill_color, alpha=0.95),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.1),
    )

ax_acc.set_title("Accuracy Comparison Across Three Experiments", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
ax_acc.set_xlabel("Round", fontsize=11)
ax_acc.set_ylabel("Accuracy (%)", fontsize=11)
ax_acc.set_ylim(0, 102)
ax_acc.xaxis.set_major_locator(MaxNLocator(integer=True))
ax_acc.grid(color=grid, linewidth=0.9, alpha=0.75)
for spine in ax_acc.spines.values():
    spine.set_color("#cbd5e1")
ax_acc.legend(loc="lower right", frameon=True, framealpha=0.92, ncol=2)

for index, series in enumerate(series_list):
    rounds = series["rounds"]
    token_per_round = series["token_per_round"]
    cumulative_tokens = series["cumulative_tokens"]
    token_ma = moving_average(token_per_round, window=7)
    color = token_colors[index % len(token_colors)]
    fill_color = token_fill_colors[index % len(token_fill_colors)]
    label = series["label"]

    ax_token.bar(
        rounds,
        token_per_round,
        color=fill_color,
        edgecolor=color,
        linewidth=0.5,
        alpha=0.40,
        label=f"{label} token/round",
        zorder=2,
    )
    ax_token.plot(rounds, token_ma, color=color, linewidth=2.2, label=f"{label} smoothed", zorder=4)
    ax_token.plot(rounds, cumulative_tokens, color=color, linestyle="--", linewidth=2.2, label=f"{label} cumulative", zorder=5)

    final_round = rounds[-1]
    final_total = cumulative_tokens[-1]
    ax_token.annotate(
        f"{label} total: {final_total:,}",
        xy=(final_round, cumulative_tokens[-1]),
        xytext=(-120, 12 + index * 18),
        textcoords="offset points",
        fontsize=9,
        color="#111827",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=fill_color, alpha=0.95),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.1),
    )

ax_token.set_title("Token Cost Comparison Across Three Experiments", fontsize=15, fontweight="bold", color="#0f172a", pad=10)
ax_token.set_xlabel("Round", fontsize=11)
ax_token.set_ylabel("Token Count", fontsize=11)
ax_token.xaxis.set_major_locator(MaxNLocator(integer=True))
ax_token.grid(color=grid, linewidth=0.9, alpha=0.75)
for spine in ax_token.spines.values():
    spine.set_color("#cbd5e1")
ax_token.legend(loc="upper left", frameon=True, framealpha=0.92, ncol=2)

acc_path = out_dir / "acc_compare.png"
token_path = out_dir / "token_compare.png"

fig_acc.tight_layout()
fig_acc.savefig(acc_path, dpi=320)
plt.close(fig_acc)

fig_token.tight_layout()
fig_token.savefig(token_path, dpi=320)
plt.close(fig_token)

print(f"Saved: {acc_path}")
print(f"Saved: {token_path}")
