# Spurfle — Physical Constraint Chains

## Purpose

This document captures the dependency chains between physical design decisions.
Each constraint states what it is, what drives it, and what it constrains
downstream. Where a constraint is enforced by an assertion in the model code,
the file and constant name are referenced.

The goal is to make the constraint chain explicit so that changing one dimension
surfaces its downstream effects, analogous to a type error or a failing test.

## Convention

In model code (`.py` files), derived dimensions must be **calculated**, never
typed as magic numbers. Every constraint between two values must have an
`assert` statement with a human-readable message:

```python
# Derived — do not edit directly, change the source values
HOUSING_DEPTH = SENSOR_DEPTH + MOUNT_CLEARANCE

# Constraint: sensor must fit inside housing
assert HOUSING_DEPTH <= SHOE_WALL_THICKNESS, (
    f"Sensor won't fit behind roller: need {HOUSING_DEPTH}mm, "
    f"wall is {SHOE_WALL_THICKNESS}mm"
)
```

Running `python <model>.py` is the test suite. A clean run = all constraints
satisfied.

---

## Contact head constraints

### C-001 — Sensor depth behind centre roller
- **Source:** load cell body depth + HX711 breakout depth + mounting clearance
- **Drives:** minimum shoe wall thickness behind centre roller
- **Status:** sensor not yet selected — TBD when load cell is chosen
- **Code:** `mechanics/contact_head.py` — `CENTRE_SENSOR_DEPTH`, `SHOE_WALL_MIN`

### C-002 — Sensor depth behind outer rollers
- **Source:** Hall effect sensor body depth + magnet clearance + mounting
- **Drives:** minimum housing depth behind each outer roller
- **Status:** sensor not yet selected — TBD
- **Code:** `mechanics/contact_head.py` — `OUTER_SENSOR_DEPTH`, `OUTER_HOUSING_DEPTH`

### C-003 — Outer roller span vs violin waist radius
- **Source:** outer-to-outer span ≤ 20mm (design decision, ADR-002)
- **Constraint:** both outer rollers must simultaneously contact the tightest
  violin curve (waist R ≈ 25mm). Half-chord (10mm) must be < waist radius.
  10mm < 25mm ✓ — satisfied by design
- **Drives:** maximum allowable outer span
- **Code:** assert in `mechanics/contact_head.py`

### C-004 — Outer roller spring travel
- **Source:** sagitta variation across full violin body outline —
  convex bouts (R≈100mm) to concave waist (R≈25mm) at 10mm half-span = 2.6mm
- **Drives:** spring must provide ≥ 3mm travel without bottoming or losing preload
- **Code:** `mechanics/contact_head.py` — `OUTER_SPRING_TRAVEL_MIN`

### C-005 — Centre roller OD vs outer roller span
- **Source:** outer-to-outer span = 20mm; centre roller is between the outer two
- **Drives:** centre roller OD must be < 20mm (so it fits between the outers)
- **Status:** roller OD TBD — to be confirmed
- **Code:** assert in `mechanics/contact_head.py`

---

## Retract mechanism constraints

### C-006 — Lead screw direction (kinematic)
- **Constraint:** lead screw must drive the Dremel carriage **upward** (away
  from shoe) on retract. The shoe defines z=0 and must never be displaced by
  the retract motion. Verify motor wiring and lead screw handedness at assembly.
- **Note:** this cannot be enforced by a model assertion — it must be verified
  physically. Captured here so it is not forgotten.

### C-007 — Lead screw stroke vs cutting depth range
- **Source:** maximum cutting depth (purfling channel depth ~5mm) + retract
  clearance (~5mm) = minimum useful stroke ~10mm
- **Drives:** lead screw length selection
- **Code:** `mechanics/carriage.py` — `STROKE_MIN`, assert stroke ≥ STROKE_MIN

### C-008 — Stepper holding torque vs Dremel carriage weight
- **Source:** Dremel weight ≈ 600g; T8 lead screw (8mm/rev); efficiency ~40%
- **Required torque:** ≈ 19 mN·m (well within NEMA 17 holding torque ~450 mN·m)
- **Status:** satisfied by component selection — no assertion needed, document only

---

## Frame and mounting constraints

### C-009 — Spring counterbalance vs instrument top contact force
- **Source:** total hanging weight (Dremel + carriage + frame + stepper)
- **Drives:** spring selection must reduce effective downforce to a safe range
  for instrument top contact (target: light positive contact, not damaging)
- **Status:** weights TBD until mechanical design progresses

### C-010 — Linear slide friction vs spring counterbalance
- **Constraint:** slide static friction must be less than the spring
  counterbalance force, otherwise the shoe will not follow the instrument
  surface under gravity
- **Status:** depends on slide selection — to be verified at build

---

## How to add a constraint

1. Assign the next C-NNN number
2. State: source, what it drives, current status, code reference
3. Add the corresponding assertion in the model `.py` file
4. If the constraint cannot be expressed as a code assertion (e.g. kinematic
   direction, assembly order), mark it **Note:** and explain why
