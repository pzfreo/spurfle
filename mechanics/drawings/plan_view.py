#!/usr/bin/env python3
"""
Top-down plan view of the three-roller contact head.
Run:   python mechanics/drawings/plan_view.py
Output: mechanics/drawings/plan_view.svg
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon, Circle, Rectangle, FancyArrowPatch
import matplotlib.lines as mlines

# ── Parameters (all in mm) ──────────────────────────────────────────────────
ROLLER_OD     = 7.0
ROLLER_R      = ROLLER_OD / 2          # 3.5
PIN_D         = 1.5
PIN_BORE      = PIN_D + 0.2            # 1.7 mm running fit
HOLDER_OD     = 4.5
HOLDER_R      = HOLDER_OD / 2         # 2.25
HOLDER_EXTEND = 10.0                   # holder body length beyond pin bore (TBD)
TOUCH_SPAN    = 20.0
ROLLER_GAP    = TOUCH_SPAN / 2 - ROLLER_OD   # 3.0 mm
OUTER_X       = ROLLER_OD + ROLLER_GAP        # 10.0 mm

assert ROLLER_GAP >= 1.0,          f"C-005: gap {ROLLER_GAP}mm too small"
assert HOLDER_OD < ROLLER_OD,      "C-011: holder overhangs roller"
assert HOLDER_OD >= PIN_D + 2*1.2, "C-011: holder wall too thin"

# In plan view: y=0 at instrument edge surface, y>0 away from edge
ROLLER_Y = ROLLER_R   # roller centres 3.5 mm below edge (tangent to edge at top)

# ── Stadium polygon helper ────────────────────────────────────────────────────
def stadium_verts(cx, cy_top, cy_bot, r, n=64):
    """
    Vertices for a stadium (capsule) shape.
    cy_top: centre of the top semicircle (pin-bore end) — arc curves toward edge
    cy_bot: centre of the bottom semicircle (far end)   — arc curves away from edge
    Coordinate system: y=0 at edge, y increases downward.
    """
    # Top cap: left → right, arc bulges toward edge (smaller y)
    t_top = np.linspace(np.pi, 0, n)
    x_top = cx + r * np.cos(t_top)
    y_top = cy_top - r * np.sin(t_top)   # sin(π→0) = 0→+1→0, so y dips below cy_top
    # Bottom cap: right → left, arc bulges away from edge (larger y)
    t_bot = np.linspace(0, np.pi, n)
    x_bot = cx + r * np.cos(t_bot)
    y_bot = cy_bot + r * np.sin(t_bot)
    return np.column_stack([np.append(x_top, x_bot),
                             np.append(y_top, y_bot)])

# ── Figure setup ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 9))
ax.set_aspect('equal')
ax.invert_yaxis()   # y=0 at top (edge), positive downward
ax.set_xlim(-14, 20)
ax.set_ylim(20, -3)
ax.axis('off')
ax.set_title('Contact Head — Plan View (top down)', fontsize=13, fontweight='bold', pad=14)

# ── Instrument edge ───────────────────────────────────────────────────────────
ax.add_patch(Rectangle((-14, -2), 34, 2,
             facecolor='#b87030', alpha=0.7, zorder=1))
ax.text(15.5, -1.0, 'instrument\nedge', va='center', ha='left',
        fontsize=8, color='#6B3810')

# ── Roller configs ────────────────────────────────────────────────────────────
ROLLER_CONFIGS = [
    (-OUTER_X, 'outer L', 'Hall',       '#d0d0d0', '#555'),
    ( 0.0,     'centre',  'load cell',  '#dde0ff', '#334'),
    (+OUTER_X, 'outer R', 'Hall',       '#d0d0d0', '#555'),
]

for xr, lbl, sub, rfill, rstroke in ROLLER_CONFIGS:
    cy = ROLLER_Y   # roller centre y

    # 1. Roller filled circle (drawn first, behind holder)
    ax.add_patch(Circle((xr, cy), ROLLER_R,
                         facecolor=rfill, edgecolor='none', zorder=2))

    # 2. Holder stadium — opaque, on top of roller
    #    Pin-bore end cap centred at roller centre (cy).
    #    Holder body extends away from edge to cy + HOLDER_EXTEND.
    verts = stadium_verts(xr, cy, cy + HOLDER_EXTEND, HOLDER_R)
    ax.add_patch(Polygon(verts, closed=True,
                          facecolor='#f5c87a', edgecolor='#b07820',
                          linewidth=1.5, zorder=3))

    # 3. Roller outline redrawn on top — shows 7 mm boundary clearly
    ax.add_patch(Circle((xr, cy), ROLLER_R,
                         facecolor='none', edgecolor=rstroke,
                         linewidth=1.5, zorder=4))

    # 4. Pin bore (hole through ASA at roller centre)
    ax.add_patch(Circle((xr, cy), PIN_BORE / 2,
                         facecolor='#f8f8f8', edgecolor='#666',
                         linewidth=1.0, zorder=5))

    # 5. Steel pin visible through bore
    ax.add_patch(Circle((xr, cy), PIN_D / 2,
                         facecolor='#aaa', edgecolor='#444',
                         linewidth=0.8, zorder=6))

    # Labels above roller
    ax.text(xr, cy - ROLLER_R - 0.4, lbl,
            ha='center', va='bottom', fontsize=8, fontweight='bold', color='#222')
    ax.text(xr, cy - ROLLER_R - 1.2, f'({sub})',
            ha='center', va='bottom', fontsize=7, color='#555')

# ── Holder width callout — right outer roller ─────────────────────────────────
ann_xr = OUTER_X
ann_cy = ROLLER_Y + HOLDER_EXTEND * 0.55   # mid-body
ax.annotate('', xy=(ann_xr - HOLDER_R, ann_cy), xytext=(ann_xr + HOLDER_R, ann_cy),
            arrowprops=dict(arrowstyle='<->', color='#b07820', lw=1.0))
ax.text(ann_xr + HOLDER_R + 0.3, ann_cy, f'⌀{HOLDER_OD:.1f} mm holder',
        va='center', fontsize=8, color='#b07820')

# ── Dimensions ────────────────────────────────────────────────────────────────
# 20 mm touch-point span (above edge)
dim_y_span = -1.5
ax.annotate('', xy=(-OUTER_X, dim_y_span), xytext=(OUTER_X, dim_y_span),
            arrowprops=dict(arrowstyle='<->', color='#333', lw=1.2))
ax.text(0, dim_y_span - 0.4, f'{TOUCH_SPAN:.0f} mm touch-point span',
        ha='center', va='bottom', fontsize=9, color='#333')

# Roller OD — left outer roller, below holder
dim_y_rod = ROLLER_Y + HOLDER_EXTEND + HOLDER_R + 1.5
ax.annotate('', xy=(-OUTER_X - ROLLER_R, dim_y_rod),
            xytext=(-OUTER_X + ROLLER_R, dim_y_rod),
            arrowprops=dict(arrowstyle='<->', color='#555', lw=1.0))
ax.text(-OUTER_X, dim_y_rod + 0.5,
        f'⌀{ROLLER_OD:.0f} mm roller', ha='center', va='top', fontsize=8, color='#555')

# Gap 3 mm — between left outer and centre roller
dim_y_gap = dim_y_rod + 2.5
ax.annotate('', xy=(-OUTER_X + ROLLER_R, dim_y_gap),
            xytext=(-ROLLER_R, dim_y_gap),
            arrowprops=dict(arrowstyle='<->', color='#555', lw=1.0))
ax.text((-OUTER_X + ROLLER_R - ROLLER_R) / 2, dim_y_gap + 0.5,
        f'{ROLLER_GAP:.0f} mm gap', ha='center', va='top', fontsize=8, color='#555')

# Wall thickness note (text, not tiny arrows)
wt_wall = (HOLDER_OD - PIN_D) / 2      # 1.5 mm
wt_proj = (ROLLER_OD - HOLDER_OD) / 2  # 1.25 mm
ax.text(0, ROLLER_Y + HOLDER_EXTEND + HOLDER_R + 3.2,
        f'holder wall {wt_wall:.2g} mm  |  roller protrusion {wt_proj:.4g} mm',
        ha='center', va='top', fontsize=7.5, color='#555', style='italic')

# ── Legend (bottom-left, away from all geometry) ─────────────────────────────
lx, ly = -13.5, 13.0
ax.add_patch(Circle((lx + 0.7, ly), 0.7, facecolor='#d0d0d0', edgecolor='#555', lw=1.2))
ax.text(lx + 1.7, ly, 'nylon roller (FDM)', va='center', fontsize=8)

ax.add_patch(Rectangle((lx, ly + 1.8), 1.4, 2.4,
             facecolor='#f5c87a', edgecolor='#b07820', lw=1.5))
ax.text(lx + 1.7, ly + 3.0, 'ASA holder (FDM) — stadium shaped', va='center', fontsize=8)

ax.add_patch(Circle((lx + 0.7, ly + 5.4), 0.7,
             facecolor='#f8f8f8', edgecolor='#666', lw=1.0))
ax.add_patch(Circle((lx + 0.7, ly + 5.4), PIN_D / 2,
             facecolor='#aaa', edgecolor='#444', lw=0.9))
ax.text(lx + 1.7, ly + 5.4,
        f'pin bore ⌀{PIN_BORE} mm  /  steel pin ⌀{PIN_D} mm',
        va='center', fontsize=8)

# ── Scale bar ─────────────────────────────────────────────────────────────────
sb_x, sb_y = -13, 18.5
ax.plot([sb_x, sb_x + 5], [sb_y, sb_y], 'k-', lw=2)
ax.plot([sb_x, sb_x], [sb_y - 0.3, sb_y + 0.3], 'k-', lw=1.5)
ax.plot([sb_x + 5, sb_x + 5], [sb_y - 0.3, sb_y + 0.3], 'k-', lw=1.5)
ax.text(sb_x + 2.5, sb_y + 0.5, '5 mm', ha='center', va='bottom', fontsize=8)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan_view.svg')
fig.savefig(out, format='svg', bbox_inches='tight', dpi=150)
plt.close(fig)
print(f"Written: {out}")
print(f"ROLLER_GAP={ROLLER_GAP}mm  OUTER_X={OUTER_X}mm  holder wall={(HOLDER_OD-PIN_D)/2}mm")
