# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
#     "bd_warehouse",
# ]
# ///
"""Purfling cutter — v0.4: plate + shoe + two-part bearing sleeve + washer.

Four printed parts (standoffs replaced by M6 flat-head bolts):
- **plate**: 3/4"-12 UN threaded Dremel mount. Two M6 × 8 OD × 10 mm heat-set
  inserts in the bottom face accept the M6 bolts that rise from the shoe.
  No longitudinal slot (channel removed).
- **shoe**: pill-shaped body, z=0–SHOE_T. Front (surround) region is a
  half-stadium snout. Two M6 flat-head bolt holes with countersinks on the
  shoe bottom accept the bolts; heads sit flush at z=0.
- **upper_sleeve / lower_sleeve + washer**: two-part bearing housing as v0.3.

Coordinates
-----------
Shoe-local frame is the world frame for the assembly.
  +X : long axis of the shoe (surround at +X end, standoffs at -X end).
  +Y : short axis (width).
  +Z : up. z = 0 is the bottom of the shoe (sits on workpiece top).
"""

from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    BuildSketch,
    Cone,
    Cylinder,
    GeomType,
    Pos,
    RegularPolygon,
    SlotOverall,
    chamfer,
    export_step,
    export_stl,
    extrude,
    fillet,
)
from bd_warehouse.thread import IsoThread

# ---- plate ---- #
PLATE_W = 30
PLATE_T = 11                     # 5.2 mm nut pocket + 5.8 mm solid below

# Dremel 3/4"-12 UN
THREAD_MAJOR = 19.05
THREAD_PITCH = 25.4 / 12
# PLATE_L and THREAD_X are derived after shoe constants below.

# M6 captive nut pockets in plate top face.
M6_NUT_AF = 10.0                 # M6 hex nut across-flats (ISO 4032)
M6_NUT_T = 5.0                   # M6 hex nut thickness
M6_NUT_POCKET_AF = 10.2          # pocket AF (0.1 mm clearance per flat)
M6_NUT_POCKET_T = 5.2            # pocket depth (0.2 mm clearance on thickness)

# ---- 608 bearing (shared) ---- #
BEARING_OD = 22.0
BEARING_THK = 7.0
# Inner race OD ≈ 12, outer race ID ≈ 16. Step/flange Ø sits between.

# ---- M6 standoff bolts (flat-head, rise from shoe into plate inserts) ---- #
M6_BOLT_CLEARANCE_D = 6.5       # bolt shank clearance through shoe and plate

# Flat-head countersink in shoe bottom face.
COUNTERSINK_D = 12.0             # head OD; M6 flat-head is typically Ø12
COUNTERSINK_DEPTH = 4.0          # head height; flush with shoe bottom (z=0)

# ---- shoe ---- #
SHOE_W = 30                      # Y, matches PLATE_W
SHOE_T = 11                      # Z thickness

# Surround snout (half-stadium): flat back, Ø SURROUND_BOSS_D semicircular front.
SURROUND_HEIGHT = 4              # Z height of snout (z=0 to z=4)
SURROUND_WALL = 4                # radial material around bit hole
BIT_HOLE_D = 6                   # router bit clearance
SURROUND_BOSS_D = BIT_HOLE_D + 2 * SURROUND_WALL  # = 16
SURROUND_LEN = 14                # X extent of the surround region
SURROUND_OVERLAP = 2             # snout rect extends back into shoe body by this much so the union is a solid weld (prints as one object)
SURROUND_FILLET_OUT = 3.4        # bottom outer perimeter of snout (hard limit: SURROUND_WALL − bit_r − inner_fillet ≈ 3.5)
SURROUND_FILLET_IN = 0.5         # bit hole bottom edge

# Bearing channel
SLOT_LEN = 18                    # gives bearing-edge-to-bit-edge gap of 1.25–13.25 mm; cantilever = 19.25 + SLOT_LEN
SLOT_W = 6.5                     # clears UPPER_STEM1_D=6 + ~0.25/side

