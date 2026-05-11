# Purfling Cutter — Design Spec (v0.5)

A 3D-printed jig that holds a Dremel rotary tool over a stringed-instrument
top so a cutter bit can rout a constant-distance channel from the edge,
following the body's perimeter via a bearing.

This document describes the **as-built** design in `cutter.py`. Constant
names below match constants in the source.

## Parts

Four printed parts plus a sourced bearing, an M4 bolt, an M4 hex nut, and
two M6 flat-head bolts.

| Part            | Function                                                                 | Source                  |
|-----------------|--------------------------------------------------------------------------|-------------------------|
| `plate`         | Holds the Dremel via a 3/4"-12 UN internal thread. Two M6 hex nut pockets in the top face accept captive nuts; M6 bolts rise from the shoe through the standoff and plate into the nuts. No longitudinal channel. | `build_plate()` |
| `shoe`          | Stadium-shaped body sitting flat on the work (z=0–SHOE_T). Front is a half-stadium snout (the only contact patch). Two M6 flat-head bolt holes with Ø12 × 4 mm countersinks on the shoe bottom accept the bolts (heads flush at z=0). Stadium-shaped bearing slot in the middle. | `build_shoe()` |
| `upper_sleeve`  | Stem 1 + top flange with captive M4 hex nut (drops in from above).      | `build_upper_sleeve()`  |
| `lower_sleeve`  | Bottom flange + bore stem (no step). Bearing slides onto stem freely.   | `build_lower_sleeve()`  |
| `washer`        | Flat ring (Ø14 × 1.5 mm). Sits on bearing inner race top below shoe; provides thrust surface. | `build_washer()` |
| 608 bearing     | Edge follower (Ø22 OD × Ø8 bore × 7 mm).                                | sourced                 |
| M4 bolt         | Clamps bearing sleeve from below into upper sleeve's captive nut.        | sourced (M4 × ~25)      |
| M4 hex nut      | Captive in upper sleeve top flange (drops in from above).               | sourced (7 mm AF × 3.2) |
| `standoff`      | Single stadium-shaped spacer spanning both M6 bolt positions. Sits on shoe top face; sets the plate-to-shoe gap to `STANDOFF_H`. Two M6 clearance bores. | `build_standoff()` |
| M6 flat-head bolt × 2 | Rises from shoe through standoff and plate into captive nut; clamps plate to shoe at fixed gap. | sourced (M6 × 45 mm flat-head) |

## Coordinate system

Shoe-local frame is the world frame for the assembly.

- **+X**: long axis of the shoe (surround at +X end, standoffs at −X end).
- **+Y**: short axis (width).
- **+Z**: up. **z = 0 is the bottom face of the shoe**, which rests on the
  workpiece. Shoe body spans z = 0 to z = `SHOE_T` (= 11). The surround snout
  spans z = 0 to z = `SURROUND_HEIGHT` (= 4); the rest of the front is cut away.

## Shoe layout

```
TOP VIEW (+Z down):
+-------------------------------------------------------+
|  (cs)   (cs)    [====slot====]         ( half-stad )  |
+-------------------------------------------------------+
  bolt#2  bolt#1    bearing channel          surround
  (back)             (upper sleeve           (bit hole)
                      stem slides)

SIDE VIEW:
+----- bolt holes w/ countersinks ------+-- snout ---+
|  v    v    [ stadium slot ]           |   snout    |  z = SHOE_T = 11
|  v    v                               |            |  z = SURROUND_HEIGHT = 4
|_______________________________________+            |  z = 0 (work surface)
  bolt heads flush at z=0                            |
                     bearing top ≈ z = -WASHER_T = -1.5
```

1. **Surround** (+X end). Half-stadium snout: flat back at the surround region
   edge, semicircular front (radius `SURROUND_BOSS_D`/2 = 8). Height `SURROUND_HEIGHT`
   = 4 mm. Only intentional contact patch with the work. Bit hole at `SURROUND_X`.
