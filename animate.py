"""
海上管道拖运演示动画
Offshore Pipeline Towing - Demonstration Animation

Generates a multi-panel animated GIF showing:
  Panel 1 — Surface Tow     (水面拖运)
  Panel 2 — Off-Bottom Tow  (离底拖运)
  Panel 3 — Bottom Tow      (海底拖运)
  Panel 4 — Speed vs Bollard-Pull sensitivity curve (灵敏度曲线)
"""

import math
import sys
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as _fm
_CJK_FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(_CJK_FONT):
    _fm.fontManager.addfont(_CJK_FONT)
    matplotlib.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyArrowPatch, Arc, Wedge
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(__file__))
from src.pipeline import Pipeline
from src.environment import MarineEnvironment
from src.towing import TowingAnalysis, TowingMethod
from src.catenary import TowWire, CatenaryAnalysis

# ── colour palette ────────────────────────────────────────────────────────────
C_SKY      = "#cce8f4"
C_SEA      = "#1a6fa8"
C_SEA_LITE = "#4da6d9"
C_SEABED   = "#c2a86b"
C_PIPE     = "#e07b39"
C_WIRE     = "#f5c518"
C_VESSEL   = "#2e4057"
C_ARROW    = "#e63946"
C_GREEN    = "#2dc653"
C_WHITE    = "#f8f9fa"
C_DARK     = "#1a1a2e"
C_WAVE     = "#5bc0eb"

TOTAL_FRAMES = 120
FPS = 20

# ── helpers ───────────────────────────────────────────────────────────────────

def wave_y(x_arr, t, amp=0.18, freq=0.10, speed=1.5):
    return amp * np.sin(2 * math.pi * (freq * x_arr - speed * t))


def catenary_pts(H, w, L, x0, y0, n=60):
    """Return (xs, ys) for a catenary starting at (x0, y0)."""
    if abs(w) < 1e-4 or H < 1e-3:
        xs = np.linspace(x0, x0 + L * 0.9, n)
        ys = np.full(n, y0)
        return xs, ys
    a = H / w
    s_arr = np.linspace(0, L, n)
    xs = x0 + a * np.arcsinh(s_arr / a)
    ys = y0 - a * (np.cosh(s_arr / a) - 1)   # depth increases downward
    return xs, ys


def draw_vessel(ax, cx, cy, width=2.2, height=0.55, color=C_VESSEL):
    """Draw a simplified tug silhouette."""
    hull_x = [cx - width/2, cx + width/2, cx + width/2 + 0.4,
               cx + width/2 + 0.4, cx - width/2]
    hull_y = [cy, cy, cy - height*0.4, cy - height, cy - height]
    ax.fill(hull_x, hull_y, color=color, zorder=7)
    # wheelhouse
    wx, wy = cx - width*0.1, cy
    ax.fill([wx, wx+0.7, wx+0.7, wx], [wy, wy, wy+0.5, wy+0.5],
            color="#3d5a80", zorder=8)
    # funnel
    ax.fill([cx-0.05, cx+0.05, cx+0.08, cx-0.08],
            [cy+0.5, cy+0.5, cy+0.85, cy+0.85],
            color="#e63946", zorder=8)


def draw_pipe(ax, x, y, length, diameter, color=C_PIPE, alpha=1.0):
    rect = mpatches.FancyBboxPatch(
        (x, y - diameter/2), length, diameter,
        boxstyle="round,pad=0.05",
        linewidth=1.2, edgecolor="#333", facecolor=color, alpha=alpha, zorder=6
    )
    ax.add_patch(rect)


def draw_seabed(ax, xlim, y_bed, roughness=0.12):
    xs = np.linspace(xlim[0], xlim[1], 300)
    ys = y_bed + roughness * (np.sin(xs * 3.1) * 0.5 + np.sin(xs * 7.3) * 0.3)
    ax.fill_between(xs, ys, y_bed - 1.5, color=C_SEABED, zorder=2)
    ax.plot(xs, ys, color="#8b7355", lw=0.8, zorder=3)


