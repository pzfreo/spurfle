# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "build123d",
#     "bd_warehouse",
# ]
# ///
"""slider_carriage — single integrated edge-follower for the m2 cutter.

ONE printed piece (nylon or other low-friction FDM filament, hand-finished)
that replaces the existing `lower_sleeve + 608 bearing + washer` stack
below the cutter shoe.

Design:
- Full-height body (z = 0 to z = −BODY_HEIGHT) — no thin necks; the two
  rib-contact features are integrated into the body's plan-view perimeter,
  not hanging off it
- Plan view: a rectangle on the −X / M4-bolt side, with TWO half-circle
  bumps protruding past the rectangle on the +X / rib side at Y = ±STUB_Y.
  The bump apexes are the two slider contact points — geometrically the
  same two-point contact as the dual-bearing variant, just solid
- M4 bolt clearance bore through the body's centre (for the existing M4
  clamp bolt from below, into the captive nut in the upper_sleeve)
- Short stadium UPSTAND on top of the body (z = 0 to z = CARRIAGE_UPSTAND_HEIGHT)
  that fits the BOTTOM of the shoe slot — same stadium dimensions as the
  upper_sleeve stem.  Both pieces are then rotation-locked by the slot
  walls; sliding load can no longer twist the carriage about the bolt axis.

The upper_sleeve in `m2/cutter.py` is correspondingly shortened (stem from
z = CARRIAGE_UPSTAND_HEIGHT to z = SHOE_T) — see that file.

Run:
    uv run --script m2/slider_carriage.py

Exports to m2/out/: slider_carriage  (.step + .stl)
"""
from __future__ import annotations

from pathlib import Path

import math

from build123d import (
    Align, Box, BuildSketch, Cylinder, Pos, SlotOverall,
    export_step, export_stl, extrude,
)

from cutter import (
    CARRIAGE_UPSTAND_HEIGHT,
    M4_BOLT_CLEARANCE_D,
    SHOE_T,
    UPPER_STEM1_D,
    UPPER_STEM1_LEN,
    UPPER_STEM1_OFFSET,
)

# ══════════════════════════════════════════════════════════════════════════════
# Source values
# ══════════════════════════════════════════════════════════════════════════════

# Slider bumps — integrated into the body's plan-view perimeter
STUB_OD              = 5.0   # mm — half-circle bump diameter (rib contact)
STUB_C_TO_C          = 5.0   # mm — apex-to-apex spacing in Y (bumps touch at Y=0)
STUB_X_OFFSET        = 10.5  # mm — bump centre offset from M4 bolt axis in +X.
                             # Sized so the bump's outer +X edge reaches the
                             # cutter bit centre at the slot's max-forward
                             # position → PURFLING_MIN = 0 (edge-trim capable).
                             # Bump-to-bit shaft clearance is then 0.39 mm at
                             # the worst-case slot position (see assertion).

# Body
BODY_HEIGHT          = 11.0  # mm — body Z extent below the shoe bottom
                             # (spans the violin top-plate thickness + rib contact range)
BODY_BACK_EXTENT     = 6.0   # mm — body extent in −X from the M4 bolt.
                             # Upstand stadium (length 9, offset −1.5) reaches
                             # X = −1.5 − 9/2 = −6 at its leftmost point.
                             # Body's −X edge matches so the upstand sits
                             # fully on the body — no print supports needed.
BODY_HALF_WIDTH      = 5.0   # mm — body half-extent in Y (matches bump outer Y)

# Required minimum +X protrusion of bump past body's +X edge
MIN_PROTRUSION_X     = 1.0   # mm

# FDM convention
FDM_WALL_MIN  = 1.2
FDM_WALL_PREF = 1.5

# Slot geometry (for the achievable-purfling check)
SLOT_X_CENTER = 11.125
SLOT_LEN      = 18.0
SLOT_W        = 6.5
BIT_X         = 30.125
BIT_OD        = 1.3            # mm — smallest router bit we want to support
# Effective bolt-X range — stem cap (r=3) must fit inside slot cap (r=3.25)
SLOT_CAP_CENTER_PLUS_X  = SLOT_X_CENTER + (SLOT_LEN - SLOT_W) / 2   # = 16.875
SLOT_CAP_CENTER_MINUS_X = SLOT_X_CENTER - (SLOT_LEN - SLOT_W) / 2   # = 5.375
STEM_CAP_R = UPPER_STEM1_D / 2                       # = 3
SLOT_CAP_R = SLOT_W / 2                              # = 3.25
STEM_CAP_TO_BOLT_X = UPPER_STEM1_LEN - UPPER_STEM1_D # = 3 (X distance bolt to −X stem cap centre)
BOLT_X_EFFECTIVE_MAX = SLOT_CAP_CENTER_PLUS_X + (SLOT_CAP_R - STEM_CAP_R)         # = 17.125
BOLT_X_EFFECTIVE_MIN = SLOT_CAP_CENTER_MINUS_X - (SLOT_CAP_R - STEM_CAP_R) + STEM_CAP_TO_BOLT_X  # = 8.125