2. **Bearing channel** (middle). Stadium slot through full shoe thickness.
3. **Standoff bolt holes** (−X end). Two M6 flat-head bolt holes with
   Ø12 × 4 mm countersinks on the shoe bottom (z=0 face), bolt heads flush.

## Plate-to-shoe attachment

Two M6 flat-head bolts rise from beneath the shoe (heads recessed in the
shoe bottom countersinks), through the shoe, and into M6 heat-set inserts
in the plate bottom face. The plate's `THREAD_X` bore aligns with the shoe's
`SURROUND_X` bit hole; the insert positions are derived from the shoe's
`STANDOFF_X_INNER` / `STANDOFF_X_OUTER` adjusted by this offset.

## Bearing housing assembly

Unchanged from v0.4. See the v0.4 stack and clamping description.

### Stack (bottom → top)

```
M4 bolt head
  → lower_sleeve bottom flange
  → lower_sleeve bore stem (full bearing bore)
  → washer (on bearing inner race top; contacts shoe bottom)
  → shoe body (clamped between washer below and upper flange above)
  → upper_sleeve Stem 1 (in slot)
  → upper_sleeve top flange (captive M4 nut)
```

### Assembly sequence

1. Bearing slides down onto lower sleeve bore stem.
2. Washer placed on bearing inner race top.
3. Sub-assembly raised to shoe slot from below.
4. Upper sleeve dropped through slot from above.
5. M4 bolt inserted from below, threaded into captive hex nut.

## Dimensions (mm)

### Shared

| Constant              | Value | Notes                                      |
|-----------------------|------:|--------------------------------------------|
| `BEARING_OD`          | 22.0  | 608 outer diameter                         |
| `BEARING_THK`         | 7.0   | 608 thickness                              |
| `M4_BOLT_CLEARANCE_D` | 4.5   | M4 clearance for bearing clamp bolt        |
| `M4_NUT_AF`           | 7.0   | M4 hex nut across-flats                    |
| `M4_NUT_T`            | 3.2   | M4 hex nut thickness                       |
| `M4_NUT_POCKET_AF`    | 7.2   | Hex pocket AF (0.1 mm clearance/flat)      |
| `M4_NUT_POCKET_T`     | 3.5   | Hex pocket depth                           |
| `M6_BOLT_CLEARANCE_D` | 6.5   | M6 standoff bolt shank clearance           |
| `COUNTERSINK_D`       | 12.0  | M6 flat-head OD at shoe bottom             |
| `COUNTERSINK_DEPTH`   | 4.0   | Countersink depth (head height)            |

### Plate

| Constant            | Value | Notes                                                                 |
|---------------------|------:|-----------------------------------------------------------------------|
| `PLATE_L`           | derived | `SURROUND_X − STANDOFF_X_OUTER + PLATE_W/2 + PLATE_BACK_WALL`. Parametric: always just long enough to span thread bore (+X semicircle) to outer nut pocket with ≥6 mm wall from hole edge. Currently ≈82.25 mm. |
| `PLATE_BACK_WALL`   | 10    | Outer nut pocket centre → plate back edge (gives ≈6.15 mm wall from hole edge). |
| `PLATE_W`           | 30    | Y                                                                     |
| `PLATE_T`           | 11    | Z; 5.2 mm nut pocket + 5.8 mm solid below.                           |
| `THREAD_MAJOR`      | 19.05 | Dremel 3/4"-12 UN major Ø                                            |
| `THREAD_PITCH`      | 25.4/12 | ≈ 2.117 mm                                                          |
| `THREAD_X`          | derived | = PLATE_L/2 − PLATE_W/2; bore centre on +X semicircle. Currently ≈26.125 mm. |
| `M6_NUT_AF`         | 10.0  | M6 hex nut across-flats (ISO 4032)                                   |
| `M6_NUT_T`          | 5.0   | M6 hex nut thickness                                                  |
| `M6_NUT_POCKET_AF`  | 10.2  | Pocket AF (0.1 mm clearance per flat)                                |
| `M6_NUT_POCKET_T`   | 5.2   | Pocket depth (0.2 mm clearance on nut thickness); entered from plate top face. |