def draw_waves(ax, xlim, y_surface, t, n_waves=3):
    xs = np.linspace(xlim[0], xlim[1], 400)
    for k in range(n_waves):
        amp   = 0.15 + 0.05 * k
        freq  = 0.08 + 0.04 * k
        speed = 1.2 + 0.5 * k
        ys = y_surface + wave_y(xs, t, amp, freq, speed)
        ax.fill_between(xs, ys, y_surface - 0.05, color=C_SEA_LITE,
                        alpha=0.35 - 0.08 * k, zorder=4)
        ax.plot(xs, ys, color=C_WAVE, lw=0.6, alpha=0.6, zorder=5)


def draw_current_arrows(ax, xlim, y_top, y_bot, t, n=5):
    ys = np.linspace(y_top, y_bot, n)
    offset = (t * 0.8) % 3.0
    for y in ys:
        x_start = xlim[0] + 0.5 + offset
        while x_start < xlim[1] - 1:
            ax.annotate("", xy=(x_start + 1.0, y),
                        xytext=(x_start, y),
                        arrowprops=dict(arrowstyle="->", color=C_SEA_LITE,
                                        lw=0.8, alpha=0.45),
                        zorder=4)
            x_start += 3.0


def force_arrow(ax, x, y, dx, dy, label, color=C_ARROW):
    ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y),
                arrowprops=dict(arrowstyle="-|>", color=color,
                                lw=2, mutation_scale=14),
                zorder=9)
    ax.text(x + dx + 0.15, y + dy, label, color=color,
            fontsize=7, fontweight="bold", zorder=10,
            path_effects=[pe.withStroke(linewidth=2, foreground="white")])


def panel_title(ax, title, subtitle):
    ax.text(0.5, 1.035, title, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=10, fontweight="bold", color=C_WHITE)
    ax.text(0.5, 1.005, subtitle, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=7.5, color="#aac4e0")


def label_box(ax, x, y, text, fontsize=7.2):
    ax.text(x, y, text, fontsize=fontsize, color=C_WHITE,
            bbox=dict(boxstyle="round,pad=0.25", fc=C_DARK, ec="#4da6d9",
                      alpha=0.88, lw=0.8),
            zorder=11, va="center")


# ── scene geometry ─────────────────────────────────────────────────────────────
XLIM      = (0, 22)
PIPE_LEN  = 8.0
PIPE_D    = 0.55
VESSEL_W  = 2.4
TOW_WIRE  = 4.0    # visual wire length

# ── pre-compute physics once ──────────────────────────────────────────────────

def _make_tow(pipe_kw, env_kw, method, speed, **kw):
    pipe = Pipeline(**pipe_kw)
    env  = MarineEnvironment(**env_kw)
    return TowingAnalysis(pipeline=pipe, environment=env,
                          method=method, towing_speed=speed, **kw)


SURFACE_TOW = _make_tow(
    dict(outer_diameter=0.508, wall_thickness=0.0080,
         coating_thickness=0.005, coating_density=700.0,
         content_density=1.2, length=500.0),
    dict(water_depth=50, current_speed=0.5, current_direction=15,
         wave_height=1.5, wave_period=7.0),
    TowingMethod.SURFACE, 1.0, safety_factor=1.5)

OFF_BOTTOM_TOW = _make_tow(
    dict(outer_diameter=0.324, wall_thickness=0.0127,
         concrete_coating_thickness=0.040, concrete_density=3000.0,
         content_density=1.2, length=1000.0),
    dict(water_depth=80, current_speed=0.8, current_direction=0.0,
         wave_height=2.0, wave_period=9.0),
    TowingMethod.OFF_BOTTOM, 0.8, off_bottom_clearance=5.0, safety_factor=1.5)

BOTTOM_TOW = _make_tow(
    dict(outer_diameter=0.610, wall_thickness=0.0159,
         concrete_coating_thickness=0.060, concrete_density=3100.0,
         content_density=1.2, length=800.0),
    dict(water_depth=30, current_speed=0.4, current_direction=0.0,
         wave_height=1.0, wave_period=6.0),
    TowingMethod.BOTTOM, 0.5, seabed_friction_coeff=0.3, safety_factor=1.5)