# ══════════════════════════════════════════════════════════════════════════════
# Derived dimensions
# ══════════════════════════════════════════════════════════════════════════════

STUB_R       = STUB_OD / 2
STUB_Y       = STUB_C_TO_C / 2          # = 2.5

BODY_X_BACK   = -BODY_BACK_EXTENT
BODY_X_FRONT  = +STUB_X_OFFSET          # rectangle ends at the bump centre line
BODY_LEN      = BODY_X_FRONT - BODY_X_BACK
BODY_WIDTH    = 2 * BODY_HALF_WIDTH
BODY_CENTRE_X = (BODY_X_BACK + BODY_X_FRONT) / 2

STUB_OUTER_X  = STUB_X_OFFSET + STUB_R  # most +X point of the body's perimeter
STUB_OUTER_Y  = STUB_Y + STUB_R

TOTAL_HEIGHT  = BODY_HEIGHT + CARRIAGE_UPSTAND_HEIGHT   # carriage Z extent

# Achievable purfling range:
#   bit-to-edge = BIT_X − (bolt_X + STUB_X_OFFSET + STUB_R)
PURFLING_MIN = BIT_X - (BOLT_X_EFFECTIVE_MAX + STUB_OUTER_X)
PURFLING_MAX = BIT_X - (BOLT_X_EFFECTIVE_MIN + STUB_OUTER_X)

# Bump-to-bit shaft clearance at the slot's most-forward position.
# Worst case: bump centre is closest in X to the bit centre.
BIT_R = BIT_OD / 2
_BUMP_TO_BIT_DX = BIT_X - (BOLT_X_EFFECTIVE_MAX + STUB_X_OFFSET)
BUMP_TO_BIT_CLEARANCE = (
    math.hypot(_BUMP_TO_BIT_DX, STUB_Y) - (STUB_R + BIT_R)
)

R_MIN = 25.0
SAGITTA_VARIATION = (STUB_C_TO_C / 2) ** 2 / R_MIN

# Recommended M4 bolt length
# Span from bolt head (at body bottom) to engaged threads in captive nut
# (top of upper_sleeve flange).  Calculation below in main().

# ══════════════════════════════════════════════════════════════════════════════
# Assertions
# ══════════════════════════════════════════════════════════════════════════════

# CORE CONSTRAINT: bumps must protrude past body in +X (rib direction)
assert STUB_OUTER_X >= BODY_X_FRONT + MIN_PROTRUSION_X, (
    f"+X protrusion: bump apex X = {STUB_OUTER_X}mm must exceed body +X "
    f"edge = {BODY_X_FRONT}mm by ≥{MIN_PROTRUSION_X}mm"
)
# Bumps must also protrude (or match) in ±Y at the contact line
assert STUB_OUTER_Y >= BODY_HALF_WIDTH, (
    f"±Y protrusion: bump outer Y = {STUB_OUTER_Y}mm < body half-width "
    f"= {BODY_HALF_WIDTH}mm — body would shadow bump in Y"
)
# M4 bolt walls
assert BODY_BACK_EXTENT >= M4_BOLT_CLEARANCE_D / 2 + FDM_WALL_PREF, (
    f"body −X wall: {BODY_BACK_EXTENT}mm < bolt R + {FDM_WALL_PREF}mm"
)
assert BODY_HALF_WIDTH >= M4_BOLT_CLEARANCE_D / 2 + FDM_WALL_PREF, (
    f"body ±Y wall: {BODY_HALF_WIDTH}mm < bolt R + {FDM_WALL_PREF}mm"
)
# Body height enough to reach the rib's contact zone
assert BODY_HEIGHT >= 7.0, (
    f"body Z height {BODY_HEIGHT}mm < 7mm — won't span violin rib"
)
# Body must extend far enough in −X to fully support the upstand's footprint
# (so the upstand doesn't overhang into thin air — printable without supports).
_UPSTAND_MINUS_X = UPPER_STEM1_LEN / 2 + UPPER_STEM1_OFFSET   # = 6.0
assert BODY_BACK_EXTENT >= _UPSTAND_MINUS_X, (
    f"body −X extent {BODY_BACK_EXTENT}mm < upstand −X reach "
    f"{_UPSTAND_MINUS_X}mm — upstand cap would overhang, requires supports"
)
# Upstand must match the upper_sleeve stem in X/Y (same stadium fits same slot)
assert CARRIAGE_UPSTAND_HEIGHT > 0, (
    f"CARRIAGE_UPSTAND_HEIGHT = 0 — no rotation lock"
)
assert CARRIAGE_UPSTAND_HEIGHT < SHOE_T, (
    f"CARRIAGE_UPSTAND_HEIGHT {CARRIAGE_UPSTAND_HEIGHT}mm ≥ SHOE_T {SHOE_T}mm "
    f"— upstand would protrude through the top of the shoe"
)
# Achievable purfling range covers typical 2–8 mm
assert PURFLING_MIN <= 2.0, (
    f"min purfling = {PURFLING_MIN:.2f}mm > 2mm — increase STUB_X_OFFSET"
)
assert PURFLING_MAX >= 8.0, (
    f"max purfling = {PURFLING_MAX:.2f}mm < 8mm — decrease STUB_X_OFFSET"
)
# Bumps must not collide with the bit shaft at the slot's max-forward position
assert BUMP_TO_BIT_CLEARANCE > 0, (
    f"bump-to-bit clearance = {BUMP_TO_BIT_CLEARANCE:.2f}mm ≤ 0 — "
    f"bumps would crash into the bit at slot max-forward. Reduce STUB_X_OFFSET."
)
# Sagitta sanity
assert SAGITTA_VARIATION < 1.0, (
    f"sagitta variation {SAGITTA_VARIATION:.2f}mm > 1mm — bearings too far apart"
)

