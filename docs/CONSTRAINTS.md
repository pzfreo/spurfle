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

### C-005 — Inter-roller gap from touch-point span and roller OD

Roller design (decided): 7mm OD nylon roller, 1.5mm steel pin axle.
Touch-point span (decided): 20mm between outer roller touch points.
Roller axis is **vertical**; OD is in the horizontal plane; roller height is
the axial (vertical) dimension that spans the instrument edge profile.

The span is built up as:

```
span = 2 × (roller_OD + gap)
```

Each side contributes one full roller diameter (centre roller radius + outer
roller radius) plus one gap. Rearranging:

```
gap = span/2 − roller_OD = 10 − 7 = 3 mm
```

- **Constraint:** gap ≥ 1mm (minimum clearance between roller bodies)
- **Drives:** for a fixed span, max roller OD = span/2 − 1 = 9mm;
  for a fixed roller OD, min span = 2 × (roller_OD + 1) = 16mm
- **Status:** satisfied — 7mm OD, 20mm span gives 3mm gap ✓
- **Code:** assert in `mechanics/contact_head.py`

  ```python
  assert ROLLER_GAP >= 1.0, (
      f"Rollers overlap: gap={ROLLER_GAP}mm with OD={ROLLER_OD}mm, span={TOUCH_SPAN}mm"
  )
  ```

### C-011 — Holder wall at pin: structural adequacy vs roller clearance

The roller holder (two stadium-shaped ASA printed end pieces, one above and one
below the roller) grips the pin at the semicircular ends. The holder OD at the
pin must satisfy two opposing requirements:

- **Lower bound** (structural): FDM ASA minimum reliable wall = 1.2mm;
  preferred 1.5mm. Holder OD ≥ pin_OD + 2 × 1.5mm = 1.5 + 3.0 = **4.5mm**
- **Upper bound** (clearance): holder must not protrude beyond the roller OD
  or it contacts the work before the roller does.
  Holder OD < roller_OD → holder OD < **7mm**

Decided value: holder OD at pin = **4.5mm** (wall = 1.5mm). Roller protrudes
1.25mm beyond holder on each side — roller always contacts the work first.

- **Code:** assert in `mechanics/contact_head.py`

  ```python
  assert HOLDER_PIN_OD >= PIN_D + 2 * 1.2, "Holder wall too thin — will fail in FDM"
  assert HOLDER_PIN_OD < ROLLER_OD, "Holder overhangs roller — will contact work"
  ```

### C-012 — Holder plate thickness (axial bearing depth)

The holder plate thickness (in the direction parallel to the pin axis = vertical
in 3D) determines the bearing length available to resist lateral loads on the
pin. Failure mode is not wall cracking under normal load but rather shock
loading if the assembly snags mid-operation.

Bearing stress = F / (pin_D × plate_thickness).  
FDM ASA conservative bearing strength ≈ 25 MPa (accounts for layer adhesion).

| Load scenario | Force | Min thickness needed |
|---|---|---|
| Spring contact (outer) | ~2 N | < 0.1 mm |
| Load cell max (centre) | 50 N | 1.3 mm |
| Snag/shock estimate | ~100 N | 2.7 mm |

- **Decided:** holder plate thickness = **3–4 mm** (comfortable margin over shock
  estimate; printable without supports when bore is vertical)
- **Print orientation constraint:** bore axis must be vertical (Z-axis) so
  bore walls are formed as complete circular rings per layer, not bridging
- **Code:** assert in `mechanics/contact_head.py`

  ```python
  assert HOLDER_THICKNESS >= 3.0, "C-012: holder too thin for shock loads"
  ```

### C-013 — Pin axial retention

A running fit (+0.2mm clearance) in a through-bore provides zero axial
retention. The decided approach avoids this entirely by using **blind pockets**:
neither holder plate has a through-bore. The axle sits in a 2mm blind pocket in
each plate's inner face; the outer face is solid.

- **Requirement:** axle must not be able to slide axially and release the roller
- **Decided approach:** blind pockets in both holder plates. Axle is captive by
  geometry — no fasteners, no cross-holes, no wire clips required.
  - Axle length = 2 × pocket depth + roller height = 2 + 10 + 2 = 14mm
  - Pocket depth = 2mm (leaving 1.5mm solid wall on outer face)
- **Code:** `mechanics/contact_head.py` — `POCKET_DEPTH`, assertion
  `POCKET_DEPTH < HOLDER_T`
- **Note:** the upper plate is a removable cap (assembly sequence: lower plate →
  axle → roller → upper plate). Attachment method for the upper plate to the
  housing is TBD pending overall housing design.

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
