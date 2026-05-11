# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
#     "bd_warehouse",
# ]
# ///
"""back_wing — bridges the m2 cutter to the rotating-frame face plate.

A flat printed panel that sandwiches between the cutter's squared back faces
(plate + shoe) and the face plate of the rotating frame.

- 4× M5 flat-head countersunk bolts on the wing FRONT (cutter side) → into
  the face plate's M5 heat-set inserts (38×25mm router-spindle pattern).
- 4× M4 flat-head countersunk bolts on the wing BACK (face plate side) → into
  the cutter's M4 heat-set inserts in the plate and shoe back faces.

Vertical alignment (option B): wing matches the cutter's full height.
Bottom of the cutter shoe is flush with the bottom of the mount (face plate
Z = −14). Wing top sits 2.5mm above the face plate top (face plate Z = +31).

Assembly order
  1. Bolt cutter to wing using the four M4 bolts (heads countersunk into the
     wing BACK face — still accessible at this stage).
  2. Bolt the cutter+wing assembly to the face plate using the four M5 bolts
     from the wing FRONT face — heads sit at X=±19, outside the cutter's
     ±15mm footprint, so an Allen key can reach them around the cutter.

Coordinate system (wing local)
  +X : width — matches face-plate X axis when assembled.
  +Y : thickness — back face at y=0 (touches face plate); front face at y=−WING_T.
  +Z : height — matches face-plate Z and mount Z. Z=0 is the rotation/bore axis.

Run
    uv run --script m2/back_wing.py
Exports to m2/out/: back_wing (.step + .stl)
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align, Box, Compound, Cylinder, Pos, Rotation,
    export_step, export_stl,
)

from cutter import (
    BACK_MOUNT_INSERT_Y as CUTTER_M4_Y,
    M4_BOLT_CLEARANCE_D,
    PLATE_T as CUTTER_PLATE_T,
    SHOE_T  as CUTTER_SHOE_T,
    STANDOFF_H as CUTTER_STANDOFF_H,
)
from frame import (
    ROUTER_BOLT_PATTERN_X,
    ROUTER_BOLT_PATTERN_Z,
    ROUTER_INSERT_Z_CENTRE,
)
from mount import MOUNT_H

# ══════════════════════════════════════════════════════════════════════════════
# Source values
# ══════════════════════════════════════════════════════════════════════════════

# Bolt-head dimensions.
# M5: socket-head cap screw (ISO 4762 / SHCS) — smaller OD than pan-head so
# the head sits clear of the cutter's 30mm width (head edge at y=14.75 vs the
# cutter edge at y=15, fine).  M4: pan-head (ISO 7045) — cutter is wide enough
# at the M4 positions to clear the larger head.
M5_HEAD_OD            = 8.5    # mm — M5 SHCS head OD (nominal)
M5_HEAD_HEIGHT        = 5.0    # mm — SHCS head height
M5_COUNTERBORE_D      = M5_HEAD_OD + 0.5   # 0.5 mm diametral clearance
M5_COUNTERBORE_DEPTH  = 5.5    # mm — slight margin over head height
M5_BOLT_CLEARANCE_D   = 5.5    # mm — M5 shank clearance

M4_HEAD_OD            = 8.0    # mm — M4 pan-head OD
M4_HEAD_HEIGHT        = 3.1    # mm
M4_COUNTERBORE_D      = M4_HEAD_OD + 0.5
M4_COUNTERBORE_DEPTH  = 3.5    # mm — slight margin over head height

# Wing dimensions
WING_W = 54.0   # mm — X width: covers M5 pattern (±19) + ≥5mm walls each side
WING_T =  8.0   # mm — Y thickness: M5 csk (front) + M4 csk (back) + ≥2mm wall

# Cutter vertical position — chosen so the cutter's M4 pair (shoe and plate
# centres) is centred on the bore axis, putting wing top and bottom at
# symmetric Z extents.  Shoe ends up 8.5mm below the mount bottom (which is
# fine — the rest of the rig is behind the workpiece, only the shoe touches).
_CUTTER_M4_MIDPOINT_LOCAL = (CUTTER_SHOE_T / 2
                             + CUTTER_SHOE_T + CUTTER_STANDOFF_H
                             + CUTTER_PLATE_T / 2) / 2   # = 22.5
SHOE_BOTTOM_Z   = -_CUTTER_M4_MIDPOINT_LOCAL                                  # = −22.5
CUTTER_TOP_Z    = SHOE_BOTTOM_Z + CUTTER_SHOE_T + CUTTER_STANDOFF_H + CUTTER_PLATE_T   # = +22.5

# FDM convention
FDM_WALL_MIN  = 1.2
FDM_WALL_PREF = 1.5

# ══════════════════════════════════════════════════════════════════════════════
# Derived dimensions
# ══════════════════════════════════════════════════════════════════════════════

# Wing bottom must clear both the bottom-pair M5 counterbore (always at
# face plate Z = −12.5) AND the shoe M4 counterbore (depends on cutter Z).
# Wing top must clear the M5 upper AND plate M4 counterbores likewise.
_LOWER_M4_Z = SHOE_BOTTOM_Z + CUTTER_SHOE_T / 2
_UPPER_M4_Z = SHOE_BOTTOM_Z + CUTTER_SHOE_T + CUTTER_STANDOFF_H + CUTTER_PLATE_T / 2
_LOWER_M5_Z = ROUTER_INSERT_Z_CENTRE - ROUTER_BOLT_PATTERN_Z / 2
_UPPER_M5_Z = ROUTER_INSERT_Z_CENTRE + ROUTER_BOLT_PATTERN_Z / 2

WING_Z_BOTTOM = min(
    _LOWER_M4_Z - M4_COUNTERBORE_D / 2 - FDM_WALL_PREF,
    _LOWER_M5_Z - M5_COUNTERBORE_D / 2 - FDM_WALL_PREF,
)
WING_Z_TOP = max(
    _UPPER_M4_Z + M4_COUNTERBORE_D / 2 + FDM_WALL_PREF,
    _UPPER_M5_Z + M5_COUNTERBORE_D / 2 + FDM_WALL_PREF,
)
WING_BOTTOM_TAB = SHOE_BOTTOM_Z - WING_Z_BOTTOM   # how far wing hangs below shoe
WING_TOP_OVER   = WING_Z_TOP - CUTTER_TOP_Z       # how far wing sticks above cutter

WING_H        = WING_Z_TOP - WING_Z_BOTTOM
WING_Z_CENTRE = (WING_Z_BOTTOM + WING_Z_TOP) / 2

# M5 router-pattern positions (X, Z) on the wing — match face plate M5 inserts.
M5_POSITIONS = [
    ( ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE + ROUTER_BOLT_PATTERN_Z/2),
    (-ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE + ROUTER_BOLT_PATTERN_Z/2),
    ( ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE - ROUTER_BOLT_PATTERN_Z/2),
    (-ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE - ROUTER_BOLT_PATTERN_Z/2),
]

# M4 cutter-side positions (X, Z) on the wing — must hit cutter M4 inserts.
# Cutter plate centre Z (cutter-local) = SHOE_T + STANDOFF_H + PLATE_T/2 = 39.5
# Cutter shoe  centre Z (cutter-local) = SHOE_T/2 = 5.5
CUTTER_PLATE_CENTRE_Z_LOCAL = CUTTER_SHOE_T + CUTTER_STANDOFF_H + CUTTER_PLATE_T / 2
CUTTER_SHOE_CENTRE_Z_LOCAL  = CUTTER_SHOE_T / 2
PLATE_M4_Z = SHOE_BOTTOM_Z + CUTTER_PLATE_CENTRE_Z_LOCAL    # = +25.5
SHOE_M4_Z  = SHOE_BOTTOM_Z + CUTTER_SHOE_CENTRE_Z_LOCAL     # = −8.5

# Cutter Y in cutter coords becomes wing X in wing coords (cutter rotates 90°
# about its own Z to mate against the face plate).
M4_POSITIONS = [
    ( CUTTER_M4_Y, PLATE_M4_Z),
    (-CUTTER_M4_Y, PLATE_M4_Z),
    ( CUTTER_M4_Y, SHOE_M4_Z),
    (-CUTTER_M4_Y, SHOE_M4_Z),
]

# ══════════════════════════════════════════════════════════════════════════════
# Assertions — `python back_wing.py` is the test suite
# ══════════════════════════════════════════════════════════════════════════════

_M5_HEAD_R = M5_COUNTERBORE_D / 2
_M4_HEAD_R = M4_COUNTERBORE_D / 2

# Width margin: M5 counterbore must clear the wing X edges
_X_MARGIN_M5 = WING_W / 2 - (ROUTER_BOLT_PATTERN_X / 2 + _M5_HEAD_R)
assert _X_MARGIN_M5 >= FDM_WALL_PREF, (
    f"wing too narrow: {_X_MARGIN_M5:.2f}mm wall between M5 head and wing edge"
)
# Each through-hole's pocket + remaining shank bore must fit in the wing.
# (M5 and M4 holes are at different X-Z positions so they don't stack in Y.)
assert WING_T - M5_COUNTERBORE_DEPTH >= FDM_WALL_MIN, (
    f"M5 counterbore depth {M5_COUNTERBORE_DEPTH}mm leaves "
    f"{WING_T - M5_COUNTERBORE_DEPTH:.2f}mm shank bore — needs ≥{FDM_WALL_MIN}mm"
)
assert WING_T - M4_COUNTERBORE_DEPTH >= FDM_WALL_MIN, (
    f"M4 counterbore depth {M4_COUNTERBORE_DEPTH}mm leaves "
    f"{WING_T - M4_COUNTERBORE_DEPTH:.2f}mm shank bore — needs ≥{FDM_WALL_MIN}mm"
)
# Z coverage — every hole's head must clear the wing top/bottom
for (x, z) in M5_POSITIONS:
    assert WING_Z_BOTTOM + _M5_HEAD_R + FDM_WALL_PREF <= z <= WING_Z_TOP - _M5_HEAD_R - FDM_WALL_PREF, (
        f"M5 hole at Z={z} too close to wing top/bottom"
    )
for (x, z) in M4_POSITIONS:
    assert WING_Z_BOTTOM + _M4_HEAD_R + FDM_WALL_PREF <= z <= WING_Z_TOP - _M4_HEAD_R - FDM_WALL_PREF, (
        f"M4 hole at Z={z} too close to wing top/bottom"
    )
# Diagonal centre-to-centre distance between every M5/M4 hole pair must
# leave enough material for the worst Y-depth radii overlap.  Counterbores
# are on opposite faces so they never coexist at the same Y, but the wider
# counterbore (M5 cbore R=5) faces the M4 shank (R=2.25) — worst sum 7.25.
_WORST_M5_M4_SUM_R = max(
    M5_COUNTERBORE_D / 2 + M4_BOLT_CLEARANCE_D / 2,   # M5 cbore + M4 shank
    M5_BOLT_CLEARANCE_D / 2 + M4_COUNTERBORE_D / 2,   # M5 shank + M4 cbore
)
_M5_TO_M4_MIN_CENTRE_DIST = _WORST_M5_M4_SUM_R + FDM_WALL_MIN
import math as _math
for (m5x, m5z) in M5_POSITIONS:
    for (m4x, m4z) in M4_POSITIONS:
        d = _math.hypot(m5x - m4x, m5z - m4z)
        assert d >= _M5_TO_M4_MIN_CENTRE_DIST, (
            f"M5 at ({m5x},{m5z}) and M4 at ({m4x},{m4z}) are {d:.2f}mm apart — "
            f"need ≥{_M5_TO_M4_MIN_CENTRE_DIST:.2f}mm (heads/walls overlap)"
        )

OUT = Path(__file__).parent / "out"


# ══════════════════════════════════════════════════════════════════════════════
# Geometry helpers
# ══════════════════════════════════════════════════════════════════════════════

def _cbore_through_from_front(cbore_d, cbore_depth, clearance_d, x, z):
    """Pan-head counterbore through-hole — head pocket on FRONT face
    (y=−WING_T), shank passes through to BACK face (y=0).  Cylindrical
    pocket, NOT conical countersink. Returns a shape to subtract."""
    head = Pos(x, -WING_T - 0.05, z) * Rotation((-90, 0, 0)) * Cylinder(
        cbore_d / 2, cbore_depth + 0.05,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shank = Pos(x, -WING_T + cbore_depth, z) * Rotation((-90, 0, 0)) * Cylinder(
        clearance_d / 2,
        WING_T - cbore_depth + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return head + shank


def _cbore_through_from_back(cbore_d, cbore_depth, clearance_d, x, z):
    """Pan-head counterbore through-hole — head pocket on BACK face (y=0),
    shank passes through to FRONT face (y=−WING_T)."""
    head = Pos(x, 0.05, z) * Rotation((90, 0, 0)) * Cylinder(
        cbore_d / 2, cbore_depth + 0.05,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shank = Pos(x, -cbore_depth, z) * Rotation((90, 0, 0)) * Cylinder(
        clearance_d / 2,
        WING_T - cbore_depth + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return head + shank


# ══════════════════════════════════════════════════════════════════════════════
# Geometry
# ══════════════════════════════════════════════════════════════════════════════

def build_back_wing():
    """Flat panel with 4× M5 (front-csk) and 4× M4 (back-csk) through-holes."""
    wing = Pos(0, -WING_T / 2, WING_Z_CENTRE) * Box(WING_W, WING_T, WING_H)
    for x, z in M5_POSITIONS:
        wing -= _cbore_through_from_front(
            M5_COUNTERBORE_D, M5_COUNTERBORE_DEPTH, M5_BOLT_CLEARANCE_D, x, z,
        )
    for x, z in M4_POSITIONS:
        wing -= _cbore_through_from_back(
            M4_COUNTERBORE_D, M4_COUNTERBORE_DEPTH, M4_BOLT_CLEARANCE_D, x, z,
        )
    return wing


def build_full_assembly():
    """Mount + bearings + rotating frame + back wing + cutter, fully positioned.

    World frame = mount frame (mount centred at origin, bore axis along Z at
    (x=0, y=−16.5)).  See m2/mount.py and m2/frame.py for the upstream layout.
    """
    from frame import (
        build_assembly as build_frame_assembly,
        FACEPLATE_Y_FRONT,
    )
    from cutter import (
        build_plate as build_cutter_plate,
        build_shoe  as build_cutter_shoe,
        build_upper_sleeve, build_lower_sleeve, build_washer, build_standoff,
        SURROUND_X, THREAD_X, SLOT_X_CENTER, SHOE_L,
        STANDOFF_X_INNER, STANDOFF_X_OUTER,
        WASHER_T, BEARING_THK, LOWER_FLANGE_T,
    )

    # 1. Mount + 2× 6800 bearings + rotating frame
    frame_compound = build_frame_assembly()

    # 2. Wing — back face flush against face plate front
    wing_positioned = Pos(0, FACEPLATE_Y_FRONT, 0) * build_back_wing()

    # 3. Cutter sub-assembly in CUTTER local frame (replicates cutter.py main())
    bearing_x         = SLOT_X_CENTER
    upper_assembled   = Pos(bearing_x, 0, 0)                  * build_upper_sleeve()
    washer_assembled  = Pos(bearing_x, 0, -WASHER_T)          * build_washer()
    lower_z           = -WASHER_T - BEARING_THK - LOWER_FLANGE_T
    lower_assembled   = Pos(bearing_x, 0, lower_z)            * build_lower_sleeve()
    plate_shoe_offset = SURROUND_X - THREAD_X
    plate_assembled   = Pos(plate_shoe_offset, 0,
                            CUTTER_SHOE_T + CUTTER_STANDOFF_H) * build_cutter_plate()
    standoff_x        = (STANDOFF_X_INNER + STANDOFF_X_OUTER) / 2
    standoff_assem    = Pos(standoff_x, 0, CUTTER_SHOE_T)     * build_standoff()
    cutter_local = Compound(children=[
        build_cutter_shoe(), plate_assembled, standoff_assem,
        upper_assembled, lower_assembled, washer_assembled,
    ])

    # 4. Transform cutter into mount frame:
    #    Rotation((0, 0, -90)) maps cutter local +X (snout) → mount −Y.
    #    Back face is at cutter local x=−SHOE_L/2; after rotation it sits at
    #    +SHOE_L/2 along mount +Y relative to the cutter origin.  Set the
    #    origin so the back face is flush with the wing's front face.
    wing_front_y    = FACEPLATE_Y_FRONT - WING_T
    cutter_origin_y = wing_front_y - SHOE_L / 2
    cutter_in_mount = (
        Pos(0, cutter_origin_y, SHOE_BOTTOM_Z)
        * Rotation((0, 0, -90))
        * cutter_local
    )

    return Compound(children=[frame_compound, wing_positioned, cutter_in_mount])


def main():
    wing = build_back_wing()

    OUT.mkdir(exist_ok=True)
    export_step(wing, str(OUT / "back_wing.step"))
    export_stl(wing,  str(OUT / "back_wing.stl"))

    print(f"Back wing: {WING_W} × {WING_T} × {WING_H} mm "
          f"(X × Y × Z, Z range {WING_Z_BOTTOM} to {WING_Z_TOP})")
    print(f"  4× M5 cap-head (SHCS) counterbore on FRONT face, "
          f"{ROUTER_BOLT_PATTERN_X}×{ROUTER_BOLT_PATTERN_Z}mm pattern → face plate")
    print(f"  4× M4 pan-head counterbore on BACK face, X=±{CUTTER_M4_Y}, "
          f"Z={SHOE_M4_Z} (shoe) + Z={PLATE_M4_Z} (plate) → cutter")
    print(f"  Min diagonal M5-to-M4 centre distance: "
          f"{min(_math.hypot(m5x-m4x, m5z-m4z) for (m5x,m5z) in M5_POSITIONS for (m4x,m4z) in M4_POSITIONS):.2f}mm "
          f"(≥{_M5_TO_M4_MIN_CENTRE_DIST:.2f}mm required)")
    print(f"Exported back_wing.{{step,stl}} to {OUT}")

    full = build_full_assembly()
    export_step(full, str(OUT / "full_assembly.step"))
    print(f"Exported full_assembly.step (mount + frame + wing + cutter) to {OUT}")


if __name__ == "__main__":
    main()
