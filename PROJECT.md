# Spurfle — Safe Purfling Device

## Problem statement

Purfling is a decorative inlay channel routed around the perimeter of a
stringed-instrument top or back, typically 1.5–2 mm wide and a few mm deep.
The manual jig (see `manual/`) holds a Dremel cutter at a fixed distance from
the instrument edge using a bearing follower, and at a fixed depth via the
plate-to-shoe gap.

The manual approach has two failure modes that can ruin months of work:

**1. Edge slip — catastrophic overcut**
If the bearing loses contact with the edge (e.g. the user slips or lifts the
jig), the cutter no longer has a distance reference and ploughs straight through
the top or back. There is no recovery from a deep overcut across the plate.

**2. Tangency error — inconsistent channel width**
The bearing follower only maintains correct distance when the jig is held
tangential to the edge curve. If the jig rotates off-tangent (common on tight
curves such as the waist or bouts), the effective cutter-to-edge distance
varies, producing a ragged or wavy purfling line.

## Proposed solutions

### Problem 1 fix — fixed jig with force-monitored edge contact

Invert the relationship between jig and instrument: instead of the operator
moving the jig along a held violin, the **jig is fixed** and the operator
feeds the **violin edge against it**.

A force sensor measures the contact force between the violin edge and the
bearing follower. While force is above a threshold, the system knows the edge
is in contact and cutting can proceed. As soon as force drops below the
threshold — indicating the edge may be slipping away — the firmware retracts
the cutter upward (away from the work surface) before the edge actually
loses contact.

Key properties of this approach:
- **Safety guarantee from physics**: while contact force is present, the
  bearing is against the edge, geometry is correct, and slippage cannot
  occur. No slippage is possible without force first reducing.
- Retract is triggered by **force starting to drop** (onset of reduction,
  not zero crossing). This gives the full duration of the force-reduction
  curve — the time it takes the violin edge to physically move away — to
  complete the retract. Retract speed does not need to be extreme.
- **False positives are acceptable**: if the cutter retracts when it didn't
  need to (e.g. momentary light pressure at a curve), the operator simply
  re-engages by pressing the violin back against the bearing. Re-engagement
  must be easy and fast by design.
- The fixed mounting means the operator's hands control only the violin,
  not the jig — simpler motor task, less chance of jig movement
- The bearing follower still provides the lateral distance reference

Control logic:
- State: ARMED (cutter at depth) / RETRACTED (cutter raised)
- Each contact point independently reports: GREEN / YELLOW / RED
- Transition ARMED→RETRACTED: either contact point enters RED
- Transition RETRACTED→ARMED: both contact points return to GREEN, triggering
  a timed countdown with auditory and visual warning before cutter descends.
  Both hands are on the violin during cutting, so re-engagement is automatic
  but deliberately delayed. If either contact point drops below GREEN during
  countdown, countdown resets.

Open questions for this sub-system:
- What force range and resolution is needed? (violin edge contact is light —
  likely 1–20 N range)
- Rate-of-change trigger vs. absolute threshold — or both?
- What is the fixed mounting — bench clamp, dedicated stand, vacuum base?

### Problem 2 fix — dual-contact tangency sensing

Replace the single bearing follower with two bearing contact points spaced
closely together along the direction of travel. Both contact points measure
force independently.

**Geometry:** When both points register equal (or near-equal) force, the line
between them is tangential to the edge curve, the cutter is perpendicular to
the edge, and the cutter-to-edge distance is the designed nominal value
(maximum correct distance). When the jig is off-tangent, one contact point
carries more load than the other and/or the cutter is no longer perpendicular
— the effective cutter-to-edge distance reduces, producing an inconsistent
channel.

**Sensing:** Each contact point has its own three-zone LED indicator:

| Zone | Colour | Meaning | Action |
|------|--------|---------|--------|
| Good | Green | Force sufficient, contact confirmed | Cut proceeds |
| Warning | Yellow | Force dropping, still acceptable | Operator increases pressure |
| Critical | Red | Force below safe threshold | Cutter retracts automatically |

Two LEDs side by side (one per contact point) serve dual purpose:
- **Slip detection**: both LEDs showing green means safe to cut
- **Tangency guidance**: imbalance between the two LEDs tells the operator
  which way to rotate the violin to re-equalise contact force

**Spacing trade-off:** Contact points closer together work on tighter curves
(violin waist radius ~20–30 mm) but are less sensitive to small angular
errors. Points further apart give a stronger differential signal but may
fail to both contact simultaneously on the tightest curves. Spacing must be
chosen to work across the full range of violin body curvature.

**Shared infrastructure:** The same force sensors used for slip detection
(Problem 1) double as the tangency sensors — two sensors, two problems solved.

Open questions:
- Optimal spacing between contact points (to be derived from violin geometry)
- Whether tangency error triggers retract, or only provides a guidance signal
  to the operator

## What we're building

A purfling router system that addresses both failure modes by adding sensing and
automatic control to the existing mechanical design.

## System layers

| Layer | Description | Directory |
|-------|-------------|-----------|
| Manual jig | 3D-printed purfling router (as-built, no electronics) | `manual/` |
| Sensing | Force/load measurement on cutter | `sensing/` |
| Actuation | Motorised retract mechanism | `actuation/` |
| Electronics | PCB / circuit for sensor + actuator drive | `electronics/` |
| Firmware | MCU code for force reading and retract control | `firmware/` |
| Control | Control law, tuning, calibration | `firmware/control/` |

## Current state

- `manual/` — copied from purfel repo (working mechanical design)
- All other layers: not yet started

## Open questions

- Retract mechanism: servo, stepper, or linear actuator?
- Sensor type: load cell (Wheatstone bridge), FSR, strain gauge on flexure?
- MCU platform: Arduino, RP2040, ESP32?
- Is retract a separate Z-axis or does it pivot the whole jig?

## Key constraints (from manual jig)

- Dremel 3/4"-12 UN thread mount
- 608 bearing edge follower (Ø22 OD)
- M6 bolt clamping at fixed standoff height
- Shoe sits flat on work at z=0
