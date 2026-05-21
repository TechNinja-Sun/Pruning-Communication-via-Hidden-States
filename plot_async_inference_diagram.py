"""绘制“异步推理 + 向量同步提取”中文示意图。

用法:
    python plot_async_inference_diagram.py
    python plot_async_inference_diagram.py --png async_pipeline.png --svg async_pipeline.svg
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="绘制异步推理与向量同步提取一体化流程图（中文）。"
    )
    parser.add_argument(
        "--png",
        default="async_inference_vector_pipeline.png",
        help="PNG 输出路径。",
    )
    parser.add_argument(
        "--svg",
        default="async_inference_vector_pipeline.svg",
        help="SVG 输出路径。",
    )
    parser.add_argument(
        "--font-path",
        default=None,
        help="可选：指定中文字体文件路径（如 simhei.ttf / msyh.ttc）。",
    )
    return parser.parse_args()


def draw_box(ax, x, y, w, h, text, fc, ec="#334155", fs=10, lw=1.2, rounded=0.02):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={rounded}",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#0f172a")


def draw_arrow(ax, p1, p2, text=None, color="#475569", ls="-", lw=1.8, fs=9, text_offset=(0, 0)):
    arrow = FancyArrowPatch(
        p1,
        p2,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        linestyle=ls,
        connectionstyle="arc3,rad=0",
    )
    ax.add_patch(arrow)
    if text:
        mx = (p1[0] + p2[0]) / 2 + text_offset[0]
        my = (p1[1] + p2[1]) / 2 + text_offset[1]
        ax.text(mx, my, text, fontsize=fs, color="#334155", ha="center", va="center")


def setup_chinese_font(font_path: str | None = None) -> None:
    if font_path:
        font_file = Path(font_path)
        if font_file.exists():
            font_manager.fontManager.addfont(str(font_file))
            font_name = font_manager.FontProperties(fname=str(font_file)).get_name()
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = [font_name, "DejaVu Sans", "Arial"]
            plt.rcParams["axes.unicode_minus"] = False
            return

    preferred_fonts = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "PingFang SC",
        "WenQuanYi Zen Hei",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = None
    for name in preferred_fonts:
        if name in available:
            chosen = name
            break

    if chosen:
        # Force matplotlib to use a CJK-capable sans font first.
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [chosen, "DejaVu Sans", "Arial"]
    else:
        # Keep a fallback list even when no preferred CJK font is detected.
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Noto Sans CJK SC",
            "Source Han Sans SC",
            "DejaVu Sans",
            "Arial",
        ]
    plt.rcParams["axes.unicode_minus"] = False


def draw_lane(ax, y, label, color="#94a3b8"):
    ax.plot([0.08, 0.95], [y, y], color=color, linewidth=1.2, linestyle="--", alpha=0.7)
    draw_box(ax, 0.01, y - 0.03, 0.06, 0.06, label, fc="#f1f5f9", ec="#94a3b8", fs=9, lw=1.0, rounded=0.01)


def make_figure(font_path: str | None = None) -> plt.Figure:
    plt.style.use("seaborn-v0_8-white")
    # Call after style.use so style presets cannot overwrite Chinese font settings.
    setup_chinese_font(font_path)
    fig, ax = plt.subplots(figsize=(15, 9), facecolor="#f8fafc")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # 标题。
    ax.text(
        0.5,
        0.95,
        "异步推理与语义向量同步提取一体化示意图",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#0f172a",
    )
    ax.text(
        0.5,
        0.915,
        "单次模型调用同时返回文本结果与语义嵌入向量，并立即进入统计分析",
        ha="center",
        va="center",
        fontsize=11,
        color="#334155",
    )

    # 时间轴与泳道。
    ax.text(0.08, 0.86, "时间轴 (t0 -> t4)", fontsize=10, color="#475569")
    draw_arrow(ax, (0.08, 0.84), (0.95, 0.84), color="#475569", lw=1.6)

    draw_lane(ax, 0.74, "调度层")
    draw_lane(ax, 0.60, "推理层")
    draw_lane(ax, 0.46, "向量层")
    draw_lane(ax, 0.32, "统计层")

    # t0: 提交任务。
    draw_box(ax, 0.10, 0.70, 0.14, 0.08, "多智能体调度器\n提交请求", fc="#dbeafe")
    draw_arrow(ax, (0.24, 0.74), (0.32, 0.74), "t0", fs=9)

    # t1: 异步网关与事件循环。
    draw_box(ax, 0.32, 0.70, 0.20, 0.08, "异步推理网关\nasyncio 事件循环", fc="#c7d2fe")
    draw_box(ax, 0.55, 0.70, 0.17, 0.08, "统一模型调用\n单次 API 请求", fc="#bfdbfe")
    draw_arrow(ax, (0.52, 0.74), (0.55, 0.74), "t1")

    # t2: 并行执行。
    draw_box(ax, 0.76, 0.56, 0.18, 0.09, "分支 A: 文本生成\n流式/最终答案", fc="#fde68a")
    draw_box(ax, 0.76, 0.42, 0.18, 0.09, "分支 B: 向量提取\n语义嵌入输出", fc="#fecaca")
    draw_arrow(ax, (0.72, 0.73), (0.76, 0.60), "并发启动", color="#2563eb", text_offset=(0.0, 0.03))
    draw_arrow(ax, (0.72, 0.71), (0.76, 0.46), color="#2563eb")

    ax.text(0.64, 0.53, "同一次调用返回双结果", fontsize=10, color="#1d4ed8")
    ax.text(0.63, 0.50, "并行而非串行", fontsize=10, color="#1d4ed8", fontweight="bold")

    # t3: 汇合屏障。
    draw_box(ax, 0.53, 0.28, 0.20, 0.09, "同步汇合点\nawait gather(text, embedding)", fc="#bbf7d0")
    draw_arrow(ax, (0.76, 0.56), (0.63, 0.37), "t3 汇合", color="#15803d", text_offset=(0.0, 0.02))
    draw_arrow(ax, (0.76, 0.46), (0.63, 0.28), color="#15803d")

    # t4: 后续分析流程。
    draw_box(ax, 0.10, 0.26, 0.18, 0.09, "相似度计算\n(cosine)", fc="#e2e8f0")
    draw_box(ax, 0.30, 0.26, 0.20, 0.09, "交互关系构建\n(边权/拓扑)", fc="#e2e8f0")
    draw_box(ax, 0.75, 0.26, 0.20, 0.09, "指标统计与记录\n准确率/耗时/开销", fc="#e2e8f0")
    draw_arrow(ax, (0.53, 0.32), (0.50, 0.30), color="#475569")
    draw_arrow(ax, (0.53, 0.32), (0.28, 0.30), color="#475569")
    draw_arrow(ax, (0.73, 0.32), (0.75, 0.30), "t4", color="#475569")

    # 传统串行路径对比。
    draw_box(ax, 0.08, 0.11, 0.32, 0.1, "传统串行: 先取文本 -> 再发向量请求", fc="#ffffff", ec="#94a3b8", fs=10, lw=1.0)
    draw_box(ax, 0.42, 0.11, 0.23, 0.1, "额外网络往返\n格式转换成本", fc="#ffffff", ec="#94a3b8", fs=10, lw=1.0)
    draw_box(ax, 0.67, 0.11, 0.28, 0.1, "风险: 时间差导致版本不一致\n并发下累计时延更明显", fc="#ffffff", ec="#94a3b8", fs=10, lw=1.0)
    draw_arrow(ax, (0.40, 0.16), (0.42, 0.16), color="#94a3b8", ls="--", lw=1.2)
    draw_arrow(ax, (0.65, 0.16), (0.67, 0.16), color="#94a3b8", ls="--", lw=1.2)

    # 关键结论。
    draw_box(ax, 0.08, 0.01, 0.87, 0.07, "结论: 一体化异步机制保证“输出结果”和“结构化分析输入”同步生成，降低耗时并提升统计准确性。", fc="#ecfeff", ec="#0ea5e9", fs=11, lw=1.3)

    fig.tight_layout()
    return fig


def main() -> None:
    args = parse_args()
    png_path = Path(args.png).resolve()
    svg_path = Path(args.svg).resolve()

    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    fig = make_figure(args.font_path)
    fig.savefig(png_path, dpi=320, bbox_inches="tight")
    fig.savefig(svg_path, dpi=320, bbox_inches="tight")
    plt.close(fig)

    print(f"已保存 PNG: {png_path}")
    print(f"已保存 SVG: {svg_path}")


if __name__ == "__main__":
    main()
