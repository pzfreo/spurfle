# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
# ]
# ///
"""Mount — base mounting block.

Run:
    uv run python mechanics/mount.py

Exports to mechanics/out/: mount (.step + .stl)
"""
from pathlib import Path

import math

from build123d import Axis, Box, Cylinder, Pos, chamfer, export_step, export_stl

# ══════════════════════════════════════════════════════════════════════════════
# Free parameters
# ══════════════════════════════════════════════════════════════════════════════

MOUNT_W = 30.0   # mm — X (width)
MOUNT_D = 56.0   # mm — Y (depth)
MOUNT_H = 28.0   # mm — Z (height)

HOLE_FROM_FRONT = 11.5   # mm — bore centre offset from front face (−Y)

CHAMFER         = 5.0    # mm — 5×5 chamfer on the two front vertical edges

# 6800 (61800) deep-groove ball bearing — sourced part
BEARING_OD       = 19.0   # mm — nominal outer diameter
BEARING_W        = 5.0    # mm — width along the bore axis
BEARING_BORE     = 10.0   # mm — inner bore (informational; drives shaft sizing)

# Press fit: housing hole is slightly smaller than bearing OD. 0.05mm is a
# starting point — FDM thermal-shrinkage error dominates this, so print,
# measure, and tune PRESS_INTERFERE in 0.05mm steps until the bearing seats.
PRESS_INTERFERE   = 0.05  # mm — POCKET_OD = BEARING_OD - PRESS_INTERFERE
BEARING_SHOULDER  = 1.0   # mm — radial shoulder the bearing axially seats against

# ══════════════════════════════════════════════════════════════════════════════
# Derived dimensions
# ══════════════════════════════════════════════════════════════════════════════

POCKET_OD    = BEARING_OD - PRESS_INTERFERE       # press-fit OD
POCKET_R     = POCKET_OD / 2
POCKET_DEPTH = BEARING_W                          # bearing seats flush
MID_BORE_OD  = POCKET_OD - 2 * BEARING_SHOULDER   # 16.95mm
MID_BORE_R   = MID_BORE_OD / 2

HOLE_X = 0.0
HOLE_Y = -MOUNT_D / 2 + HOLE_FROM_FRONT     # front face at y = -MOUNT_D/2

# ══════════════════════════════════════════════════════════════════════════════
# Assertions
# ══════════════════════════════════════════════════════════════════════════════

assert POCKET_R < MOUNT_W / 2, (
    f"pocket radius {POCKET_R}mm exceeds half-width {MOUNT_W/2}mm — breaks side faces"
)
assert HOLE_FROM_FRONT >= POCKET_R, (
    f"bore centre {HOLE_FROM_FRONT}mm < pocket radius {POCKET_R}mm — bore breaks front face"
)
assert HOLE_FROM_FRONT + POCKET_R <= MOUNT_D, (
    f"bore extends past back face: {HOLE_FROM_FRONT + POCKET_R}mm > depth {MOUNT_D}mm"
)

# Bearing stack must fit in mount height with material between the pockets
assert 2 * POCKET_DEPTH < MOUNT_H, (
    f"two {POCKET_DEPTH}mm bearing pockets exceed mount height {MOUNT_H}mm"
)
assert MID_BORE_R > BEARING_BORE / 2, (
    f"middle bore ø{MID_BORE_OD}mm too small for bearing inner ø{BEARING_BORE}mm — "
    f"won't clear the bearing inner race"
)
assert BEARING_SHOULDER > 0, "bearing shoulder must be positive"

# Chamfer sanity: must fit on the front edge, and must not bite into the bore.
_CHAMFER_TO_BORE_EDGE = (
    math.sqrt((MOUNT_W/2 - CHAMFER)**2 + HOLE_FROM_FRONT**2) - POCKET_R
)
assert 2 * CHAMFER < MOUNT_W, (
    f"two {CHAMFER}mm chamfers consume {2*CHAMFER}mm of {MOUNT_W}mm front face"
)
assert _CHAMFER_TO_BORE_EDGE > 0, (
    f"chamfer corner reaches {-_CHAMFER_TO_BORE_EDGE:.2f}mm INTO the bearing pocket"
)

OUT = Path(__file__).parent / "out"


def main():
    mount = Box(MOUNT_W, MOUNT_D, MOUNT_H)

    # Middle bore: full-height, smaller diameter (creates a 1mm bearing
    # shoulder at each end). +0.2mm overrun keeps booleans clean.
    mount -= Pos(HOLE_X, HOLE_Y, 0) * Cylinder(MID_BORE_R, MOUNT_H + 0.2)

    # Top bearing pocket: counterbore from the top face down BEARING_W.
    # Centre at z = MOUNT_H/2 - POCKET_DEPTH/2; +0.1mm overrun above the top.
    mount -= Pos(
        HOLE_X, HOLE_Y, MOUNT_H/2 - POCKET_DEPTH/2 + 0.05,
    ) * Cylinder(POCKET_R, POCKET_DEPTH + 0.1)

    # Bottom bearing pocket: counterbore from the bottom face up BEARING_W.
    mount -= Pos(
        HOLE_X, HOLE_Y, -MOUNT_H/2 + POCKET_DEPTH/2 - 0.05,
    ) * Cylinder(POCKET_R, POCKET_DEPTH + 0.1)

    # Chamfer the two front vertical edges (Z-aligned edges at min Y).
    front_vertical_edges = mount.edges().filter_by(Axis.Z).group_by(Axis.Y)[0]
    mount = chamfer(front_vertical_edges, length=CHAMFER)

    OUT.mkdir(exist_ok=True)
    export_step(mount, str(OUT / "mount.step"))
    export_stl(mount, str(OUT / "mount.stl"))

    print(f"Mount: {MOUNT_W} × {MOUNT_D} × {MOUNT_H} mm")
    print(f"Bore at (x={HOLE_X}, y={HOLE_Y}) — {HOLE_FROM_FRONT}mm from front face")
    print(f"  Bearing pockets: ø{POCKET_OD:.2f}mm × {POCKET_DEPTH}mm deep "
          f"(press fit: {PRESS_INTERFERE}mm interference vs nominal ø{BEARING_OD})")
    print(f"  Middle bore:     ø{MID_BORE_OD:.2f}mm  ({BEARING_SHOULDER}mm "
          f"radial shoulder per bearing)")
    print(f"  Bearing: 6800 (61800), 2× — ø{BEARING_OD}×{BEARING_W}, bore ø{BEARING_BORE}")
    print(f"Front chamfer: {CHAMFER}×{CHAMFER}mm — clears pocket by "
          f"{_CHAMFER_TO_BORE_EDGE:.2f}mm")
    print(f"Exported: mount.step, mount.stl in {OUT}")


if __name__ == "__main__":
    main()
