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
| Pin (axle) | 1.5mm steel | Piano wire or equivalent |
| Pin bore clearance | +0.2mm → 1.7mm bore | Running fit |
| Roller wall thickness | (7 − 1.7) / 2 = 2.65mm | Adequate for FDM |

## Holder design

Two stadium-shaped ASA printed end pieces, one above and one below the roller.
Each piece has a 1.5mm bore at the centre of the semicircular end to accept
the pin. The two pieces are held apart at the correct roller height.

| Parameter | Value | Constraint |
|-----------|-------|-----------|
| Holder OD at pin | 4.5mm | Must be < roller OD (7mm) so roller contacts work first |
| Holder wall at pin | 1.5mm | FDM minimum structural wall (see C-011) |
| Holder plate thickness (axial) | 3–4mm | Bearing depth for pin; see C-012 |
| Holder material | ASA | Dimensionally stable, good layer adhesion |
| Print orientation | Bore axis vertical (Z) | Bore formed as circular rings per layer — strongest for lateral loads |

The roller (7mm) protrudes 1.25mm beyond the holder (4.5mm) on each side —
the holder face never reaches the work.

### Pin retention

A running fit (+0.2mm) gives no axial retention. Without positive retention the
pin can slide out under shock loading, releasing the roller near the cutter.
**Each pin end must be retained** by one of:

- A 1mm cross-drilled hole with a bent wire clip or split pin (preferred —
  easy to print a slot, no special tooling)
- A light press-fit collar printed into the holder (2nd option)

See C-013.

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

Once `contact_head.py` exists: `python mechanics/contact_head.py`
