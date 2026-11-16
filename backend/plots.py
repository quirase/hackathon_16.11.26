"""Seaborn/Matplotlib editorial SVG plot generator matching LexisTube's palette."""

from __future__ import annotations

import io
import re
import threading
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from cefr_analyzer.levels import LEVELS as CEFR_LEVELS, number as level_number

CEFR_COLORS = {
    "A1": "#17655B",
    "A2": "#1E4FD6",
    "B1": "#9A4A06",
    "B2": "#B93815",
    "C1": "#93183A",
    "C2": "#4C1D95",
}
# Empirical baseline share across calibration_data/*.txt
BASELINE_SHARE = {
    "A1": 0.8318,
    "A2": 0.0905,
    "B1": 0.0407,
    "B2": 0.0252,
    "C1": 0.0066,
    "C2": 0.0051,
}

_PLOT_LOCK = threading.Lock()
_BG_PLATE = "#FDFBF7"
_BG_BAR = "#E6E0D4"
_INK = "#171614"
_MUTED = "#736D64"
_HAIRLINE = "#E0DBD0"
_VERMILION = "#C83E2B"


def render_joint_cefr_svg(
    lexical_matches: list[dict[str, Any]],
    lex_dist: dict[str, int],
) -> str | None:
    """Render a Seaborn JointGrid SVG: pacing (top), word scatter (center), CEFR lift (right)."""
    xs: list[float] = []
    ys: list[float] = []
    colors: list[str] = []

    for m in lexical_matches:
        lvl = m.get("level")
        tcs = m.get("time_codes") or []
        if lvl not in CEFR_LEVELS or not tcs or not isinstance(tcs[0], (int, float)):
            continue
        xs.append(float(tcs[0]) / 60.0)
        ys.append(float(level_number(lvl)))
        colors.append(CEFR_COLORS[lvl])

    if len(xs) < 2:
        return None

    rng = np.random.default_rng(42)
    x_arr = np.array(xs, dtype=float)
    y_arr = np.array(ys, dtype=float)
    y_jitter = y_arr + rng.uniform(-0.22, 0.22, size=len(y_arr))

    total_lex = sum(lex_dist.get(lvl, 0) for lvl in CEFR_LEVELS) or 1
    lifts = [
        (lex_dist.get(lvl, 0) / total_lex) / BASELINE_SHARE[lvl]
        for lvl in CEFR_LEVELS
    ]

    with _PLOT_LOCK:
        sns.set_theme(
            style="ticks",
            rc={
                "axes.facecolor": _BG_PLATE,
                "figure.facecolor": _BG_PLATE,
                "axes.edgecolor": _HAIRLINE,
                "axes.labelcolor": _INK,
                "xtick.color": _MUTED,
                "ytick.color": _MUTED,
                "font.family": "sans-serif",
            },
        )
        grid = sns.JointGrid(height=6.2, ratio=4, space=0.14)
        grid.fig.set_size_inches(9.2, 5.6)

        # Center: jittered CEFR word scatter + vermilion trend line
        ax = grid.ax_joint
        ax.scatter(
            x_arr,
            y_jitter,
            c=colors,
            alpha=0.52,
            s=26,
            edgecolors="none",
            rasterized=False,
        )
        if np.ptp(x_arr) > 0:
            sns.regplot(
                x=x_arr,
                y=y_arr,
                ax=ax,
                scatter=False,
                ci=95,
                line_kws={"color": _VERMILION, "linewidth": 2.0},
                color=_VERMILION,
            )
        ax.set_yticks(range(1, 7))
        ax.set_yticklabels(CEFR_LEVELS, fontweight="bold", fontsize=10)
        ax.set_ylim(0.45, 6.55)
        ax.set_xlabel("Video Time (min)", fontsize=10, labelpad=8)
        ax.set_ylabel("Word CEFR Level", fontsize=10, labelpad=8)
        ax.grid(axis="y", color=_HAIRLINE, linestyle="-", linewidth=0.7, alpha=0.8)

        # Top marginal: speech pacing histogram + KDE
        ax_top = grid.ax_marg_x
        sns.histplot(
            x=x_arr,
            bins=min(16, max(6, int(np.ceil(x_arr.max() * 2)))),
            kde=True,
            ax=ax_top,
            color=_BG_BAR,
            edgecolor=_MUTED,
            linewidth=0.7,
            line_kws={"color": _VERMILION, "linewidth": 1.6},
        )
        ax_top.set_ylabel("")
        ax_top.set_title(
            "Speech Pacing (words / interval)",
            fontsize=9,
            color=_MUTED,
            loc="left",
            pad=4,
        )

        # Right marginal: Baseline-normalized CEFR Lift (vs 1.0x calibration average)
        ax_right = grid.ax_marg_y
        y_pos = np.arange(1, 7)
        bar_colors = [CEFR_COLORS[lvl] for lvl in CEFR_LEVELS]
        ax_right.barh(y_pos, lifts, height=0.56, color=bar_colors, alpha=0.88)
        ax_right.axvline(1.0, color=_MUTED, linestyle="--", linewidth=1.0)
        max_lift = max(lifts) if lifts else 1.0
        ax_right.set_xlim(0, max(1.6, max_lift * 1.32))
        for yp, lift in zip(y_pos, lifts):
            ax_right.text(
                lift + max_lift * 0.04,
                yp,
                f"{lift:.1f}x",
                va="center",
                fontsize=8,
                color=_INK,
                fontweight="bold" if lift >= 1.2 else "normal",
            )
        ax_right.set_xlabel("Lift vs Avg", fontsize=9, color=_MUTED)
        ax_right.tick_params(axis="x", labelsize=8)

        sns.despine(fig=grid.fig)
        buf = io.StringIO()
        grid.fig.savefig(buf, format="svg", bbox_inches="tight", facecolor=_BG_PLATE)
        plt.close(grid.fig)

    svg = buf.getvalue()
    # Strip XML/DOCTYPE header and make width/height responsive inside the card
    svg = re.sub(r"^<\?xml[^>]*\?>\s*<!DOCTYPE[^>]*>\s*", "", svg, flags=re.DOTALL)
    svg = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"\s+height="[^"]*"', r'\1 width="100%"', svg, count=1)
    return svg
