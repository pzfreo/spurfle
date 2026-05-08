# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
# ]
# ///
"""Roller assembly for the three-roller contact head.

One roller + two holder plates:
- Lower plate: L-shaped bracket — extended horizontal base + vertical wall
  rising behind the roller to support the upper plate.
- Upper plate: shorter removable cap; rests on the lower plate's vertical wall
  at its far end; attachment method TBD pending overall housing design.
- Axle: 1.5mm steel, captive between blind pockets in both plates (no
  through-hole, no fasteners required).

Run:
    uv run python mechanics/contact_head.py

Exports to mechanics/out/: roller, lower_plate, upper_plate  (.step + .stl)
"""

from pathlib import Path
from build123d import (
    Align,
    Box,
    BuildSketch,
    Cylinder,
    Locations,
    Pos,
    SlotOverall,
    export_step,
    export_stl,
    extrude,
)

# ─── Parameters (from mechanics/SPEC.md) ──────────────────────────────────────
ROLLER_OD      = 7.0          # mm — nylon FDM; contacts instrument edge
ROLLER_R       = ROLLER_OD / 2
ROLLER_H       = 10.0         # mm — axial height; spans violin 3mm overhang with margin
PIN_D          = 1.5          # mm — steel axle (piano wire or equivalent)
PIN_BORE       = PIN_D + 0.2  # mm — 1.7mm running fit in roller and holder pockets
HOLDER_OD      = 4.5          # mm — stadium OD at pin end (C-011)
HOLDER_R       = HOLDER_OD / 2
LOWER_EXTEND   = 20.0         # mm — lower plate body length beyond pin centre
UPPER_EXTEND   = 10.0         # mm — upper plate body length beyond pin centre (TBD: issue #11)
HOLDER_T       = 3.5          # mm — plate thickness; mid of 3–4mm range (C-012)
POCKET_DEPTH           = 2.0   # mm — blind bore depth; axle captive by geometry
ROLLER_AXIAL_CLEARANCE = 0.2   # mm — total axial play (0.1mm each end); roller spins freely
ROLLER_H_PRINT         = ROLLER_H - ROLLER_AXIAL_CLEARANCE  # 9.8mm printed height

# Vertical wall: rises from lower plate behind the roller to support upper plate
WALL_CLEARANCE = 0.5          # mm — gap between wall inner face and roller surface
WALL_START_X   = ROLLER_R + WALL_CLEARANCE   # 4.0mm from pin centre

# ─── Assertions ───────────────────────────────────────────────────────────────
assert HOLDER_OD < ROLLER_OD, (
    f"C-011: holder OD {HOLDER_OD}mm overhangs roller {ROLLER_OD}mm — holder will contact work"
)
assert HOLDER_OD >= PIN_D + 2 * 1.2, (
    f"C-011: holder wall {(HOLDER_OD - PIN_D)/2:.2f}mm too thin — FDM minimum 1.2mm"
)
assert POCKET_DEPTH < HOLDER_T, (
    f"Blind pocket {POCKET_DEPTH}mm deep breaks through {HOLDER_T}mm plate"
)
assert ROLLER_H >= 3.0, (
    f"Roller height {ROLLER_H}mm must clear violin plate overhang (3mm minimum)"
)
assert ROLLER_AXIAL_CLEARANCE > 0, "Roller needs axial clearance to spin"
assert ROLLER_AXIAL_CLEARANCE < POCKET_DEPTH, "Clearance must not exceed pocket depth"
assert WALL_START_X > ROLLER_R, (
    "Vertical wall inner face intersects roller"
)

# ─── Derived ──────────────────────────────────────────────────────────────────
LOWER_Z = -(ROLLER_H / 2 + HOLDER_T)   # −8.5 mm
UPPER_Z =   ROLLER_H / 2               # +5.0 mm
AXLE_L  = 2 * POCKET_DEPTH + ROLLER_H  # 14 mm — fully captive
AXLE_Z  = -(ROLLER_H / 2 + POCKET_DEPTH)  # −7.0 mm