# sensitivity curve data
_sens_pipe = Pipeline(outer_diameter=0.508, wall_thickness=0.0127,
                      coating_thickness=0.004, coating_density=900.0,
                      length=500.0)
_sens_env  = MarineEnvironment(water_depth=50, current_speed=0.5,
                               current_direction=0.0, wave_height=1.5,
                               wave_period=7.0)
SENS_SPEEDS = np.linspace(0.1, 1.8, 40)   # m/s
SENS_BP = []
for _v in SENS_SPEEDS:
    _t = TowingAnalysis(_sens_pipe, _sens_env, TowingMethod.SURFACE, _v, safety_factor=1.5)
    SENS_BP.append(_t.required_bollard_pull())
SENS_BP = np.array(SENS_BP)

# ── figure setup ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 9), facecolor=C_DARK)
fig.subplots_adjust(left=0.04, right=0.97, top=0.88, bottom=0.07,
                    hspace=0.48, wspace=0.32)

# 2×2 grid: top-left, top-right, bottom-left — scenes; bottom-right — curve
AX_SURF = fig.add_subplot(2, 2, 1, facecolor=C_SEA)
AX_OFFB = fig.add_subplot(2, 2, 2, facecolor=C_SEA)
AX_BOT  = fig.add_subplot(2, 2, 3, facecolor=C_SEA)
AX_SENS = fig.add_subplot(2, 2, 4, facecolor="#0d1b2a")

for ax in (AX_SURF, AX_OFFB, AX_BOT):
    ax.set_xlim(*XLIM)
    ax.tick_params(colors=C_WHITE, labelsize=6.5)
    for spine in ax.spines.values():
        spine.set_edgecolor("#3a5a7a")

AX_SENS.tick_params(colors=C_WHITE, labelsize=7)
for spine in AX_SENS.spines.values():
    spine.set_edgecolor("#3a5a7a")

# super title
fig.text(0.5, 0.955, "海上管道拖运演示  |  Offshore Pipeline Towing Demonstration",
         ha="center", fontsize=14, fontweight="bold", color=C_WHITE)
fig.text(0.5, 0.926, "三种拖运方式 · 拖缆悬链线 · 拖力灵敏度分析   "
         "Three Towing Methods · Catenary Wire · Bollard-Pull Sensitivity",
         ha="center", fontsize=8.5, color="#7ab3d4")

# ── draw static sensitivity background ────────────────────────────────────────
AX_SENS.set_xlabel("拖运速度 Towing Speed  (m/s)", color=C_WHITE, fontsize=8)
AX_SENS.set_ylabel("所需拖力 Bollard Pull  (kN)", color=C_WHITE, fontsize=8)
AX_SENS.set_xlim(SENS_SPEEDS[0], SENS_SPEEDS[-1])
AX_SENS.set_ylim(0, SENS_BP.max() * 1.18)
AX_SENS.fill_between(SENS_SPEEDS, SENS_BP, alpha=0.18, color=C_SEA_LITE)
AX_SENS.plot(SENS_SPEEDS, SENS_BP, color=C_SEA_LITE, lw=1.5, alpha=0.35, zorder=2)
panel_title(AX_SENS, "灵敏度分析  Sensitivity Analysis",
            "水面拖运 · 500 m 管道  |  Surface Tow · 500 m pipeline")

sens_dot,  = AX_SENS.plot([], [], "o", color=C_ARROW, ms=7, zorder=6)
sens_vline = AX_SENS.axvline(0, color=C_ARROW, lw=0.8, ls="--", alpha=0.7, zorder=5)
sens_label = AX_SENS.text(0, 0, "", color=C_ARROW, fontsize=7.5,
                           fontweight="bold", zorder=7)

# ── animation state ────────────────────────────────────────────────────────────
# Pipe position oscillates left↔right to show towing motion
def pipe_x(t, base=5.5, amp=1.8, period=TOTAL_FRAMES):
    return base + amp * math.sin(2 * math.pi * t / period)