OUT = Path(__file__).parent / "out"


# ══════════════════════════════════════════════════════════════════════════════
# Geometry
# ══════════════════════════════════════════════════════════════════════════════

def build_slider_carriage():
    """Single solid carriage: body with integrated bump perimeter, plus an
    upstand on top that engages the slot bottom for rotation lock."""

    # ── Body — rectangle, full height z = 0 → −BODY_HEIGHT ───────────────────
    body = Pos(BODY_CENTRE_X, 0, 0) * Box(
        BODY_LEN, BODY_WIDTH, BODY_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )

    # ── Two bump cylinders — half-inside / half-outside the rectangle ────────
    for sign_y in (+1, -1):
        bump = Pos(STUB_X_OFFSET, sign_y * STUB_Y, 0) * Cylinder(
            STUB_R, BODY_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
        )
        body += bump

    # ── Upstand — stadium fitting the bottom of the shoe slot ────────────────
    with BuildSketch() as sk:
        SlotOverall(UPPER_STEM1_LEN, UPPER_STEM1_D)
    # Same X offset as the upper_sleeve stem (bolt at +X cap centre)
    upstand = Pos(-UPPER_STEM1_OFFSET, 0, 0) * extrude(
        sk.sketch, amount=CARRIAGE_UPSTAND_HEIGHT,
    )
    body += upstand

    # ── M4 clearance bore — top of upstand to bottom of body ──────────────────
    body -= Pos(0, 0, CARRIAGE_UPSTAND_HEIGHT + 0.05) * Cylinder(
        M4_BOLT_CLEARANCE_D / 2, TOTAL_HEIGHT + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MAX),
    )

    return body


def main():
    carriage = build_slider_carriage()

    OUT.mkdir(exist_ok=True)
    export_step(carriage, str(OUT / "slider_carriage.step"))
    export_stl(carriage,  str(OUT / "slider_carriage.stl"))

    # Recommended M4 bolt length:
    # span = body bottom (-BODY_HEIGHT) → bottom of captive nut in upper_sleeve flange
    # Bottom of nut ≈ SHOE_T + UPPER_TOP_FLANGE_T − M4_NUT_POCKET_T = 11 + 5 − 3.5 = 12.5
    bolt_span = BODY_HEIGHT + 12.5

    print("Slider carriage (single integrated unit):")
    print(f"  Body: full-height {BODY_LEN}(X) × {BODY_WIDTH}(Y) × {BODY_HEIGHT}(Z) mm")
    print(f"        + 2 half-circle bumps (ø{STUB_OD}, full height) at "
          f"X=+{STUB_X_OFFSET}, Y=±{STUB_Y}")
    print(f"        bumps protrude {STUB_OUTER_X - BODY_X_FRONT:.1f}mm past body +X edge")
    print(f"  Upstand on top: stadium {UPPER_STEM1_LEN}×{UPPER_STEM1_D}, "
          f"{CARRIAGE_UPSTAND_HEIGHT}mm tall — rotation-locked by slot bottom")
    print(f"  Sagitta variation at waist (R={R_MIN}mm): {SAGITTA_VARIATION:.2f}mm")
    print(f"  Achievable purfling range: "
          f"{PURFLING_MIN:.2f}mm to {PURFLING_MAX:.2f}mm")
    print(f"  Bump-to-bit (ø{BIT_OD}) clearance at slot max-forward: "
          f"{BUMP_TO_BIT_CLEARANCE:.2f}mm")
    print(f"  Required M4 bolt length: ≥ {bolt_span:.1f}mm "
          f"(use M4 × 25 or longer)")
    print(f"Exported slider_carriage.{{step,stl}} to {OUT}")


if __name__ == "__main__":
    main()
