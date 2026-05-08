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
Assertions enforce all numbered constraints — a clean run means all pass.
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

# ══════════════════════════════════════════════════════════════════════════════
# Named engineering limits
# These are fixed by material/process choice, not adjustable per design.
# Change only when switching process or material.
# ══════════════════════════════════════════════════════════════════════════════

FDM_WALL_MIN          = 1.2   # mm — absolute FDM minimum structural wall (any material)
FDM_WALL_PREF         = 1.5   # mm — preferred minimum for load-bearing FDM walls (ASA)
BORE_FIT              = 0.2   # mm — running fit clearance (bore = shaft_OD + BORE_FIT)
ROLLER_TO_WALL_MIN    = 1.0   # mm — minimum radial gap, roller OD to any holder face (C-014)
POCKET_MIN_ENGAGEMENT = 1.5   # mm — minimum blind pocket depth for shock retention (C-013)
ROLLER_H_MIN          = 3.0   # mm — roller must clear violin plate overhang (3mm edge)
HOLDER_T_MIN          = 3.0   # mm — plate minimum for bearing loads under shock (C-012)

# ══════════════════════════════════════════════════════════════════════════════
# Free parameters — adjust these to change the design
# ══════════════════════════════════════════════════════════════════════════════

ROLLER_OD              = 7.0   # mm — nylon FDM; contacts instrument edge
ROLLER_H               = 10.0  # mm — nominal plate-to-plate gap (roller printed shorter)
PIN_D                  = 1.5   # mm — steel axle diameter
HOLDER_OD              = 4.5   # mm — holder stadium OD at pin bore end (C-011)
LOWER_EXTEND           = 20.0  # mm — lower plate body length beyond pin centre
UPPER_EXTEND           = 10.0  # mm — upper plate body length beyond pin centre
HOLDER_T               = 3.5   # mm — plate thickness (C-012: min 3mm)
POCKET_DEPTH           = 2.0   # mm — blind bore depth each plate (C-013)
ROLLER_TO_WALL_GAP     = 1.0   # mm — radial gap, roller OD to vertical wall (C-014)
ROLLER_AXIAL_CLEARANCE = 0.2   # mm — total axial play; 0.1mm each end

# ══════════════════════════════════════════════════════════════════════════════
# Derived dimensions — calculated, never typed
# ══════════════════════════════════════════════════════════════════════════════

ROLLER_R       = ROLLER_OD / 2
HOLDER_R       = HOLDER_OD / 2
PIN_BORE       = PIN_D + BORE_FIT          # 1.7 mm running fit
ROLLER_H_PRINT = ROLLER_H - ROLLER_AXIAL_CLEARANCE   # 9.8 mm actual printed height
WALL_START_X   = ROLLER_R + ROLLER_TO_WALL_GAP       # 4.5 mm from pin centre
LOWER_Z        = -(ROLLER_H / 2 + HOLDER_T)
UPPER_Z        =   ROLLER_H / 2
AXLE_L         = 2 * POCKET_DEPTH + ROLLER_H         # 14 mm — spans both pockets
AXLE_Z         = -(ROLLER_H / 2 + POCKET_DEPTH)

# ══════════════════════════════════════════════════════════════════════════════
# Intermediate values for assertions (not used in geometry)
# ══════════════════════════════════════════════════════════════════════════════

ROLLER_WALL           = (ROLLER_OD - PIN_BORE) / 2    # nylon wall around axle bore
HOLDER_WALL           = (HOLDER_OD - PIN_D) / 2       # ASA wall at pin bore (C-011)
ROLLER_PROTRUSION     = (ROLLER_OD - HOLDER_OD) / 2   # roller beyond holder each side
OUTER_FACE_WALL       = HOLDER_T - POCKET_DEPTH        # solid ASA behind blind pocket (C-013)
AXLE_RADIAL_CLEARANCE = (PIN_BORE - PIN_D) / 2        # = BORE_FIT / 2

