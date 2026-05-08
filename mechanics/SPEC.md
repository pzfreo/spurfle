# Mechanics — Contact Head Spec

Design decisions for the three-roller contact head. Status: design phase,
no code written yet. This spec and any future `contact_head.py` are a coupled
pair — update both in the same commit.

## Roller design

| Parameter | Value | Notes |
|-----------|-------|-------|
| Roller material | Nylon (FDM printed) | Won't mar instrument finish |
| Roller OD | 7mm | Horizontal plane; contacts instrument edge |
| Roller axis | Vertical | OD is in the horizontal plane; height is the axial dimension |
| Roller height (axial) | 10mm | Spans violin 3mm overhang with margin; TBD for viol da gamba |
| Pin (axle) | 1.5mm steel × 14mm | Piano wire or equivalent; captive by geometry (see below) |
| Pin bore clearance | +0.2mm → 1.7mm bore | Running fit in roller and holder pockets |
| Roller wall thickness | (7 − 1.7) / 2 = 2.65mm | Adequate for FDM |

## Holder design

Two ASA printed plates: a **lower plate** (L-shaped bracket, the main structure)
and an **upper plate** (short removable cap). The roller and axle sit between them.

| Parameter | Value | Constraint |
|-----------|-------|-----------|
| Holder OD at pin | 4.5mm | Must be < roller OD (7mm) so roller contacts work first |
| Holder wall at pin | 1.5mm | FDM minimum structural wall (see C-011) |
| Holder plate thickness (axial) | 3.5mm | Bearing depth for axle; mid of 3–4mm range (C-012) |
| Holder material | ASA | Dimensionally stable, good layer adhesion |
| Print orientation | Bore axis vertical (Z) | Bore formed as circular rings per layer — strongest for lateral loads |

The roller (7mm) protrudes 1.25mm beyond the holder (4.5mm) on each side —
the holder face never reaches the work.

### Lower plate (L-shaped bracket)

The lower plate is the primary structural part. It has two sections:

1. **Horizontal base** — extended stadium shape, 20mm body beyond pin centre.
   Blind axle bore (2mm deep) from inner (top) face; outer (bottom) face solid.

2. **Vertical wall** — rises from the back of the horizontal base, starting
   1.0mm clear of the roller surface (at X = roller_R + 1.0mm = 4.5mm from
   pin centre, see C-014). Wall height = roller height (10mm), so its top face
   is flush with the bottom of the upper plate, providing direct support.

The vertical wall + horizontal base form a J-shape when viewed from the side.

### Upper plate (removable cap)

Shorter stadium shape, 10mm body beyond pin centre (same width as lower plate).
Blind axle bore (2mm deep) from inner (bottom) face; outer (top) face solid.
Far end rests on top of the lower plate's vertical wall. Attachment method TBD
pending overall housing design.

### Pin retention

The axle is retained by **blind pockets** in both holder plates — the bore does
not go all the way through either plate. Each plate has a 2mm blind bore from
its inner face only; the outer face is solid. The axle (14mm = 2mm pocket +
10mm roller + 2mm pocket) is fully captive by geometry: no cross-holes, no wire
clips, no fasteners required.

Assembly sequence: drop axle into lower plate pocket → slide roller onto axle
from above → place upper plate on top, capturing axle in its pocket.

See C-013 (updated).

## Span geometry

Three rollers: fixed centre + spring-loaded outer pair.
Touch-point span between outer rollers: **20mm**.

```
span = 2 × (roller_OD + gap)
  20 = 2 × (7 + gap)
 gap = 3mm
```

Outer roller centres at ±10mm from centre roller. Gap between adjacent
roller bodies = 3mm (see C-005).

## Centre roller — force sensing

The centre roller is fixed in position but its holder must float slightly
to press against the load cell. Design TBD. Options under consideration:

- Holder slides in a channel in the main body, bears directly on a button/disc
  load cell face
- Holder bears via a small plunger to isolate the load cell from side loads

Preferred load cell form: button/disc compression type, ~15–20mm diameter,
rated 0–50N, paired with HX711 (ADR-001). Not yet selected.

## Outer rollers — tangency sensing

Spring-loaded, Hall effect displacement sensors (ADR-002).
Spring travel required: ≥ 3mm (sagitta variation across violin body, see C-004).
Spring rate and preload: TBD — must be light enough not to mar instrument finish,
stiff enough to maintain contact on convex bouts.

## Plan view diagram

`mechanics/drawings/plan_view.py` — parametric Python/matplotlib script.
Run `python mechanics/drawings/plan_view.py` to regenerate `plan_view.svg`.
Assertions in the script enforce C-005 and C-011 at render time.

## What this spec does not cover

- Overall housing geometry and dimensions
- Mounting of the contact head to the retract carriage
- Height adjustment for violin vs viol da gamba (different edge heights)
- Spring selection (rate, preload, OD)
- Specific load cell part number

These will be added as the design develops. See `docs/CONSTRAINTS.md` for
the full constraint chain.

## Build command

```sh
uv run python mechanics/contact_head.py
```

Produces in `mechanics/out/`: `roller.{step,stl}`, `lower_plate.{step,stl}`,
`upper_plate.{step,stl}`. Assertions fire at import time — a clean run means
all constraints are satisfied.