OUT = Path(__file__).parent / "out"


def build_roller():
    """Nylon roller — cylindrical with running-fit axle bore.

    Printed height is ROLLER_H_PRINT (9.8mm), 0.1mm shorter than the plate
    gap each end so the roller spins freely without being clamped.
    Centered at Z=0 in the assembly.
    """
    body = Cylinder(ROLLER_R, ROLLER_H_PRINT)
    body -= Cylinder(PIN_BORE / 2, ROLLER_H_PRINT + 0.2)
    return body


def build_lower_plate():
    """Lower holder plate — L-shaped bracket.

    Horizontal base: extended stadium (LOWER_EXTEND body length), blind axle
    bore from inner (top) face.

    Vertical wall: rises from top of horizontal base, starting WALL_CLEARANCE
    beyond the roller surface, extending to the far end. Top face of wall is
    flush with UPPER_Z (bottom of upper plate), providing direct support.
    """
    # ── Horizontal base ───────────────────────────────────────────────────────
    lower_slot_l = LOWER_EXTEND + HOLDER_OD
    with BuildSketch() as sk:
        with Locations((LOWER_EXTEND / 2, 0)):
            SlotOverall(lower_slot_l, HOLDER_OD)
    horiz = extrude(sk.sketch, HOLDER_T)

    # Blind axle bore from inner (top) face
    horiz -= Pos(0, 0, HOLDER_T - POCKET_DEPTH) * Cylinder(
        PIN_BORE / 2, POCKET_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # ── Vertical wall ─────────────────────────────────────────────────────────
    wall_h = ROLLER_H  # fills the gap between plates exactly

    # Straight body section
    wall_box = Pos(WALL_START_X, 0, HOLDER_T) * Box(
        LOWER_EXTEND - WALL_START_X,
        HOLDER_OD,
        wall_h,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )

    # Far-end semicircular cap (matches end of horizontal base)
    wall_cap = Pos(LOWER_EXTEND, 0, HOLDER_T) * Cylinder(
        HOLDER_R, wall_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    return horiz + wall_box + wall_cap


def build_upper_plate():
    """Upper holder plate — short removable cap.

    Blind axle bore from inner (bottom) face. Far end rests on the lower
    plate's vertical wall. Attachment method TBD pending housing design.
    """
    upper_slot_l = UPPER_EXTEND + HOLDER_OD
    with BuildSketch() as sk:
        with Locations((UPPER_EXTEND / 2, 0)):
            SlotOverall(upper_slot_l, HOLDER_OD)
    plate = extrude(sk.sketch, HOLDER_T)
    plate -= Pos(0, 0, -0.1) * Cylinder(
        PIN_BORE / 2, POCKET_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return plate


def main():
    OUT.mkdir(exist_ok=True)

    roller      = build_roller()
    lower_plate = Pos(0, 0, LOWER_Z) * build_lower_plate()
    upper_plate = Pos(0, 0, UPPER_Z) * build_upper_plate()

    for part, name in [
        (roller,      "roller"),
        (lower_plate, "lower_plate"),
        (upper_plate, "upper_plate"),
    ]:
        export_step(part, str(OUT / f"{name}.step"))
        export_stl(part,  str(OUT / f"{name}.stl"))

    print(f"Exported: {sorted(p.name for p in OUT.iterdir())}")
    print(f"Axle (not exported — sourced): ⌀{PIN_D}mm × {AXLE_L}mm steel")
    print(f"Roller protrusion beyond holder: {(ROLLER_OD - HOLDER_OD)/2:.2f}mm each side")
    print(f"Vertical wall: X={WALL_START_X}→{LOWER_EXTEND+HOLDER_R:.1f}mm, "
          f"clearance from roller={WALL_CLEARANCE}mm")


if __name__ == "__main__":
    main()
