# Spurfle — Safe Purfling Device

## What we're building

A fixed jig that routes purfling channels around stringed-instrument tops and
backs, replacing the hand-held manual approach with a device that senses edge
contact and automatically retracts the cutter when contact is lost. Designed
for both violin family (plate overhang edge) and viol da gamba (full rib edge).

## Problem statement

Purfling is a decorative inlay channel routed around the perimeter of a
stringed-instrument top or back, typically 1.5–2 mm wide and a few mm deep.
The manual jig (see `manual/`) holds a Dremel cutter at a fixed distance from
the instrument edge using a bearing follower, and at a fixed depth via the
plate-to-shoe gap.

The manual approach has two failure modes that can ruin months of work:

**1. Edge slip — catastrophic overcut**
If the bearing loses contact with the edge (e.g. the operator slips or the jig
lifts), the cutter no longer has a distance reference and ploughs straight
through the top or back. There is no recovery from a deep overcut across the
plate.

**2. Tangency error — inconsistent channel width**
The bearing follower only maintains correct distance when the jig is held
tangential to the edge curve. If the jig rotates off-tangent (common on tight
curves such as the waist or bouts), the effective cutter-to-edge distance
varies, producing a ragged or wavy purfling line.

## Solution overview

**Invert the relationship between jig and instrument.** Instead of the operator
moving the jig along a held violin, the **jig is fixed** and the operator feeds
the **violin edge against it**. The jig senses edge contact continuously and
retracts the cutter automatically if contact is lost.

Tangency is monitored by a three-roller contact head. The operator receives
real-time visual feedback and corrects angle by rotating the instrument.

## Contact head design

Three needle rollers, ~4mm OD, spaced within a 20mm total outer-to-outer span:

```
   outer-L    centre    outer-R
      O    |    O    |    O
   spring  |  fixed  |  spring
   + disp  | + force |  + disp
   sensor  |  sensor |  sensor
```

| Roller | Mounting | Sensor | Purpose |
|--------|----------|--------|---------|
| Centre | Fixed | Load cell + HX711 (see ADR-001) | Contact detection — sole retract trigger |
| Outer left | Spring-loaded | Displacement (Hall effect) | Tangency guidance |
| Outer right | Spring-loaded | Displacement (Hall effect) | Tangency guidance |

**Why needle rollers:** Ball plungers are unreliable against the thin (~3mm)
violin overhang edge — insufficient surface height to retain the ball. Needle
rollers constrained in slots track both the 3mm violin overhang and the full
viol da gamba rib reliably.

**Why separate sensor types:** The outer rollers move naturally with convex and
concave curves (sagitta variation ~3mm spring travel required across the full
violin body outline). Their position cannot be used to infer whether the centre
roller is in contact — that requires an independent force sensor on the centre.

**Sagitta note:** At 10mm from centre to each outer roller, the spring travel
needed to follow the full range of violin curvature (convex bouts R≈100mm to
concave waist R≈25mm) is approximately 2.6mm. Springs must accommodate this
without bottoming out or losing preload.

## Control logic

Two independent systems sharing the same firmware:

### Safety system (centre force sensor)

```
State: ARMED ←→ RETRACTED
```

- **ARMED → RETRACTED**: any of the three sensors enters RED.
  Cutter retracts immediately.
- **RETRACTED → ARMED**: all three sensors return to GREEN and hold for the
  full countdown duration. Countdown provides auditory and visual warning
  so the operator can get both hands back on the instrument before the
  cutter descends. If any sensor drops below GREEN during countdown,
  countdown resets.

Force zones for centre sensor:

| Zone | Colour | Meaning |
|------|--------|---------|
| Good | Green | Contact confirmed — cut proceeds |
| Warning | Yellow | Force reducing — operator should increase pressure |
| Critical | Red | Contact unsafe — retract triggered |

### Tangency system (outer displacement sensors)

The differential between left and right outer roller displacements indicates
angular error. Each outer LED reports the magnitude of that differential:

| Zone | Colour | Meaning | Action |
|------|--------|---------|--------|
| Good | Green | Displacements equal — jig tangential | Cut proceeds |
| Warning | Yellow | Differential growing — jig drifting off-tangent | Operator rotates instrument |
| Critical | Red | Differential too large — cut geometry unsafe | Cutter retracts |

Which LED is more extended tells the operator which way to rotate the
instrument to re-equalise. Retract is triggered if either outer LED enters RED.

Re-engagement countdown only begins when **all three sensors** (centre force
and both outer differentials) are back in GREEN.

## Target instruments

| Instrument | Edge type | Contact height |
|------------|-----------|----------------|
| Violin / viola | Plate overhang | ~3mm |
| Viol da gamba | Full rib, no overhang | ~50–60mm |

Contact point height must be set correctly for each instrument type. The needle
roller geometry serves both; the 3mm violin overhang constrains the minimum
usable roller diameter.

## Operational scenarios

The device must support two distinct working scenarios determined by where the
maker is in the build process:

### Scenario 1 — plate on table (before assembly)
The top or back plate lies flat on the workbench before the body is assembled.
The jig shoe sits directly on the plate surface at z=0. This is the same
geometry as the manual jig. Gravity holds the shoe against the plate surface.

### Scenario 2 — assembled body in a stand (after assembly)
The assembled violin or viol is held horizontal in a cradle or stand above the
bench. The jig must be positioned so the shoe is level with the plate surface
of the elevated instrument.

**Prior art — guitar binding jigs:** Guitar makers use a gravity-fed vertical
linear slide for exactly this scenario. The jig hangs on the slide above the
instrument cradle; gravity pulls the shoe down onto the plate surface; no
manual height setting is required. The operator rotates the instrument in the
cradle to feed the edge against the jig.

Guitar binding jigs do not need a safety retract because the cut direction is
parallel to the plate (into the side of the body), so the cutter cannot
plough across the plate if the bearing slips. Violin and viol purfling cuts
into the plate from above, making edge slip catastrophic — this is why the
spurfle safety system is needed.

**Mounting approach for both scenarios:** gravity does the height work.
- Scenario 1: jig rests on plate surface by gravity
- Scenario 2: jig on vertical linear slide above instrument cradle, gravity
  pulls shoe onto plate surface

**Implication for retract mechanism:** gravity holds the jig down in both
scenarios. The retract mechanism must lift against gravity and must also
*control the descent* during re-engagement — gravity cannot be allowed to
bring the cutter down uncontrolled. The retract actuator holds position
throughout and manages both lift and controlled descent.

## System layers

| Layer | Description | Directory |
|-------|-------------|-----------|
| Manual jig | 3D-printed purfling router (baseline, no electronics) | `manual/` |
| Mechanics | Contact head, retract mechanism, fixed mounting | `mechanics/` |
| Electronics | PCB / circuit for sensors and actuator drive | `electronics/` |
| Firmware | MCU code: force reading, retract control, LED display | `firmware/` |

## Current state

- `manual/` — copied from purfel repo (working mechanical design)
- All other layers: design phase, not yet started

## Open questions

- Retract mechanism: decided — see ADR-003
- MCU platform: decided — see ADR-004
- Mounting: vertical linear slide + instrument cradle for scenario 2 — to be decided via ADR
- Centre force sensor range: violin edge contact estimated 1–20 N — to confirm by measurement
- Re-engagement countdown duration: 3–5 s suggested — to confirm with use
- Centre roller OD: must fit between outer rollers within 20mm span

**Decided** (see `docs/adr/`):
- ADR-001: Load cell + HX711 for centre force measurement
- ADR-002: Three-roller contact head — fixed centre + spring-loaded outer pair
- ADR-003: Stepper + lead screw Dremel carriage within gravity-fed floating frame
- ADR-004: RP2040 (Raspberry Pi Pico) as MCU platform

## Key constraints (from manual jig)

- Dremel 3/4"-12 UN thread mount
- Shoe sits flat on work at z=0
- Cutter depth set by plate-to-shoe gap