Insert X positions are derived in `build_plate()` from shoe standoff positions
adjusted by `SURROUND_X − THREAD_X` (the plate-to-shoe X alignment offset).

### Shoe

| Constant           | Value   | Notes                                                                  |
|--------------------|--------:|------------------------------------------------------------------------|
| `SHOE_W`           | 30      | Y. Matches PLATE_W.                                                    |
| `SHOE_T`           | 11      | Z thickness.                                                           |
| `SURROUND_HEIGHT`  | 4       | Z height of surround snout (z=0 to z=4).                              |
| `SURROUND_WALL`    | 4       | Radial material around bit hole.                                       |
| `SURROUND_BOSS_D`  | 14      | Derived: BIT_HOLE_D + 2·SURROUND_WALL.                                |
| `SURROUND_LEN`     | 14      | X extent of surround region (visible). Rectangle portion = SURROUND_LEN/2 = 7 outside the body. |
| `SURROUND_OVERLAP` | 2       | Snout rectangle extends this far back into the shoe body past the front cut plane so the union is a single solid (no 0.1 mm gap from cut tolerance; prints as one piece). |
| `SURROUND_FILLET_OUT` | 3.4  | Fillet on outer bottom perimeter of snout. Max before colliding with the inner fillet at the cap (SURROUND_WALL − bit_r − SURROUND_FILLET_IN − margin). |
| `SURROUND_FILLET_IN`  | 0.5  | Fillet on bit hole bottom edge (smooth bit entry). |
| `BIT_HOLE_D`       | 6       | Router bit clearance.                                                  |
| `SLOT_LEN`         | 18      | Bearing slot X length. Gives bearing-edge-to-bit-edge gap of 1.25–13.25 mm and a 37.25 mm cantilever (inner bolt → bit center). `max_gap = SLOT_LEN − 4.75`; `cantilever = 19.25 + SLOT_LEN`. |
| `SLOT_W`           | 6.5     | Slot Y width. Clears UPPER_STEM1_D=6 with ~0.25 mm/side.              |
| `END_WALL_FRONT`   | 3       | Surround edge → slot edge.                                             |
| `SLOT_END_WALL`    | 6       | Slot edge → standoff bolt near edge (increased from 3 so Ø12 countersink clears slot by ≥3 mm). |
| `END_WALL_BACK`    | 10      | Outer bolt center → back of shoe (increased from 6 to keep countersink inside shoe end). |
| `STANDOFF_BOLT_D`  | 6.5     | = M6_BOLT_CLEARANCE_D.                                                |
| `STANDOFF_SPAN`    | 20      | Bolt-center to bolt-center.                                            |
| `SHOE_L`           | 74.25   | Derived. Grew from 71.25 when SLOT_LEN went 15 → 18.                   |

**Countersink geometry check**: with SLOT_END_WALL = 6, the distance from inner
bolt center to slot back edge = 6 + 6.5/2 = 9.25 mm. Countersink radius = 6 mm.
Gap from countersink edge to slot = 3.25 mm ✓. With END_WALL_BACK = 10, the gap
from outer countersink edge to shoe end = 10 − 6 = 4 mm ✓.

### Upper sleeve