# ── per-frame draw functions ───────────────────────────────────────────────────

def draw_surface_scene(ax, frame, t):
    ax.cla()
    ax.set_xlim(*XLIM)
    ax.set_facecolor(C_SKY)
    ax.set_ylim(-0.5, 3.2)
    ax.set_yticks([])
    ax.xaxis.set_visible(False)

    y_surf = 2.0
    # sky gradient (rectangles)
    ax.fill_between([0, 22], [y_surf, y_surf], [3.2, 3.2], color=C_SKY, zorder=0)
    ax.fill_between([0, 22], [-0.5, -0.5], [y_surf, y_surf],
                    color=C_SEA, alpha=0.82, zorder=1)
    draw_waves(ax, XLIM, y_surf, t)

    # pipe floats at surface
    px = pipe_x(frame, base=6.0, amp=1.2)
    draw_pipe(ax, px, y_surf - 0.3, PIPE_LEN, PIPE_D * 0.75)

    # vessel ahead
    vx = px + PIPE_LEN + TOW_WIRE + VESSEL_W
    draw_vessel(ax, vx, y_surf - 0.05)

    # tow wire (straight for surface)
    wire_x = [px + PIPE_LEN, vx - VESSEL_W / 2]
    wire_y = [y_surf - 0.05, y_surf - 0.05]
    ax.plot(wire_x, wire_y, color=C_WIRE, lw=1.8, zorder=6,
            path_effects=[pe.withStroke(linewidth=3, foreground="#333")])

    # force arrows
    force_arrow(ax, px + PIPE_LEN + 0.3, y_surf + 0.3, 1.1, 0, "F_tow")
    force_arrow(ax, px + PIPE_LEN / 2, y_surf - 0.55, -0.9, 0, "F_drag", "#4da6d9")

    # buoyancy arrow
    ax.annotate("", xy=(px + PIPE_LEN/2, y_surf + 0.55),
                xytext=(px + PIPE_LEN/2, y_surf + 0.05),
                arrowprops=dict(arrowstyle="-|>", color=C_GREEN, lw=1.5,
                                mutation_scale=12), zorder=9)
    ax.text(px + PIPE_LEN/2 + 0.15, y_surf + 0.35, "浮力\nBuoyancy",
            color=C_GREEN, fontsize=6, zorder=10)

    bp = SURFACE_TOW.required_bollard_pull()
    label_box(ax, 13.5, 0.5,
              f"拖力  {bp:.0f} kN\n"
              f"比重  SG = {SURFACE_TOW.pipeline.specific_gravity:.3f}  (< 1.0 浮)")
    panel_title(ax, "① 水面拖运  Surface Tow",
                "管道漂浮于海面  |  Pipeline floats at sea surface")


