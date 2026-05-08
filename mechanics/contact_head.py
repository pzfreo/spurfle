# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
# ]
# ///
"""Roller assembly for the three-roller contact head.

One roller + two holder plates (lower fixed, upper removable cap).
The 1.5mm steel axle is captive between blind pockets in both plates —
no through-hole, no fasteners required.

Run:
    uv run python mechanics/contact_head.py

Exports to mechanics/out/: roller, lower_plate, upper_plate  (.step + .stl)
"""

from pathlib import Path
from build123d import (
    Align,
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
ROLLER_OD     = 7.0          # mm — nylon FDM; contacts instrument edge
ROLLER_R      = ROLLER_OD / 2
ROLLER_H      = 10.0         # mm — axial height; spans violin 3mm overhang with margin
PIN_D         = 1.5          # mm — steel axle (piano wire or equivalent)
PIN_BORE      = PIN_D + 0.2  # mm — 1.7mm running fit in roller and holder pockets
HOLDER_OD     = 4.5          # mm — stadium OD at pin end (C-011)
HOLDER_R      = HOLDER_OD / 2
HOLDER_EXTEND = 10.0         # mm — body length beyond pin centre (TBD: see issue #11)
HOLDER_T      = 3.5          # mm — plate thickness; mid of 3–4mm range (C-012)
POCKET_DEPTH  = 2.0          # mm — blind bore depth in each plate; axle captive by geometry

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

# ─── Derived ──────────────────────────────────────────────────────────────────
LOWER_Z  = -(ROLLER_H / 2 + HOLDER_T)
UPPER_Z  =   ROLLER_H / 2
AXLE_L   = 2 * POCKET_DEPTH + ROLLER_H   # 14mm — fully captive between both pockets
AXLE_Z   = -(ROLLER_H / 2 + POCKET_DEPTH)

OUT = Path(__file__).parent / "out"

ROLLER_GAP  = HOLDER_EXTEND / 2 - ROLLER_OD  # sanity — HOLDER_EXTEND drives inter-roller gap
# (Full C-005 gap assertion lives in plan_view.py which has the full three-roller geometry)


def build_roller():
    """Nylon roller — cylindrical with running-fit axle bore."""
    body = Cylinder(ROLLER_R, ROLLER_H)
    body -= Cylinder(PIN_BORE / 2, ROLLER_H + 0.2)
    return body


def _plate_body():
    """Stadium-shaped holder plate body, no bore yet.

    Pin-end semicircle centre at X=0; body extends in +X to X=HOLDER_EXTEND.
    """
    slot_l = HOLDER_EXTEND + HOLDER_OD  # 14.5mm tip-to-tip
    with BuildSketch() as sk:
        with Locations((HOLDER_EXTEND / 2, 0)):
            SlotOverall(slot_l, HOLDER_OD)
    return extrude(sk.sketch, HOLDER_T)


def build_lower_plate():
    """Lower holder plate — blind axle bore from inner (top) face.

    Outer (bottom) face is solid — no fasteners, no holes.
    Bore opens at Z=HOLDER_T (inner face), blind at Z=HOLDER_T-POCKET_DEPTH.
    """
    plate = _plate_body()
    plate -= Pos(0, 0, HOLDER_T - POCKET_DEPTH) * Cylinder(
        PIN_BORE / 2, POCKET_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return plate


def build_upper_plate():
    """Upper holder plate — blind axle bore from inner (bottom) face.

    Outer (top) face is solid. Plate is a removable cap; attachment to the
    holder body is TBD pending overall housing design.
    """
    plate = _plate_body()
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


if __name__ == "__main__":
    main()