# Walls — SLOT_END_WALL and END_WALL_BACK sized so Ø12 countersinks clear the
# slot (≥3.25 mm gap) and stay inside the shoe end (≥4 mm margin).
END_WALL_FRONT = 3               # surround edge → slot edge
SLOT_END_WALL = 6                # slot edge → standoff bolt near edge (was 3)
END_WALL_BACK = 10               # outer bolt center → back of shoe (was 6)

# Standoff bolt holes (M6 clearance + countersink on shoe bottom)
STANDOFF_BOLT_D = M6_BOLT_CLEARANCE_D  # = 6.5
STANDOFF_SPAN = 20               # bolt-center to bolt-center

# Derived shoe length and feature X positions (shoe centered at X=0).
SHOE_L = (
    SURROUND_LEN
    + END_WALL_FRONT
    + SLOT_LEN
    + SLOT_END_WALL
    + STANDOFF_BOLT_D / 2
    + STANDOFF_SPAN
    + END_WALL_BACK
)
SURROUND_X = SHOE_L / 2 - SURROUND_LEN / 2
SLOT_X_CENTER = (
    SURROUND_X - SURROUND_LEN / 2 - END_WALL_FRONT - SLOT_LEN / 2
)
STANDOFF_X_INNER = (
    SLOT_X_CENTER - SLOT_LEN / 2 - SLOT_END_WALL - STANDOFF_BOLT_D / 2
)
STANDOFF_X_OUTER = STANDOFF_X_INNER - STANDOFF_SPAN

# Plate length: just long enough to span from thread bore (+X semicircle) to
# past the outer insert with ≥6 mm wall from hole edge.
PLATE_BACK_WALL = 10             # outer insert centre → plate back edge (≈6 mm from hole edge)
PLATE_L = SURROUND_X - STANDOFF_X_OUTER + PLATE_W / 2 + PLATE_BACK_WALL
THREAD_X = PLATE_L / 2 - PLATE_W / 2  # bore centre on the +X semicircle

# ---- bearing housing ---- #
M4_BOLT_CLEARANCE_D = 4.5

M4_NUT_AF = 7.0
M4_NUT_T = 3.2
M4_NUT_POCKET_AF = 7.2
M4_NUT_POCKET_T = 3.5

UPPER_STEM1_D = 6
UPPER_STEM1_LEN = 9              # X extent of stadium stem; flat sides prevent rotation in slot
UPPER_STEM1_OFFSET = (UPPER_STEM1_LEN - UPPER_STEM1_D) / 2  # stadium shifted -X so hole sits at +X cap centre
UPPER_TOP_FLANGE_D = 13
UPPER_TOP_FLANGE_T = 5

LOWER_FLANGE_D = 14
LOWER_FLANGE_T = 1.5
LOWER_STEM_D = 7.8
LOWER_STEM_L = BEARING_THK       # = 7.0

WASHER_OD = 14
WASHER_T = 1.5

# ---- standoff ---- #
STANDOFF_H = 23                  # plate-to-shoe gap (shoe top → plate bottom)
STANDOFF_CLEARANCE = 2           # total margin kept from both hard limits (1 mm each end)
# Most-negative bearing X: inner stem left cap aligns with outer slot left cap.
BEARING_X_MIN = (
    SLOT_X_CENTER
    - (SLOT_LEN - SLOT_W - (UPPER_STEM1_LEN - UPPER_STEM1_D)) / 2
    + UPPER_STEM1_OFFSET
)
# Width is the smaller of: (a) flush with shoe back wall, (b) clear of upper sleeve flange
# at maximum bearing-to-bit distance (bearing at −X slot limit).
STANDOFF_W = min(
    2 * (SHOE_L / 2 + STANDOFF_X_OUTER),                                  # shoe-end limit
    2 * (BEARING_X_MIN - UPPER_TOP_FLANGE_D / 2 - STANDOFF_X_INNER),     # flange limit at max bearing dist
) - STANDOFF_CLEARANCE           # = 14 mm; wall ≈ 3.5 mm each side
STANDOFF_HOLE_D = M6_BOLT_CLEARANCE_D + 0.5             # extra clearance for standoff bolt passage