def draw_offbottom_scene(ax, frame, t):
    ax.cla()
    ax.set_xlim(*XLIM)
    ax.set_facecolor(C_SEA)
    ax.set_ylim(-5.5, 2.5)
    ax.set_yticks([])
    ax.xaxis.set_visible(False)

    y_surf = 1.8
    y_bed  = -4.5
    y_pipe = y_bed + 1.8   # off-bottom

    ax.fill_between([0, 22], [y_surf]*2, [2.5]*2, color=C_SKY, alpha=0.6, zorder=0)
    ax.fill_between([0, 22], [y_bed]*2, [y_surf]*2, color=C_SEA, alpha=0.82, zorder=1)
    draw_seabed(ax, XLIM, y_bed)
    draw_waves(ax, XLIM, y_surf, t, n_waves=2)
    draw_current_arrows(ax, XLIM, y_surf - 0.5, y_bed + 0.5, t, n=4)

    px = pipe_x(frame, base=5.0, amp=1.0)
    draw_pipe(ax, px, y_pipe - PIPE_D/2, PIPE_LEN, PIPE_D)

    # vessel at surface
    vx = px + PIPE_LEN + 5.0
    draw_vessel(ax, vx, y_surf - 0.05)

    # catenary tow wire
    H = OFF_BOTTOM_TOW.towing_resistance()
    w = TowWire(0.076, 35.0, 3500.0, 500.0).submerged_weight_per_meter
    L_vis = 5.5
    xs, ys = catenary_pts(H/1500, w/500, L_vis,
                           px + PIPE_LEN, y_pipe)
    ys_clamped = np.clip(ys, y_bed + 0.05, y_surf)
    ax.plot(xs, ys_clamped, color=C_WIRE, lw=2.0, zorder=6,
            path_effects=[pe.withStroke(linewidth=3, foreground="#222")])

    # clearance indicator
    ax.annotate("", xy=(px + PIPE_LEN/2, y_pipe - PIPE_D/2),
                xytext=(px + PIPE_LEN/2, y_bed),
                arrowprops=dict(arrowstyle="<->", color="#aac4e0", lw=1.0,
                                mutation_scale=8), zorder=8)
    ax.text(px + PIPE_LEN/2 + 0.25, (y_pipe + y_bed)/2, "离底高度\nclearance",
            color="#aac4e0", fontsize=6, zorder=9)

    force_arrow(ax, px + PIPE_LEN + 0.2, y_pipe, 1.1, 0, "F_tow")
    force_arrow(ax, px + PIPE_LEN/2, y_pipe + 0.35, -0.9, 0, "F_drag", "#4da6d9")

    bp = OFF_BOTTOM_TOW.required_bollard_pull()
    label_box(ax, 13.0, -3.8,
              f"拖力  {bp:.0f} kN\n"
              f"比重  SG = {OFF_BOTTOM_TOW.pipeline.specific_gravity:.3f}  (> 1.0 沉)")
    panel_title(ax, "② 离底拖运  Off-Bottom Tow",
                "管道悬浮于海底以上  |  Pipeline suspended above seabed")


def draw_bottom_scene(ax, frame, t):
    ax.cla()
    ax.set_xlim(*XLIM)
    ax.set_facecolor(C_SEA)
    ax.set_ylim(-4.5, 3.0)
    ax.set_yticks([])
    ax.xaxis.set_visible(False)

    y_surf = 2.0
    y_bed  = -3.5
    y_pipe = y_bed

    ax.fill_between([0, 22], [y_surf]*2, [3.0]*2, color=C_SKY, alpha=0.6, zorder=0)
    ax.fill_between([0, 22], [y_bed]*2, [y_surf]*2, color=C_SEA, alpha=0.82, zorder=1)
    draw_seabed(ax, XLIM, y_bed)
    draw_waves(ax, XLIM, y_surf, t, n_waves=2)
    draw_current_arrows(ax, XLIM, y_surf - 0.5, y_bed + 0.8, t, n=3)

    px = pipe_x(frame, base=5.0, amp=1.0)
    # pipe rests on seabed
    draw_pipe(ax, px, y_pipe, PIPE_LEN, PIPE_D)

    # friction force indicator on seabed
    fric_x = np.linspace(px - 0.5, px + PIPE_LEN + 0.5, 12)
    fric_y = np.full_like(fric_x, y_pipe - 0.08)
    for i in range(0, len(fric_x)-1, 2):
        ax.plot([fric_x[i], fric_x[i+1]],
                [fric_y[i] - 0.15 * (i % 3), fric_y[i]],
                color="#8b7355", lw=1.2, zorder=5)

    # vessel
    vx = px + PIPE_LEN + 5.0
    draw_vessel(ax, vx, y_surf - 0.05)

    # tow wire goes up to vessel fairlead
    H = BOTTOM_TOW.towing_resistance()
    w = TowWire(0.089, 48.0, 5000.0, 300.0).submerged_weight_per_meter
    L_vis = 5.0
    xs, ys = catenary_pts(H / 2000, w / 600, L_vis,
                           px + PIPE_LEN, y_pipe + PIPE_D/2)
    ys_c = np.clip(ys, y_pipe - 0.1, y_surf + 0.3)
    ax.plot(xs, ys_c, color=C_WIRE, lw=2.0, zorder=6,
            path_effects=[pe.withStroke(linewidth=3, foreground="#222")])

    # weight arrow
    ax.annotate("", xy=(px + PIPE_LEN/2, y_pipe - 0.55),
                xytext=(px + PIPE_LEN/2, y_pipe),
                arrowprops=dict(arrowstyle="-|>", color="#f5a623", lw=1.5,
                                mutation_scale=12), zorder=9)
    ax.text(px + PIPE_LEN/2 + 0.15, y_pipe - 0.38, "水中重量\nSub.Wt",
            color="#f5a623", fontsize=6, zorder=10)

    force_arrow(ax, px + PIPE_LEN + 0.2, y_pipe + PIPE_D/2, 1.1, 0, "F_tow")
    force_arrow(ax, px + PIPE_LEN/2, y_pipe + PIPE_D + 0.2, -0.9, 0, "F_drag", "#4da6d9")
    force_arrow(ax, px + 0.5, y_pipe + PIPE_D/2, -0.7, 0, "F_fric", "#f5a623")

    bp = BOTTOM_TOW.required_bollard_pull()
    label_box(ax, 13.0, -3.0,
              f"拖力  {bp:.0f} kN\n"
              f"摩擦系数 μ = {BOTTOM_TOW.seabed_friction_coeff}  "
              f"  SG = {BOTTOM_TOW.pipeline.specific_gravity:.2f}")
    panel_title(ax, "③ 海底拖运  Bottom Tow",
                "管道沿海底滑动  |  Pipeline dragged along seabed")


