# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
#     "bd_warehouse",
# ]
# ///
"""Frame — rotates inside the mount around the vertical bore axis.

Four printed designs:
  - top_plate, bottom_plate  (rectangular; M6 inserts in TOP face for sleeve bolt
                              and in FRONT face for face plate attach)
  - sleeve                   (ø9.9 OD × ø6.5 bore × 29 mm, axial through bearings)
  - face_plate               (vertical, bolts to top + bottom plates; carries
                              4× M5 inserts on front for router-side adapters)

Structural connection: the face plate (bolted via 4× M6 flat-head countersunk)
provides anti-rotation between top and bottom plates. No off-axis sleeve needed.

Assembly: drop sleeve through the mount bearings onto bottom plate, place
top plate on sleeve. Tighten the sleeve bolt (vertical M6, top→bottom plate
insert). Then bolt face plate front→top plate and front→bottom plate via
4× M6 flat-head countersunk into the plates' front-face inserts.

Run:
    uv run --script m2/frame.py

Exports to m2/out/:
    top_plate, bottom_plate, sleeve            (.step + .stl)
    frame_mount_assembly                       (.step — mount + bearings + frame)

Coordinates (inherited from m2/mount.py)
----------------------------------------
  +X : mount width
  +Y : mount depth; −Y is in front of the mount
  +Z : up.  Frame mirrors above and below the mount.
  Bore axis at (x=0, y=−16.5).
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align, Axis, Box, BuildLine, BuildSketch, Circle, Compound, Cone, Cylinder,
    Line, Locations, Pos, Rectangle, Rotation, ThreePointArc, chamfer,
    export_step, export_stl, extrude, make_face,
)

# Single source of truth — pull mount geometry from m2/mount.py
from mount import (
    BEARING_BORE, BEARING_W, HOLE_X, HOLE_Y,
    MOUNT_D, MOUNT_H, MOUNT_W,
    build_mount,
)

# ══════════════════════════════════════════════════════════════════════════════
# Source values — frame design parameters
# ══════════════════════════════════════════════════════════════════════════════

ROTATION_HALF_ANGLE      = 60.0   # ° — design rotation half-range; used for clearance maths
FACEPLATE_DIST_FROM_AXIS = 38.0   # mm — face plate back face distance from rotation axis

PLATE_T   = 14.0   # mm — fits 10mm M6 insert + walls; with FACEPLATE_ATTACH_Z
                   # offset 1mm from plate centre, M6 flat-head countersink has
                   # 1.5mm clearance to the (flush) face plate bottom edge
PLATE_W   = 70.0   # mm — wider than face plate insert pattern (M6 at ±27 + countersink)
PLATE_GAP = 0.5    # mm — air gap between plate body inner face and mount face
                   # (plate body sits clear of mount; only the boss touches the bearing)

# D-shape plate — flat front, half-circle back
PLATE_Y_BACK_OFFSET  = 13.5  # mm — plate back past standoff A; sized so the ø12
                             # axial counterbore has ≥7mm wall thickness to the
                             # back arc of the D-shape

SLEEVE_OD  = 9.9   # mm — slip fit on the 6800 bearing bore (ø10 nominal)
SLEEVE_BOLT_CLEARANCE = 6.5   # mm — M6 clearance through the sleeve

# Bearing inner-race boss: annular ring on the inner face of each plate that
# touches the bearing inner race only (cleared from the outer race).  When
# the M6 bolts tighten, the bosses + sleeve clamp the bearing inner races
# axially without ever rubbing the (stationary) outer races.
BOSS_OD    = 13.0  # mm — annular boss ø; covers 6800 inner race face, clears outer race ID ~15mm
BOSS_DEPTH = 0.5   # mm — boss protrusion below/above the plate body inner face

# Fasteners — all M6 heat-set inserts are 10mm long (user's standard inserts)
BOLT_CLEARANCE_D = 6.5    # mm — M6 clearance
INSERT_OD        = 8.0    # mm — M6 heat-set insert NOMINAL OD (pre-bore is smaller; see below)
INSERT_LENGTH    = 10.0   # mm — user's M6 inserts are 10mm

# Heat-set insert pre-bore: slightly smaller than nominal insert OD so the
# melted plastic grips the brass.  Standard practice for M5/M6 with brass
# heat-set inserts (Ruthex, McMaster) is 0.1–0.2 mm reduction.
HEATSET_PREBORE_REDUCTION = 0.15  # mm — pre-bore_ø = insert_OD − this
HEATSET_CHAMFER_DEPTH     = 0.5   # mm — entry chamfer depth (guides insert in)
HEATSET_CHAMFER_WIDTH     = 0.5   # mm — radial widening at the entry
# Relief bore behind the insert so displaced plastic has somewhere to go
# during heat-pressing (otherwise it bunches up and blocks the bolt path).
HEATSET_RELIEF_DEPTH      = 3.0   # mm — depth of bolt-clearance bore past the insert
M5_BOLT_CLEARANCE_D       = 5.5   # mm — M5 clearance (relief diameter for M5 inserts)

# M6 flat-head (countersunk) bolt for face plate to top/bottom plate attachment
M6_HEAD_OD            = 12.0  # mm — M6 flat-head head ø (countersink at face)
M6_COUNTERSINK_DEPTH  = 3.0   # mm — countersink depth (~90° cone for M6 flat-head)

# Axial bolt (sleeve A) recess: counterbore the head into the top plate so
# a shorter bolt (M6×45 flat-head) reaches into the bottom-plate insert with
# proper thread engagement. Depth = 5mm gives 7mm engagement for an M6×45.
AXIAL_BOLT_COUNTERBORE_DEPTH = 5.0  # mm — head recess into top plate at standoff A

# Notch the plate's front-inner edge so the M5 router insert chamfers on the
# face plate aren't partially blocked by the plate sitting right behind them.
# Width covers both router insert positions (X=±19) plus chamfer extent, but
# stops short of the M6 attach insert positions (X=±27) — so it doesn't touch
# the M6 attach pockets.
PLATE_FRONT_NOTCH_X_HALF = 23.0   # mm — half-width (notch spans X=±23)
PLATE_FRONT_NOTCH_DEPTH  = 4.0    # mm — Y depth into plate from the front face
PLATE_FRONT_NOTCH_HEIGHT = 3.5    # mm — Z height (clears M5 chamfer top w/ 1.5mm margin)

# Approximate 6800 outer-race ID (for the boss-clears-outer-race assertion)
BEARING_OUTER_RACE_ID = 15.0   # mm — typical 6800 inner-race-to-outer-race gap

# ── Face plate (router mounting surface, SEPARATE part, bolts to top+bottom plates) ──
# Carries 4× M5 heat-set inserts on its front face (router-adapter bolts to it)
# and 4× M6 flat-head countersunk bolts that attach the face plate to the
# top and bottom plates.
FACEPLATE_W           = 70.0   # mm — X extent (matches plate width)
FACEPLATE_T           = 8.0    # mm — Y thickness (room for countersink + clearance)
# Face plate top flush with top plate top (computed from PLATE_OUTER_Z_TOP)

# M5 router inserts on face plate FRONT
ROUTER_INSERT_OD      = 7.0    # mm — M5 heat-set insert pre-bore
ROUTER_INSERT_LENGTH  = 6.0    # mm — short M5 insert
ROUTER_BOLT_PATTERN_X = 38.0   # mm — horizontal (Onefinity forum, 65mm clamp)
ROUTER_BOLT_PATTERN_Z = 25.0   # mm — vertical
ROUTER_INSERT_Z_CENTRE = 0.0   # mm — centred on the bore axis Z

# M6 face-plate-to-plate attachment positions (countersunk through face plate
# into M6 inserts in top/bottom plates). 2 per plate, 4 total.
FACEPLATE_ATTACH_X      = 27.0   # mm — X offset from centre (well clear of M5 router at ±19)
# FACEPLATE_ATTACH_Z derived (centred in plate Z range)

# FDM wall thickness guidance (project convention)
FDM_WALL_MIN  = 1.2   # mm
FDM_WALL_PREF = 1.5   # mm

# ══════════════════════════════════════════════════════════════════════════════
# Derived dimensions
# ══════════════════════════════════════════════════════════════════════════════

# Single axial sleeve (A) on the bore axis; face plate provides the second
# structural connection between top and bottom plates.
SLEEVE_A_X, SLEEVE_A_Y = HOLE_X, HOLE_Y                       # axial: on bore

# Rectangular plate footprint
PLATE_Y_FRONT  = HOLE_Y - FACEPLATE_DIST_FROM_AXIS            # = −54.5
PLATE_Y_BACK   = SLEEVE_A_Y + PLATE_Y_BACK_OFFSET             # = −10 (wall around standoff A bolt)
PLATE_LENGTH       = PLATE_Y_BACK - PLATE_Y_FRONT                # = 44.5 mm
PLATE_CENTRE_Y     = (PLATE_Y_FRONT + PLATE_Y_BACK) / 2
# D-shape geometry: flat front + half-circle back of radius PLATE_W/2.
# Cap centre at Y where rectangle meets the half-circle.
PLATE_Y_CAP_CENTRE = PLATE_Y_BACK - PLATE_W / 2                  # = -45 mm

# Z stack
PLATE_INNER_Z_TOP    =  MOUNT_H/2 + PLATE_GAP                 # top plate bottom face
PLATE_OUTER_Z_TOP    =  PLATE_INNER_Z_TOP + PLATE_T           # top plate top face
PLATE_INNER_Z_BOTTOM = -MOUNT_H/2 - PLATE_GAP                 # bottom plate top face
PLATE_OUTER_Z_BOTTOM =  PLATE_INNER_Z_BOTTOM - PLATE_T        # bottom plate bottom face

BOSS_Z_TOP    =  MOUNT_H / 2                                  # +14, top boss bottom face
BOSS_Z_BOTTOM = -MOUNT_H / 2                                  # -14, bottom boss top face
SLEEVE_LENGTH = BOSS_Z_TOP - BOSS_Z_BOTTOM                    # = 28 mm (sits between bosses)

INSERT_CLEARANCE_DEPTH = PLATE_T - INSERT_LENGTH              # M6 clearance below insert

# Face plate Z: both top and bottom flush with the plates
FACEPLATE_Z_BOTTOM = PLATE_OUTER_Z_BOTTOM                        # flush with bottom plate
FACEPLATE_Z_TOP    = PLATE_OUTER_Z_TOP                           # flush with top plate
FACEPLATE_H        = FACEPLATE_Z_TOP - FACEPLATE_Z_BOTTOM
FACEPLATE_Z_CENTRE = (FACEPLATE_Z_BOTTOM + FACEPLATE_Z_TOP) / 2

# Face plate Y: back face meets plate front face (face plate sits in front)
FACEPLATE_Y_BACK   = PLATE_Y_FRONT                               # mating plane
FACEPLATE_Y_FRONT  = FACEPLATE_Y_BACK - FACEPLATE_T
FACEPLATE_Y_CENTRE = (FACEPLATE_Y_BACK + FACEPLATE_Y_FRONT) / 2

# Plate Z centres (geometric, reference only)
PLATE_TOP_Z_CENTRE    = (PLATE_INNER_Z_TOP + PLATE_OUTER_Z_TOP) / 2
PLATE_BOTTOM_Z_CENTRE = (PLATE_INNER_Z_BOTTOM + PLATE_OUTER_Z_BOTTOM) / 2

# Face-plate-to-plate attach Z position — offset 1mm from plate centre toward
# the plate inner face, so the M6 flat-head countersink (ø12) has 1.5mm clearance
# to the face plate's outer edge (which is flush with the plate outer face).
FACEPLATE_ATTACH_Z_OFFSET = 1.0   # mm — offset from plate centre toward inner face
FACEPLATE_ATTACH_Z        = PLATE_TOP_Z_CENTRE - FACEPLATE_ATTACH_Z_OFFSET
# Bottom-plate attach uses -FACEPLATE_ATTACH_Z (mirror)

# 4× M5 router insert positions (X, Z) on face plate front face
ROUTER_INSERT_XZ = [
    ( ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE + ROUTER_BOLT_PATTERN_Z/2),
    (-ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE + ROUTER_BOLT_PATTERN_Z/2),
    ( ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE - ROUTER_BOLT_PATTERN_Z/2),
    (-ROUTER_BOLT_PATTERN_X/2, ROUTER_INSERT_Z_CENTRE - ROUTER_BOLT_PATTERN_Z/2),
]

# 4× M6 face-plate-to-plate attachment positions (X, Z), holes in face plate
FACEPLATE_ATTACH_XZ = [
    ( FACEPLATE_ATTACH_X,  FACEPLATE_ATTACH_Z),
    (-FACEPLATE_ATTACH_X,  FACEPLATE_ATTACH_Z),
    ( FACEPLATE_ATTACH_X, -FACEPLATE_ATTACH_Z),
    (-FACEPLATE_ATTACH_X, -FACEPLATE_ATTACH_Z),
]

# Face plate rotation clearance vs mount — full check after _AXIS_TO_CORNER defined
FACEPLATE_BACK_DIST_FROM_AXIS = abs(FACEPLATE_Y_BACK - HOLE_Y)

# Margins (M5 router inserts)
_INSERT_R              = ROUTER_INSERT_OD / 2
_INSERT_MARGIN_X       = FACEPLATE_W/2 - (ROUTER_BOLT_PATTERN_X/2 + _INSERT_R)
_INSERT_WALL_BEHIND    = FACEPLATE_T - ROUTER_INSERT_LENGTH

# Margins (M6 face-plate attachment in face plate — countersink ø takes more space)
_M6_HEAD_R             = M6_HEAD_OD / 2
_ATTACH_MARGIN_X       = FACEPLATE_W/2 - (FACEPLATE_ATTACH_X + _M6_HEAD_R)
_ATTACH_MARGIN_Z_TOP   = FACEPLATE_Z_TOP - (FACEPLATE_ATTACH_Z + _M6_HEAD_R)
_ATTACH_MARGIN_Z_BOT   = (-FACEPLATE_ATTACH_Z - _M6_HEAD_R) - FACEPLATE_Z_BOTTOM

# M5 router inserts must clear M6 attach holes (different X, separated)
_ROUTER_TO_ATTACH_DIST = math.sqrt(
    (FACEPLATE_ATTACH_X - ROUTER_BOLT_PATTERN_X/2)**2
    + (FACEPLATE_ATTACH_Z - ROUTER_BOLT_PATTERN_Z/2)**2
)
_ROUTER_TO_ATTACH_CLEARANCE = _ROUTER_TO_ATTACH_DIST - (_INSERT_R + _M6_HEAD_R)

# ── Rotation clearance check ──────────────────────────────────────────────────
# The face plate (closest off-axis rigid feature) must not intersect the mount
# swept envelope. Mount's worst-case point from the rotation axis is the front
# corner at (±MOUNT_W/2, −MOUNT_D/2).
_CORNER_X = MOUNT_W / 2
_CORNER_Y = -MOUNT_D / 2
_AXIS_TO_CORNER = math.sqrt(_CORNER_X**2 + (HOLE_Y - _CORNER_Y)**2)   # ≈18.9

FACEPLATE_TO_MOUNT_CLEARANCE = FACEPLATE_BACK_DIST_FROM_AXIS - _AXIS_TO_CORNER

# ══════════════════════════════════════════════════════════════════════════════
# Assertions — running this file IS the test suite
# ══════════════════════════════════════════════════════════════════════════════

assert SLEEVE_OD <= BEARING_BORE, (
    f"sleeve ø{SLEEVE_OD}mm > bearing bore ø{BEARING_BORE}mm — won't fit"
)
assert SLEEVE_BOLT_CLEARANCE < SLEEVE_OD - 1.0, (
    f"sleeve wall ({(SLEEVE_OD - SLEEVE_BOLT_CLEARANCE)/2:.2f}mm) below 0.5mm"
)
assert PLATE_T >= INSERT_LENGTH, (
    f"plate {PLATE_T}mm < insert length {INSERT_LENGTH}mm — pocket can't fit"
)
assert PLATE_W > INSERT_OD + 2.0, (
    f"plate width {PLATE_W}mm leaves <1mm wall around insert ø{INSERT_OD}"
)
assert BOSS_OD > SLEEVE_OD, (
    f"boss ø{BOSS_OD} ≤ sleeve ø{SLEEVE_OD} — boss must cover sleeve top"
)
assert BOSS_OD < BEARING_OUTER_RACE_ID, (
    f"boss ø{BOSS_OD} ≥ outer-race ID ø{BEARING_OUTER_RACE_ID} — boss would rub outer race"
)
assert (BOSS_OD - BOLT_CLEARANCE_D) / 2 >= 1.0, (
    f"boss ring is {(BOSS_OD - BOLT_CLEARANCE_D)/2:.2f}mm wide — too thin to seat reliably"
)

# Face plate assertions
assert FACEPLATE_H > 0, (
    f"face plate has zero or negative height — top plate inner Z "
    f"({PLATE_INNER_Z_TOP}) ≤ bottom plate outer Z ({PLATE_OUTER_Z_BOTTOM}) + gap"
)
assert _INSERT_MARGIN_X >= FDM_WALL_PREF, (
    f"face plate X margin around M5 insert is {_INSERT_MARGIN_X:.2f}mm < {FDM_WALL_PREF}mm pref"
)
assert _INSERT_WALL_BEHIND >= FDM_WALL_MIN, (
    f"face plate wall behind M5 insert is {_INSERT_WALL_BEHIND:.2f}mm < {FDM_WALL_MIN}mm min"
)
assert _ATTACH_MARGIN_X >= FDM_WALL_PREF, (
    f"face plate X margin around M6 countersink is {_ATTACH_MARGIN_X:.2f}mm < {FDM_WALL_PREF}mm pref"
)
assert _ATTACH_MARGIN_Z_TOP >= FDM_WALL_PREF, (
    f"face plate Z margin above top M6 countersink is {_ATTACH_MARGIN_Z_TOP:.2f}mm"
)
assert _ATTACH_MARGIN_Z_BOT >= FDM_WALL_PREF, (
    f"face plate Z margin below bottom M6 countersink is {_ATTACH_MARGIN_Z_BOT:.2f}mm"
)
assert _ROUTER_TO_ATTACH_CLEARANCE > 0, (
    f"M5 router insert overlaps M6 attach countersink — "
    f"{-_ROUTER_TO_ATTACH_CLEARANCE:.2f}mm overlap"
)
assert PLATE_T >= INSERT_LENGTH + FDM_WALL_MIN, (
    f"plate {PLATE_T}mm too thin for {INSERT_LENGTH}mm M6 insert + wall"
)
# Axial counterbore must leave some M6 clearance bore below the countersink
_AXIAL_CLEARANCE_REMAINING = PLATE_T - AXIAL_BOLT_COUNTERBORE_DEPTH - M6_COUNTERSINK_DEPTH
assert _AXIAL_CLEARANCE_REMAINING >= FDM_WALL_MIN, (
    f"top-plate axial counterbore leaves only {_AXIAL_CLEARANCE_REMAINING:.2f}mm of "
    f"M6 clearance bore — reduce AXIAL_BOLT_COUNTERBORE_DEPTH or thicken plate"
)
assert PLATE_W/2 - FACEPLATE_ATTACH_X >= _INSERT_R + FDM_WALL_PREF, (
    f"plate too narrow for M6 attach insert at X=±{FACEPLATE_ATTACH_X}"
)
assert FACEPLATE_TO_MOUNT_CLEARANCE > 0, (
    f"face plate intersects mount swept envelope by "
    f"{-FACEPLATE_TO_MOUNT_CLEARANCE:.2f}mm at ±{ROTATION_HALF_ANGLE}° swing"
)

OUT = Path(__file__).parent / "out"


# ══════════════════════════════════════════════════════════════════════════════
# Geometry
# ══════════════════════════════════════════════════════════════════════════════

def _build_plate_sketch():
    """D-shape: flat front (mates with face plate) + half-circle back of
    radius PLATE_W/2.  No sharp corners at the back."""
    with BuildSketch() as sk:
        with BuildLine():
            Line((-PLATE_W/2, PLATE_Y_FRONT), ( PLATE_W/2, PLATE_Y_FRONT))
            Line(( PLATE_W/2, PLATE_Y_FRONT), ( PLATE_W/2, PLATE_Y_CAP_CENTRE))
            ThreePointArc(
                ( PLATE_W/2, PLATE_Y_CAP_CENTRE),
                ( 0,         PLATE_Y_BACK),
                (-PLATE_W/2, PLATE_Y_CAP_CENTRE),
            )
            Line((-PLATE_W/2, PLATE_Y_CAP_CENTRE), (-PLATE_W/2, PLATE_Y_FRONT))
        make_face()
    return sk.sketch


def _heatset_pocket_z_down(insert_od, length, x, y, z_face, relief_d, relief_depth=None):
    """Heat-set insert pocket: pre-bore + entry chamfer + back relief.
    Direction: going DOWN from z_face.  The relief gives displaced plastic
    somewhere to go during heat-pressing; if the relief extends past the
    part's back face the boolean automatically becomes a through-hole.
    Returns a SHAPE to subtract from the parent plate."""
    if relief_depth is None:
        relief_depth = HEATSET_RELIEF_DEPTH
    pre_bore_r = (insert_od - HEATSET_PREBORE_REDUCTION) / 2
    # Main bore
    bore = Pos(x, y, z_face - length) * Cylinder(
        pre_bore_r, length + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Entry chamfer: wider at z_face, narrowing into the part
    chamfer = Pos(x, y, z_face - HEATSET_CHAMFER_DEPTH) * Cone(
        bottom_radius=pre_bore_r,
        top_radius=pre_bore_r + HEATSET_CHAMFER_WIDTH,
        height=HEATSET_CHAMFER_DEPTH + 0.05,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Relief bore behind the insert (smaller diameter, for displaced plastic)
    relief = Pos(x, y, z_face - length - relief_depth) * Cylinder(
        relief_d / 2, relief_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return bore + chamfer + relief


def _heatset_pocket_y_in(insert_od, length, x, y_face, z, relief_d, relief_depth=None):
    """Heat-set insert pocket: pre-bore + entry chamfer + back relief.
    Direction: going +Y from y_face (into the plate from its front face).
    Returns a SHAPE to subtract from the parent plate."""
    if relief_depth is None:
        relief_depth = HEATSET_RELIEF_DEPTH
    pre_bore_r = (insert_od - HEATSET_PREBORE_REDUCTION) / 2
    # Main bore
    bore = Pos(x, y_face - 0.05, z) * Rotation((-90, 0, 0)) * Cylinder(
        pre_bore_r, length + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Entry chamfer
    chamfer = Pos(x, y_face, z) * Rotation((-90, 0, 0)) * Cone(
        bottom_radius=pre_bore_r + HEATSET_CHAMFER_WIDTH,
        top_radius=pre_bore_r,
        height=HEATSET_CHAMFER_DEPTH + 0.05,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Relief bore behind the insert
    relief = Pos(x, y_face + length - 0.05, z) * Rotation((-90, 0, 0)) * Cylinder(
        relief_d / 2, relief_depth + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return bore + chamfer + relief


def _countersink_through(thickness):
    """Cone (M6 flat-head countersink) + cylinder (M6 clearance) through a plate.
    Oriented along +Z initially; rotate to face direction at the call site."""
    cone = Cone(
        bottom_radius=M6_HEAD_OD/2 + 0.25,
        top_radius=BOLT_CLEARANCE_D/2,
        height=M6_COUNTERSINK_DEPTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    cyl = Pos(0, 0, M6_COUNTERSINK_DEPTH) * Cylinder(
        BOLT_CLEARANCE_D/2,
        thickness - M6_COUNTERSINK_DEPTH + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return cone + cyl


def build_top_plate():
    """Top plate: rectangular body + bearing boss at standoff A,
    M6 through-clearance at both standoffs (for sleeve bolts),
    M6 insert pockets in front face (for face plate attach)."""
    body = Pos(0, 0, PLATE_INNER_Z_TOP) * extrude(_build_plate_sketch(), PLATE_T)
    boss = Pos(SLEEVE_A_X, SLEEVE_A_Y, PLATE_INNER_Z_TOP) * Cylinder(
        BOSS_OD/2, BOSS_DEPTH,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )
    plate = body + boss
    # Vertical M6 clearance at standoff A (sleeve A bolt from above)
    plate -= Pos(SLEEVE_A_X, SLEEVE_A_Y, PLATE_INNER_Z_TOP - BOSS_DEPTH - 0.1) * Cylinder(
        BOLT_CLEARANCE_D/2, PLATE_T + BOSS_DEPTH + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Counterbore + countersink at standoff A so the M6 flat-head bolt's head
    # sits recessed below the top face, gaining engagement at the bottom plate insert.
    plate -= Pos(SLEEVE_A_X, SLEEVE_A_Y, PLATE_OUTER_Z_TOP - AXIAL_BOLT_COUNTERBORE_DEPTH) * Cylinder(
        M6_HEAD_OD/2, AXIAL_BOLT_COUNTERBORE_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    _csk_bottom_z = PLATE_OUTER_Z_TOP - AXIAL_BOLT_COUNTERBORE_DEPTH - M6_COUNTERSINK_DEPTH
    plate -= Pos(SLEEVE_A_X, SLEEVE_A_Y, _csk_bottom_z) * Cone(
        bottom_radius=BOLT_CLEARANCE_D/2,
        top_radius=M6_HEAD_OD/2,
        height=M6_COUNTERSINK_DEPTH + 0.05,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Horizontal M6 insert pockets in front face (face plate attaches here)
    for sign in (+1, -1):
        plate -= _heatset_pocket_y_in(
            INSERT_OD, INSERT_LENGTH,
            sign * FACEPLATE_ATTACH_X, PLATE_Y_FRONT, FACEPLATE_ATTACH_Z,
            relief_d=BOLT_CLEARANCE_D,
        )
    # Front-inner notch so the M5 router insert chamfers on the face plate
    # aren't blocked by this plate sitting behind them.  Stops short of the
    # M6 attach pockets in X (±23 < ±27).
    plate -= Pos(0, PLATE_Y_FRONT - 0.05, PLATE_INNER_Z_TOP - 0.05) * Box(
        2 * PLATE_FRONT_NOTCH_X_HALF,
        PLATE_FRONT_NOTCH_DEPTH + 0.05,
        PLATE_FRONT_NOTCH_HEIGHT + 0.05,
        align=(Align.CENTER, Align.MIN, Align.MIN),
    )
    return plate


def build_bottom_plate():
    """Bottom plate: rectangular body + bearing boss at standoff A,
    M6 insert in TOP face for sleeve A bolt,
    M6 inserts in FRONT face for face plate attach."""
    body = Pos(0, 0, PLATE_OUTER_Z_BOTTOM) * extrude(_build_plate_sketch(), PLATE_T)
    boss = Pos(SLEEVE_A_X, SLEEVE_A_Y, PLATE_INNER_Z_BOTTOM) * Cylinder(
        BOSS_OD/2, BOSS_DEPTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    plate = body + boss

    # Sleeve A insert pocket: from top face (z=PLATE_INNER_Z_BOTTOM) going DOWN.
    # Relief is the M6 clearance through the rest of the plate to the bottom face.
    plate -= _heatset_pocket_z_down(
        INSERT_OD, INSERT_LENGTH,
        SLEEVE_A_X, SLEEVE_A_Y, PLATE_INNER_Z_BOTTOM,
        relief_d=BOLT_CLEARANCE_D, relief_depth=INSERT_CLEARANCE_DEPTH,
    )
    plate -= Pos(SLEEVE_A_X, SLEEVE_A_Y, PLATE_INNER_Z_BOTTOM - 0.05) * Cylinder(
        BOLT_CLEARANCE_D/2, BOSS_DEPTH + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Horizontal M6 insert pockets in front face (face plate attach)
    for sign in (+1, -1):
        plate -= _heatset_pocket_y_in(
            INSERT_OD, INSERT_LENGTH,
            sign * FACEPLATE_ATTACH_X, PLATE_Y_FRONT, -FACEPLATE_ATTACH_Z,
            relief_d=BOLT_CLEARANCE_D,
        )
    # Front-inner notch (mirror of top plate's): clears M5 router insert
    # chamfers on the face plate. Extends DOWN from the inner (top) face.
    plate -= Pos(0, PLATE_Y_FRONT - 0.05, PLATE_INNER_Z_BOTTOM + 0.05) * Box(
        2 * PLATE_FRONT_NOTCH_X_HALF,
        PLATE_FRONT_NOTCH_DEPTH + 0.05,
        PLATE_FRONT_NOTCH_HEIGHT + 0.05,
        align=(Align.CENTER, Align.MIN, Align.MAX),
    )
    return plate


def build_face_plate():
    """Face plate — SEPARATE part. Bolts to top + bottom plates via 4× M6
    flat-head countersunk bolts. Carries 4× M5 heat-set inserts on the
    front face for router-side adapter attachment."""
    plate = Pos(0, FACEPLATE_Y_CENTRE, FACEPLATE_Z_CENTRE) * Box(
        FACEPLATE_W, FACEPLATE_T, FACEPLATE_H,
    )
    # 4× M5 router insert pockets on front face (chamfered, pre-bore < insert OD)
    # The relief extends past the face plate back — effectively a through-hole
    # that lets displaced plastic escape into the air behind the face plate.
    for ix, iz in ROUTER_INSERT_XZ:
        plate -= _heatset_pocket_y_in(
            ROUTER_INSERT_OD, ROUTER_INSERT_LENGTH,
            ix, FACEPLATE_Y_FRONT, iz,
            relief_d=M5_BOLT_CLEARANCE_D,
        )
    # 4× M6 countersunk through-holes for attachment to plates
    for ix, iz in FACEPLATE_ATTACH_XZ:
        plate -= Pos(ix, FACEPLATE_Y_FRONT - 0.05, iz) * Rotation((-90, 0, 0)) \
                 * _countersink_through(FACEPLATE_T)
    return plate


def build_sleeve():
    """Printed tube: ø SLEEVE_OD outer, ø SLEEVE_BOLT_CLEARANCE bore,
    SLEEVE_LENGTH long, aligned with bottom face at z=0."""
    sleeve = Cylinder(
        SLEEVE_OD/2, SLEEVE_LENGTH,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return sleeve - Cylinder(
        SLEEVE_BOLT_CLEARANCE/2, SLEEVE_LENGTH + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


def build_assembly():
    """Mount + 2 bearings + 2 plates + 2 sleeves + face plate."""
    from bd_warehouse.bearing import SingleRowDeepGrooveBallBearing

    mount   = build_mount()
    bearing = lambda: SingleRowDeepGrooveBallBearing(size="M10-19-5")
    top_bearing    = Pos(HOLE_X, HOLE_Y,  MOUNT_H/2 - BEARING_W) * bearing()
    bottom_bearing = Pos(HOLE_X, HOLE_Y, -MOUNT_H/2            ) * bearing()

    top_plate    = build_top_plate()
    bottom_plate = build_bottom_plate()
    face_plate   = build_face_plate()
    sleeve_a = Pos(SLEEVE_A_X, SLEEVE_A_Y, BOSS_Z_BOTTOM) * build_sleeve()

    return Compound(children=[
        mount, top_bearing, bottom_bearing,
        top_plate, bottom_plate, face_plate, sleeve_a,
    ])


def main():
    parts = {
        "top_plate":    build_top_plate(),
        "bottom_plate": build_bottom_plate(),
        "face_plate":   build_face_plate(),
        "sleeve":       build_sleeve(),
    }

    OUT.mkdir(exist_ok=True)
    for name, part in parts.items():
        export_step(part, str(OUT / f"{name}.step"))
        export_stl(part,  str(OUT / f"{name}.stl"))

    assembly = build_assembly()
    export_step(assembly, str(OUT / "frame_mount_assembly.step"))

    print(f"Frame: single-axial sleeve + face plate (no off-axis sleeve)")
    print(f"  Plates: D-shaped, {PLATE_W} wide × {PLATE_LENGTH:.1f} long × {PLATE_T} thick mm "
          f"(flat front, half-circle back)")
    print(f"  Sleeve A: ø{SLEEVE_OD} × {SLEEVE_LENGTH}mm, ø{SLEEVE_BOLT_CLEARANCE} bore "
          f"(through the bearings)")
    print(f"  Bearing boss: ø{BOSS_OD} × {BOSS_DEPTH}mm protrusion (each plate)")
    print(f"  Face plate: {FACEPLATE_W} × {FACEPLATE_T} × {FACEPLATE_H:.1f} mm "
          f"(W×T×H), bottom flush with bottom plate, top at z={FACEPLATE_Z_TOP}")
    print(f"  Router inserts: 4× M5 in {ROUTER_BOLT_PATTERN_X}×{ROUTER_BOLT_PATTERN_Z}mm "
          f"pattern (ø{ROUTER_INSERT_OD} × {ROUTER_INSERT_LENGTH}mm)")
    print(f"  Face-plate→plate attach: 4× M6 flat-head SHCS through countersinks; "
          f"4× M6 heat-set inserts ({INSERT_LENGTH}mm) in plate front faces")
    print(f"  Axial fastener: 1× M6 × 45 flat-head countersunk into M6 insert "
          f"({INSERT_LENGTH}mm) in bottom plate top face; "
          f"top plate has {AXIAL_BOLT_COUNTERBORE_DEPTH}mm counterbore "
          f"(head sits recessed → 7mm thread engagement)")
    print(f"  Face plate clearance to mount: {FACEPLATE_TO_MOUNT_CLEARANCE:.2f}mm")
    print(f"Exported {len(parts)} part designs + 1 assembly to {OUT}")


if __name__ == "__main__":
    main()