OUT = Path(__file__).parent / "out"
STL_OUT = Path(__file__).parent / "stl"


def build_plate():
    # Insert positions are derived so they align with the shoe standoff holes.
    # The plate's THREAD_X sits over the shoe's SURROUND_X (bit hole).
    plate_shoe_offset = SURROUND_X - THREAD_X
    insert_x_inner = STANDOFF_X_INNER - plate_shoe_offset
    insert_x_outer = STANDOFF_X_OUTER - plate_shoe_offset

    with BuildSketch() as sk:
        SlotOverall(PLATE_L, PLATE_W)
    plate = extrude(sk.sketch, amount=PLATE_T)

    # Dremel bore + thread.
    plate -= Pos(THREAD_X, 0, -0.1) * Cylinder(
        radius=THREAD_MAJOR / 2,
        height=PLATE_T + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    thread = IsoThread(
        major_diameter=THREAD_MAJOR,
        pitch=THREAD_PITCH,
        length=PLATE_T,
        external=False,
        end_finishes=("chamfer", "chamfer"),
    )
    plate += Pos(THREAD_X, 0, 0) * thread

    # M6 captive nut pockets — bolt clearance bore through plate, hex pocket from top.
    with BuildSketch() as nut_sk:
        RegularPolygon(radius=M6_NUT_POCKET_AF / math.sqrt(3), side_count=6)
    m6_nut_pocket = extrude(nut_sk.sketch, amount=M6_NUT_POCKET_T).solids()[0]
    for x in (insert_x_inner, insert_x_outer):
        plate -= Pos(x, 0, -0.1) * Cylinder(
            radius=M6_BOLT_CLEARANCE_D / 2,
            height=PLATE_T + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        plate -= Pos(x, 0, PLATE_T - M6_NUT_POCKET_T) * m6_nut_pocket

    return plate


def build_shoe():
    with BuildSketch() as sk:
        SlotOverall(SHOE_L, SHOE_W)
    shoe = extrude(sk.sketch, amount=SHOE_T)

    # Surround: cut the front region away, add back a half-stadium snout.
    surround_x_start = SURROUND_X - SURROUND_LEN / 2
    shoe -= Pos(surround_x_start - 0.1, 0, -0.1) * Box(
        SURROUND_LEN + SHOE_W / 2 + 0.2,
        SHOE_W + 2,
        SHOE_T + 0.2,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    # Snout rect spans from (surround_x_start - SURROUND_OVERLAP) to SURROUND_X
    # so it pushes back into the remaining body and unions solidly, instead of
    # leaving the 0.1 mm gap from the cut tolerance.
    snout_rect_l = SURROUND_LEN / 2 + SURROUND_OVERLAP
    shoe += Pos(surround_x_start - SURROUND_OVERLAP, 0, 0) * Box(
        snout_rect_l, SURROUND_BOSS_D, SURROUND_HEIGHT,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    shoe += Pos(SURROUND_X, 0, 0) * Cylinder(
        radius=SURROUND_BOSS_D / 2, height=SURROUND_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shoe -= Pos(SURROUND_X, 0, -0.1) * Cylinder(
        radius=BIT_HOLE_D / 2,
        height=SURROUND_HEIGHT + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Fillet the outer bottom perimeter of the snout at z=0.
    # Keep z=0 edges in the snout region (x > surround_x_start), skip the
    # bit hole and the rect back edge that meets the main shoe body.
    outer_bottom = []
    for e in shoe.edges():
        c = e.center()
        if abs(c.Z) > 0.01:
            continue
        if c.X <= surround_x_start + 0.5:
            continue
        if e.geom_type == GeomType.CIRCLE and e.radius < SURROUND_BOSS_D / 2 - 0.5:
            continue
        outer_bottom.append(e)
    shoe = fillet(outer_bottom, radius=SURROUND_FILLET_OUT)

    # Fillet the bit hole bottom edge (z=0 circle of radius BIT_HOLE_D/2).
    bit_hole_bottom = [
        e for e in shoe.edges()
        if abs(e.center().Z) < 0.01
        and e.geom_type == GeomType.CIRCLE
        and abs(e.radius - BIT_HOLE_D / 2) < 0.1
    ]
    shoe = fillet(bit_hole_bottom, radius=SURROUND_FILLET_IN)

    # Bearing channel.
    with BuildSketch() as slot_sk:
        SlotOverall(SLOT_LEN, SLOT_W)
    slot_cut = extrude(slot_sk.sketch, amount=SHOE_T + 0.2)
    shoe -= Pos(SLOT_X_CENTER, 0, -0.1) * slot_cut

    # Standoff bolt holes: flat-head countersink from shoe bottom + clearance bore.
    # Countersink: Ø COUNTERSINK_D at z=0 tapering to M6 clearance at z=COUNTERSINK_DEPTH.
    for x in (STANDOFF_X_INNER, STANDOFF_X_OUTER):
        shoe -= Pos(x, 0, -0.1) * Cone(
            bottom_radius=COUNTERSINK_D / 2,
            top_radius=STANDOFF_BOLT_D / 2,
            height=COUNTERSINK_DEPTH + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        shoe -= Pos(x, 0, COUNTERSINK_DEPTH - 0.1) * Cylinder(
            radius=STANDOFF_BOLT_D / 2,
            height=SHOE_T - COUNTERSINK_DEPTH + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    return shoe


def build_upper_sleeve():
    with BuildSketch() as stem_sk:
        SlotOverall(UPPER_STEM1_LEN, UPPER_STEM1_D)
    # Shift stadium toward -X so its +X edge aligns with the original circle's +X edge.
    # Extra material goes toward the bolt side; bit-side extent is unchanged.
    body = Pos(-UPPER_STEM1_OFFSET, 0, 0) * extrude(stem_sk.sketch, amount=SHOE_T)
    body += Pos(0, 0, SHOE_T) * Cylinder(
        radius=UPPER_TOP_FLANGE_D / 2, height=UPPER_TOP_FLANGE_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    flange_top = SHOE_T + UPPER_TOP_FLANGE_T
    body -= Pos(0, 0, -0.1) * Cylinder(
        radius=M4_BOLT_CLEARANCE_D / 2, height=flange_top + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    with BuildSketch() as nut_sk:
        RegularPolygon(
            radius=M4_NUT_POCKET_AF / math.sqrt(3), side_count=6,
        )
    nut_pocket = extrude(nut_sk.sketch, amount=M4_NUT_POCKET_T).solids()[0]
    body -= Pos(0, 0, flange_top - M4_NUT_POCKET_T) * nut_pocket
    return body


def build_lower_sleeve():
    body = Cylinder(
        radius=LOWER_FLANGE_D / 2, height=LOWER_FLANGE_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body += Pos(0, 0, LOWER_FLANGE_T) * Cylinder(
        radius=LOWER_STEM_D / 2, height=LOWER_STEM_L,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    total_h = LOWER_FLANGE_T + LOWER_STEM_L
    body -= Pos(0, 0, -0.1) * Cylinder(
        radius=M4_BOLT_CLEARANCE_D / 2, height=total_h + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body


def build_washer():
    body = Cylinder(
        radius=WASHER_OD / 2, height=WASHER_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body -= Pos(0, 0, -0.1) * Cylinder(
        radius=M4_BOLT_CLEARANCE_D / 2, height=WASHER_T + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body


def build_standoff():
    with BuildSketch() as sk:
        SlotOverall(STANDOFF_SPAN + STANDOFF_W, STANDOFF_W)
    body = extrude(sk.sketch, amount=STANDOFF_H)
    for x_off in (STANDOFF_SPAN / 2, -STANDOFF_SPAN / 2):
        body -= Pos(x_off, 0, -0.1) * Cylinder(
            radius=STANDOFF_HOLE_D / 2,
            height=STANDOFF_H + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    return body


def main() -> None:
    OUT.mkdir(exist_ok=True)
    STL_OUT.mkdir(exist_ok=True)
    plate = build_plate()
    shoe = build_shoe()
    upper_sleeve = build_upper_sleeve()
    lower_sleeve = build_lower_sleeve()
    washer = build_washer()
    standoff = build_standoff()

    export_step(plate, str(OUT / "plate.step"))
    export_stl(plate, str(OUT / "plate.stl"))
    export_step(shoe, str(OUT / "shoe.step"))
    export_stl(shoe, str(OUT / "shoe.stl"))
    export_step(upper_sleeve, str(OUT / "upper_sleeve.step"))
    export_stl(upper_sleeve, str(OUT / "upper_sleeve.stl"))
    export_step(lower_sleeve, str(OUT / "lower_sleeve.step"))
    export_stl(lower_sleeve, str(OUT / "lower_sleeve.stl"))
    export_step(washer, str(OUT / "washer.step"))
    export_stl(washer, str(OUT / "washer.stl"))
    export_step(standoff, str(OUT / "standoff.step"))
    export_stl(standoff, str(OUT / "standoff.stl"))

    for part, name in [
        (plate, "plate"), (shoe, "shoe"), (upper_sleeve, "upper_sleeve"),
        (lower_sleeve, "lower_sleeve"), (washer, "washer"), (standoff, "standoff"),
    ]:
        export_stl(part, str(STL_OUT / f"{name}.stl"))

    print(f"Exported: {sorted(p.name for p in OUT.iterdir())}")

    # ---- assembly preview ---- #
    bearing_x = SLOT_X_CENTER
    upper_assembled = Pos(bearing_x, 0, 0) * upper_sleeve
    washer_z_base = -WASHER_T
    washer_assembled = Pos(bearing_x, 0, washer_z_base) * washer
    bearing_top_z = -WASHER_T
    bearing_bottom_z = bearing_top_z - BEARING_THK
    bearing_ghost = Cylinder(
        radius=BEARING_OD / 2, height=BEARING_THK,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ) - Cylinder(
        radius=LOWER_STEM_D / 2 + 0.05, height=BEARING_THK + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    bearing_ghost = Pos(bearing_x, 0, bearing_bottom_z) * bearing_ghost
    lower_z_base = bearing_bottom_z - LOWER_FLANGE_T
    lower_assembled = Pos(bearing_x, 0, lower_z_base) * lower_sleeve
    plate_shoe_offset = SURROUND_X - THREAD_X
    plate_assembled = Pos(plate_shoe_offset, 0, SHOE_T + STANDOFF_H) * plate
    standoff_x = (STANDOFF_X_INNER + STANDOFF_X_OUTER) / 2
    standoff_assembled = Pos(standoff_x, 0, SHOE_T) * standoff

    try:
        from ocp_vscode import show
        show(
            plate_assembled, shoe, upper_assembled, lower_assembled,
            washer_assembled, bearing_ghost, standoff_assembled,
            names=["plate", "shoe", "upper_sleeve", "lower_sleeve",
                   "washer", "bearing", "standoff"],
        )
        print("Sent to OCP CAD Viewer.")
    except ImportError:
        print("ocp_vscode not installed; skipping viewer.")
    except Exception as exc:
        print(f"Viewer unavailable (is the VS Code extension running?): {exc}")


if __name__ == "__main__":
    main()