# ══════════════════════════════════════════════════════════════════════════════
# Assertions — running this file IS the test suite
# ══════════════════════════════════════════════════════════════════════════════

# C-011: holder geometry — must not contact work, wall must survive FDM printing
assert HOLDER_OD < ROLLER_OD, (
    f"C-011: holder OD {HOLDER_OD}mm ≥ roller OD {ROLLER_OD}mm — "
    f"holder contacts work before roller"
)
assert ROLLER_PROTRUSION > 0, (
    f"C-011: roller protrusion {ROLLER_PROTRUSION:.2f}mm ≤ 0 — "
    f"holder OD must be strictly less than roller OD"
)
assert HOLDER_WALL >= FDM_WALL_PREF, (
    f"C-011: holder wall {HOLDER_WALL:.2f}mm < preferred FDM minimum {FDM_WALL_PREF}mm "
    f"— wall around pin bore will fail under lateral load"
)

# C-012: plate thickness for bearing loads
assert HOLDER_T >= HOLDER_T_MIN, (
    f"C-012: holder plate {HOLDER_T}mm < {HOLDER_T_MIN}mm — "
    f"insufficient bearing depth for shock loads (see constraint analysis)"
)

# C-013: axle retention via blind pockets
assert POCKET_DEPTH >= POCKET_MIN_ENGAGEMENT, (
    f"C-013: pocket depth {POCKET_DEPTH}mm < {POCKET_MIN_ENGAGEMENT}mm minimum — "
    f"axle engagement too short to resist shock extraction"
)
assert POCKET_DEPTH < HOLDER_T, (
    f"C-013: pocket depth {POCKET_DEPTH}mm ≥ plate thickness {HOLDER_T}mm — "
    f"bore exits the outer face, defeating retention"
)
assert OUTER_FACE_WALL >= FDM_WALL_MIN, (
    f"C-013: outer face wall {OUTER_FACE_WALL:.2f}mm < FDM minimum {FDM_WALL_MIN}mm — "
    f"plate will fracture behind pocket under load"
)

# C-014: radial clearance between roller OD and any holder face
assert ROLLER_TO_WALL_GAP >= ROLLER_TO_WALL_MIN, (
    f"C-014: roller-to-wall gap {ROLLER_TO_WALL_GAP}mm < {ROLLER_TO_WALL_MIN}mm minimum — "
    f"roller will foul holder under FDM tolerances"
)

# Roller FDM manufacturability
assert ROLLER_WALL >= FDM_WALL_MIN, (
    f"Roller wall {ROLLER_WALL:.2f}mm < FDM minimum {FDM_WALL_MIN}mm — "
    f"pin bore too large for roller OD, wall will fail"
)
assert ROLLER_H >= ROLLER_H_MIN, (
    f"Roller height {ROLLER_H}mm < {ROLLER_H_MIN}mm — "
    f"roller won't span violin plate overhang (minimum 3mm edge height)"
)
assert ROLLER_H_PRINT > 0, (
    f"ROLLER_AXIAL_CLEARANCE {ROLLER_AXIAL_CLEARANCE}mm ≥ ROLLER_H {ROLLER_H}mm — "
    f"printed roller has zero or negative height"
)

# Assembly fit
assert AXLE_RADIAL_CLEARANCE > 0, (
    f"Axle bore {PIN_BORE}mm ≤ axle OD {PIN_D}mm — axle won't fit in bore"
)
assert ROLLER_AXIAL_CLEARANCE > 0, (
    f"ROLLER_AXIAL_CLEARANCE = 0 — "
    f"roller will be clamped between plates and won't spin"
)
assert ROLLER_AXIAL_CLEARANCE < POCKET_DEPTH, (
    f"ROLLER_AXIAL_CLEARANCE {ROLLER_AXIAL_CLEARANCE}mm ≥ POCKET_DEPTH {POCKET_DEPTH}mm — "
    f"axle protrudes far enough to allow extraction"
)