def draw_sensitivity(ax, frame):
    idx = int(frame / TOTAL_FRAMES * len(SENS_SPEEDS)) % len(SENS_SPEEDS)
    v = SENS_SPEEDS[idx]
    bp = SENS_BP[idx]

    # redraw static curve in case axes were cleared
    ax.fill_between(SENS_SPEEDS[:idx+1], SENS_BP[:idx+1],
                    alpha=0.30, color=C_SEA_LITE, zorder=3)
    ax.plot(SENS_SPEEDS[:idx+1], SENS_BP[:idx+1],
            color=C_SEA_LITE, lw=2, zorder=4)

    sens_dot.set_data([v], [bp])
    sens_vline.set_xdata([v, v])
    sens_label.set_position((v + 0.04, bp + 5))
    sens_label.set_text(f"{v:.2f} m/s\n{bp:.0f} kN")
    AX_SENS.set_xlim(SENS_SPEEDS[0], SENS_SPEEDS[-1])
    AX_SENS.set_ylim(0, SENS_BP.max() * 1.18)


# ── animation update ──────────────────────────────────────────────────────────
def update(frame):
    t = frame / FPS  # time in seconds

    draw_surface_scene(AX_SURF, frame, t)
    draw_offbottom_scene(AX_OFFB, frame, t)
    draw_bottom_scene(AX_BOT, frame, t)
    draw_sensitivity(AX_SENS, frame)

    # progress bar at bottom
    prog = (frame + 1) / TOTAL_FRAMES
    fig.patches = [p for p in fig.patches if not getattr(p, "_progress", False)]
    bar = mpatches.FancyBboxPatch((0.04, 0.015), 0.93 * prog, 0.008,
                                   boxstyle="round,pad=0.001",
                                   fc=C_SEA_LITE, ec="none",
                                   transform=fig.transFigure, zorder=20)
    bar._progress = True
    fig.add_artist(bar)

    return []


# ── run ───────────────────────────────────────────────────────────────────────
print("正在渲染动画帧... Rendering animation frames...")
anim = FuncAnimation(fig, update, frames=TOTAL_FRAMES,
                     interval=1000 // FPS, blit=False)

out_path = os.path.join(os.path.dirname(__file__), "offshore_pipeline_towing.gif")
writer = PillowWriter(fps=FPS)
anim.save(out_path, writer=writer, dpi=110)
print(f"动画已保存：{out_path}")
print(f"文件大小：{os.path.getsize(out_path) / 1024:.0f} KB")