| Constant             | Value | Notes                                               |
|----------------------|------:|-----------------------------------------------------|
| `UPPER_STEM1_D`      | 6     | Stadium stem Y-width (fits SLOT_W=6.5 with ~0.25 mm/side). Minimum cross-section; unchanged from circular version. |
| `UPPER_STEM1_LEN`    | 9     | Stadium stem X-length. Flat face on the −X (bolt) side keys into the slot wall and prevents rotation. |
| `UPPER_STEM1_OFFSET` | (UPPER_STEM1_LEN − UPPER_STEM1_D) / 2 = 1.5 | Stadium is shifted −X by this amount so the M4 hole sits at the +X cap centre. The +X (bit-side) edge of the stadium therefore matches the original circle's +X edge, preserving the minimum bearing-to-bit distance. All extra material is added on the bolt side. |
| `UPPER_TOP_FLANGE_D` | 13    | Sits on shoe body top.                              |
| `UPPER_TOP_FLANGE_T` | 5     | 1.5 mm solid base + 3.5 mm nut pocket from top.    |

### Lower sleeve

| Constant         | Value | Notes                                                |
|------------------|------:|------------------------------------------------------|
| `LOWER_FLANGE_D` | 14    | Below bearing inner race.                            |
| `LOWER_FLANGE_T` | 1.5   |                                                      |
| `LOWER_STEM_D`   | 7.8   | Through 608 bore (Ø8), full height.                  |
| `LOWER_STEM_L`   | 7.0   | = BEARING_THK; fills bore end-to-end.                |

### Standoff

| Constant        | Value | Notes                                                                 |
|-----------------|------:|-----------------------------------------------------------------------|
| `STANDOFF_H`      | 23    | Height (shoe top → plate bottom). Sets the plate-to-shoe gap.       |
| `STANDOFF_CLEARANCE` | 2  | Total margin from hard limits (1 mm each end).                      |
| `STANDOFF_W`      | derived | `min(shoe-end limit, flange limit) − STANDOFF_CLEARANCE = 16 mm`. Constrained so the −X end cap stays 1 mm inside the shoe back wall and the +X end cap stays 1 mm clear of the upper sleeve flange **at maximum bearing-to-bit distance** (bearing slid to −X slot limit, `BEARING_X_MIN`). Wall ≈ 4.5 mm each side of bolt hole. Stadium length = STANDOFF_SPAN + STANDOFF_W = 36 mm. |
| `STANDOFF_HOLE_D` | M6_BOLT_CLEARANCE_D + 0.5 = 7.0 | Bolt clearance in standoff; 0.5 mm extra over shoe/plate holes for easy bolt passage. |

Bolt holes centred at ±`STANDOFF_SPAN/2` (= ±10 mm) from the standoff's geometric centre, which sits at `(STANDOFF_X_INNER + STANDOFF_X_OUTER) / 2` in shoe coords.

### Washer

| Constant    | Value | Notes                                                          |
|-------------|------:|----------------------------------------------------------------|
| `WASHER_OD` | 14    | Contacts inner race only; clears outer race ID (~Ø16).         |
| `WASHER_T`  | 1.5   | Thrust thickness; bearing top at z = −WASHER_T = −1.5.        |

## Build & verify

```sh
uv run python cutter.py
```

Produces in `out/`: `plate.{step,stl}`, `shoe.{step,stl}`,
`upper_sleeve.{step,stl}`, `lower_sleeve.{step,stl}`, `washer.{step,stl}`.

Visual checks in the viewer:

- Plate has no longitudinal slot. Two insert holes (Ø7.7, through-plate) with
  entry chamfers visible on the bottom face.
- Shoe: half-stadium snout at the +X end. Two countersunk bolt holes (Ø12 at
  shoe bottom, narrowing to Ø6.5 at 4 mm depth) in the −X region.
- Countersink edges clear the slot ends and shoe back wall.
- Upper sleeve: Stem 1 in slot, flange on shoe top, hex nut pocket upward.
- Washer flat ring between bearing inner race top and shoe bottom (z = −1.5 to 0).
- M4 clearance line unobstructed through sleeve stack.

## Out of scope (next iterations)

- Physical standoffs are replaced by M6 flat-head bolts; no separate standoff part.
- M4 bolt head choice (socket cap vs. thumbscrew).
- Alignment features between shoe and plate.
