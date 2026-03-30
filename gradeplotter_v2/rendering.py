from __future__ import annotations

import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.ticker import MaxNLocator

GRADE_CUTOFFS = [x / 10.0 for x in range(0, 41)]
TICK_LABELS = [str(x / 10) for x in range(0, 41, 5)] + ["NaN"]


def _ax_no_borders(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#DDDDDD")
    axis.spines["bottom"].set_color("#DDDDDD")
    axis.set_axisbelow(True)
    axis.yaxis.grid(True, color="#EEEEEE")
    axis.xaxis.grid(True, color="#EEEEEE")
    axis.tick_params(bottom=True, left=True)


def _grade_distribution(grades: list[float]) -> list[int]:
    return [len([x for x in grades if x == cutoff]) for cutoff in GRADE_CUTOFFS]


def _build_stats_text(numerical: list[float], non_numerical: list[str]) -> str:
    if not numerical:
        return "No grades found"
    stdev = "0" if len(numerical) < 2 else f"{statistics.stdev(numerical):.2f}"
    return (
        f"Total: {len(numerical) + len(non_numerical)}\n"
        f"Mean: {statistics.mean(numerical):.2f}\n"
        f"Median: {statistics.median(numerical):.2f}\n"
        f"Stdev: {stdev}\n"
        f"Min: {min(numerical):.1f}\n"
        f"Max: {max(numerical):.1f}"
    )


def _build_non_num_stats(non_numerical: list[str]) -> str:
    stats = sorted(set(non_numerical))
    return "\n".join(f"{label}x{non_numerical.count(label)}" for label in stats)


def render_histogram(grades: list[float], title: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bins = [x / 10.0 for x in range(0, 42, 2)]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.hist(grades, bins=bins, edgecolor="black")
    ax.set_title(title)
    ax.set_xlabel("Grade")
    ax.set_ylabel("Students")
    ax.set_xlim(0, 4.1)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def render_legacy_style_histogram(
    numerical_grades: list[float],
    non_numerical_grades: list[str],
    title: str,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    distribution = _grade_distribution(numerical_grades)
    distribution.append(len(non_numerical_grades))

    fig, axis = plt.subplots(figsize=(11, 6))
    _ax_no_borders(axis)
    left = range(1, 47)
    nan_height = distribution[-1]
    heights = distribution[:-1] + [0, 0, 0, 0, nan_height]

    axis.bar(left, heights, width=0.8, color=["lightsteelblue"])
    axis.yaxis.set_major_locator(MaxNLocator(integer=True))
    axis.xaxis.set_major_locator(ticker.FixedLocator([1 + x * 5 for x in range(0, len(TICK_LABELS))]))
    axis.xaxis.set_ticklabels(TICK_LABELS)

    axis.set_title(title, pad=15, color="#333333", weight="bold")
    axis.set_xlabel("Grades")
    axis.set_ylabel("Students")

    loc = min(heights) + (max(heights) - min(heights)) / 2 if heights else 0
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    axis.text(0.5, loc, _build_stats_text(numerical_grades, non_numerical_grades), bbox=props)
    non_num_stats = _build_non_num_stats(non_numerical_grades)
    if non_num_stats:
        axis.text(len(GRADE_CUTOFFS) + 0.7, loc, non_num_stats, bbox=props)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def render_multiyear_trend(points: list[tuple[str, float]], title: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = list(range(len(points)))
    labels = [term for term, _ in points]
    y = [value for _, value in points]
    ax.plot(x, y, marker="o", linewidth=2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0.0, 4.0)
    ax.set_title(title)
    ax.set_xlabel("Term")
    ax.set_ylabel("Median Grade")
    for idx, value in enumerate(y):
        ax.text(idx, value, f"{value:.2f}", fontsize=8, ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
