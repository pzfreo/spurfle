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

- Retract mechanism: servo, solenoid, or linear actuator? (speed vs. precision)
- MCU platform: to be decided via ADR
- Fixed mounting type: bench clamp, dedicated stand, or vacuum base?
- Centre force sensor range: violin edge contact estimated 1–20 N — to confirm by measurement
- Re-engagement countdown duration: 3–5 s suggested — to confirm with use
- Centre roller OD: must fit between outer rollers within 20mm span

**Decided** (see `docs/adr/`):
- ADR-001: Load cell + HX711 for centre force measurement
- ADR-002: Three-roller contact head — fixed centre + spring-loaded outer pair

## Key constraints (from manual jig)

- Dremel 3/4"-12 UN thread mount
- Shoe sits flat on work at z=0
- Cutter depth set by plate-to-shoe gap