OUT = Path(__file__).parent / "out"


# ══════════════════════════════════════════════════════════════════════════════
# Geometry
# ══════════════════════════════════════════════════════════════════════════════

def build_roller():
    """Nylon roller — cylindrical with running-fit axle bore.

    Printed height ROLLER_H_PRINT is shorter than plate gap by
    ROLLER_AXIAL_CLEARANCE (0.1mm each end), so the roller spins freely.
    Centered at Z=0 in the assembly.
    """
    body = Cylinder(ROLLER_R, ROLLER_H_PRINT)
    body -= Cylinder(PIN_BORE / 2, ROLLER_H_PRINT + 0.2)
    return body


def build_lower_plate():
    """Lower holder plate — L-shaped bracket (horizontal base + vertical wall).

    Horizontal base: extended stadium (LOWER_EXTEND body), blind axle bore
    (POCKET_DEPTH deep) from inner face; outer face solid.

    Vertical wall: rises from top of base, starting ROLLER_TO_WALL_GAP
    beyond the roller surface. Top face flush with UPPER_Z (upper plate
    bottom), providing direct support.
    """
    # ── Horizontal base ───────────────────────────────────────────────────────
    with BuildSketch() as sk:
        with Locations((LOWER_EXTEND / 2, 0)):
            SlotOverall(LOWER_EXTEND + HOLDER_OD, HOLDER_OD)
    horiz = extrude(sk.sketch, HOLDER_T)
    horiz -= Pos(0, 0, HOLDER_T - POCKET_DEPTH) * Cylinder(
        PIN_BORE / 2, POCKET_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # ── Vertical wall ─────────────────────────────────────────────────────────
    wall_box = Pos(WALL_START_X, 0, HOLDER_T) * Box(
        LOWER_EXTEND - WALL_START_X, HOLDER_OD, ROLLER_H,
        align=(Align.MIN, Align.CENTER, Align.MIN),
    )
    wall_cap = Pos(LOWER_EXTEND, 0, HOLDER_T) * Cylinder(
        HOLDER_R, ROLLER_H,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return horiz + wall_box + wall_cap


def build_upper_plate():
    """Upper holder plate — short removable cap.

    Blind axle bore from inner (bottom) face. Far end rests on the lower
    plate's vertical wall. Attachment method TBD pending housing design.
    """
    with BuildSketch() as sk:
        with Locations((UPPER_EXTEND / 2, 0)):
            SlotOverall(UPPER_EXTEND + HOLDER_OD, HOLDER_OD)
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

    assembly = roller + lower_plate + upper_plate
    export_step(assembly, str(OUT / "assembly.step"))

    print(f"Exported: {sorted(p.name for p in OUT.iterdir())}")
    print(f"Axle (sourced): ⌀{PIN_D}mm × {AXLE_L:.1f}mm steel")
    print()
    print("Clearances:")
    print(f"  Roller axial each end : {ROLLER_AXIAL_CLEARANCE/2:.2f} mm")
    print(f"  Axle radial each side : {AXLE_RADIAL_CLEARANCE:.2f} mm")
    print(f"  Roller to wall (radial): {ROLLER_TO_WALL_GAP:.2f} mm")
    print()
    print("Wall thicknesses:")
    print(f"  Roller wall (nylon)   : {ROLLER_WALL:.2f} mm")
    print(f"  Holder wall at pin    : {HOLDER_WALL:.2f} mm  (FDM pref ≥{FDM_WALL_PREF})")
    print(f"  Outer face wall       : {OUTER_FACE_WALL:.2f} mm  (FDM min ≥{FDM_WALL_MIN})")
    print(f"  Roller protrusion     : {ROLLER_PROTRUSION:.2f} mm beyond holder each side")


if __name__ == "__main__":
    main()
