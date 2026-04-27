"""Generate publication-quality figures for the manuscript.

Produces:
    fig1_pipeline.png        — system block diagram
    fig2_angle_geometry.png  — angle between v_motion and v_ref
    fig3_state_machine.png   — violation state-machine diagram
    fig4_lane_example.png    — annotated frame mockup with lanes + arrows
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent


def _box(ax, xy, w, h, text, fc="#ECEFF4", ec="#2E3440", fontsize=9, bold=False):
    patch = FancyBboxPatch(
        (xy[0], xy[1]), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.2, facecolor=fc, edgecolor=ec,
    )
    ax.add_patch(patch)
    weight = "bold" if bold else "normal"
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text,
            ha="center", va="center", fontsize=fontsize, weight=weight)


def _arrow(ax, src, dst, color="#2E3440", lw=1.4):
    ax.add_patch(FancyArrowPatch(src, dst,
                                  arrowstyle="->,head_width=4,head_length=7",
                                  color=color, lw=lw, shrinkA=4, shrinkB=4))


# ----------------------------------------------------------------------
# Figure 1 — system pipeline
# ----------------------------------------------------------------------
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(9, 3.2), dpi=220)
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.2); ax.axis("off")

    stages = [
        ("Input\nCCTV Frame",             0.2,  "#D8DEE9"),
        ("YOLO26\nDetection",             1.8,  "#A3BE8C"),
        ("BoT-SORT /\nByteTrack",         3.4,  "#A3BE8C"),
        ("Motion-Vector\nAnalysis",       5.0,  "#88C0D0"),
        ("Lane Reference\n& Angle Test",  6.6,  "#88C0D0"),
        ("Violation\nState Machine",      8.2,  "#BF616A"),
    ]
    w, h, y = 1.45, 1.3, 0.95
    centres = []
    for label, x, color in stages:
        _box(ax, (x, y), w, h, label, fc=color, bold=True)
        centres.append((x + w / 2, y + h / 2))

    for a, b in zip(centres[:-1], centres[1:]):
        _arrow(ax, (a[0] + w / 2 - 0.05, a[1]), (b[0] - w / 2 + 0.05, b[1]))

    ax.text(5, 0.45,
            "Outputs: annotated video · CSV log of violations · per-frame metrics",
            ha="center", fontsize=9, style="italic", color="#4C566A")
    fig.suptitle("Fig. 1. Block diagram of the proposed wrong-way detection pipeline.",
                 fontsize=10, y=0.03)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_pipeline.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------
# Figure 2 — angle geometry
# ----------------------------------------------------------------------
def fig_angle_geometry():
    fig, ax = plt.subplots(figsize=(5.2, 4.2), dpi=220)
    ax.set_xlim(-3.2, 3.2); ax.set_ylim(-3.2, 3.2); ax.set_aspect("equal"); ax.axis("off")

    # lane background
    lane = mpatches.Polygon([[-1.3, -3], [1.3, -3], [1.3, 3], [-1.3, 3]],
                             closed=True, facecolor="#E5E9F0", edgecolor="#4C566A")
    ax.add_patch(lane)
    ax.plot([0, 0], [-3, 3], color="white", linestyle="--", linewidth=1)

    # reference vector (allowed direction)
    ax.annotate("", xy=(0, 2.3), xytext=(0, -2.3),
                arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=2.4))
    ax.text(0.15, 2.0, r"$\mathbf{v}_{ref}$", color="#2E7D32", fontsize=13, weight="bold")

    # motion vector
    theta = np.deg2rad(155)
    mx, my = 2.0 * np.cos(theta), 2.0 * np.sin(theta)
    ax.annotate("", xy=(mx, my), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="#B71C1C", lw=2.4))
    ax.text(mx - 0.8, my + 0.15, r"$\mathbf{v}_{motion}$", color="#B71C1C", fontsize=13, weight="bold")

    # arc showing angle θ
    arc = mpatches.Arc((0, 0), 1.6, 1.6, angle=0, theta1=90, theta2=155,
                       color="#4C566A", lw=1.4)
    ax.add_patch(arc)
    ax.text(-0.45, 1.0, r"$\theta$", fontsize=14, color="#4C566A")

    # threshold cone annotation
    ax.text(0, -3.45,
            r"$\theta \geq 135\degree \;\; \Rightarrow$  opposing motion",
            ha="center", fontsize=10)

    fig.suptitle("Fig. 2. Angle between motion vector and lane reference direction.",
                 fontsize=10, y=0.03)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_angle_geometry.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------
# Figure 3 — state machine
# ----------------------------------------------------------------------
def fig_state_machine():
    fig, ax = plt.subplots(figsize=(8, 3.3), dpi=220)
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.3); ax.axis("off")

    states = [
        ("NORMAL",    1.5, "#A3BE8C"),
        ("OPPOSING",  5.0, "#EBCB8B"),
        ("VIOLATING", 8.5, "#BF616A"),
    ]
    y = 1.3; r = 0.75
    for name, x, col in states:
        circ = mpatches.Circle((x, y), r, facecolor=col, edgecolor="#2E3440", linewidth=1.4)
        ax.add_patch(circ)
        ax.text(x, y, name, ha="center", va="center", weight="bold", fontsize=10)

    _arrow(ax, (1.5 + r, y + 0.15), (5.0 - r, y + 0.15))
    ax.text(3.25, y + 0.55, r"$\theta \geq \theta_{th}$", ha="center", fontsize=9.5)

    _arrow(ax, (5.0 + r, y + 0.15), (8.5 - r, y + 0.15))
    ax.text(6.75, y + 0.55, r"streak $\geq N_{min}$", ha="center", fontsize=9.5)

    _arrow(ax, (5.0 - r, y - 0.15), (1.5 + r, y - 0.15))
    ax.text(3.25, y - 0.6, r"$\theta < \theta_{th}$ for $>\tau$ frames",
            ha="center", fontsize=9.5, color="#4C566A")

    # self-loop on VIOLATING
    ax.add_patch(FancyArrowPatch((8.5 + r * 0.3, y + r),
                                  (8.5 + r * 0.3, y + r + 0.8),
                                  arrowstyle="->", color="#2E3440",
                                  connectionstyle="arc3,rad=1.6", lw=1.4))
    ax.text(9.35, y + r + 0.55, "latched\nuntil track exits",
            ha="left", va="center", fontsize=8.5, color="#4C566A")

    fig.suptitle("Fig. 3. Violation state machine with hysteresis.",
                 fontsize=10, y=0.03)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_state_machine.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------
# Figure 4 — schematic lane-annotated frame
# ----------------------------------------------------------------------
def fig_lane_example():
    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=220)
    ax.set_xlim(0, 1280); ax.set_ylim(720, 0); ax.set_aspect("equal"); ax.axis("off")

    bg = mpatches.Rectangle((0, 0), 1280, 720, facecolor="#2B3038")
    ax.add_patch(bg)

    # two lanes
    south = mpatches.Polygon([[520, 100], [760, 100], [820, 700], [440, 700]],
                             closed=True, facecolor="#3B4252", edgecolor="#ECEFF4")
    north = mpatches.Polygon([[260, 100], [500, 100], [420, 700], [40,  700]],
                             closed=True, facecolor="#3B4252", edgecolor="#ECEFF4")
    ax.add_patch(south); ax.add_patch(north)

    # reference arrows (placed on lane edges so they don't clash with vehicles)
    ax.annotate("", xy=(780, 640), xytext=(780, 160),
                arrowprops=dict(arrowstyle="->", color="#A3BE8C", lw=2.4))
    ax.text(795, 380, "v_ref\n(south)", color="#A3BE8C", fontsize=8.5, weight="bold")

    ax.annotate("", xy=(120, 200), xytext=(120, 640),
                arrowprops=dict(arrowstyle="->", color="#A3BE8C", lw=2.4))
    ax.text(10, 380, "v_ref\n(north)", color="#A3BE8C", fontsize=8.5, weight="bold")

    # legitimate vehicle going south (in southbound lane)
    ax.add_patch(mpatches.Rectangle((600, 280), 80, 55, edgecolor="#A3BE8C", facecolor="none", lw=2))
    ax.annotate("", xy=(640, 395), xytext=(640, 340),
                arrowprops=dict(arrowstyle="->", color="#A3BE8C", lw=2))
    ax.text(495, 270, "#12 car 0.91", color="#A3BE8C", fontsize=8, weight="bold")

    # wrong-way vehicle in southbound lane going north
    ax.add_patch(mpatches.Rectangle((590, 510), 80, 55, edgecolor="#BF616A", facecolor="none", lw=2.4))
    ax.annotate("", xy=(630, 450), xytext=(630, 500),
                arrowprops=dict(arrowstyle="->", color="#BF616A", lw=2.2))
    ax.text(440, 600, "#19 motorcycle 0.83  [WRONG-WAY]",
            color="#BF616A", fontsize=8, weight="bold")

    # legitimate vehicle going north (in northbound lane)
    ax.add_patch(mpatches.Rectangle((320, 410), 80, 55, edgecolor="#A3BE8C", facecolor="none", lw=2))
    ax.annotate("", xy=(360, 395), xytext=(360, 450),
                arrowprops=dict(arrowstyle="->", color="#A3BE8C", lw=2))
    ax.text(260, 395, "#7 car 0.88", color="#A3BE8C", fontsize=8, weight="bold")

    fig.suptitle("Fig. 4. Schematic annotated frame: lane polygons, reference\ndirections (green), and a wrong-way violation (red).",
                 fontsize=10, y=0.04)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_lane_example.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fig_pipeline()
    fig_angle_geometry()
    fig_state_machine()
    fig_lane_example()
    print("Figures written to", OUT)
