---
id: ADR-003
title: Stepper + lead screw Dremel carriage within gravity-fed floating frame
status: decided
date: 2026-05-07
---

## Context

The retract mechanism must lift the cutter clear of the instrument surface
when edge contact is lost, and return it slowly and under control during
re-engagement. Two constraints drove the design:

1. The shoe must remain in contact with the instrument top at all times — it
   is the reference surface for cutting depth and must not lift away.
2. In both operational scenarios (plate on table; assembled body in cradle),
   gravity provides the vertical positioning of the jig. The retract actuator
   must therefore control both lift and descent — gravity cannot be allowed to
   bring the cutter down uncontrolled.

## Options considered

**Solenoid:** Fast but binary (snap in/snap out). Cannot control descent.
Rejected.

**RC servo with linkage:** Controllable but limited torque, backlash in
linkage, difficult to hold position against gravity reliably. Rejected.

**Stepper motor + lead screw:** Full position and speed control in both
directions. Smooth motion via microstepping. Holds position against gravity
when stationary (holding torque). Well-understood from 3D printer use. Accepted.

## Decision

**Two-level vertical mechanism:**

### Level 1 — floating frame on linear slide (gravity + springs)
The jig frame, contact head, and all electronics hang on a vertical linear
slide above the instrument. Gravity pulls the assembly down so the shoe rests
on the instrument top. Counterbalance springs reduce the effective downforce
to a gentle, controlled contact — enough to keep the shoe on the surface
without risking damage to the instrument top.

The shoe remains in contact with the instrument at all times during operation.
It is never part of the retract motion.

### Level 2 — Dremel carriage on stepper + lead screw (within the frame)
The Dremel is mounted in a carriage that slides vertically within the jig
frame on a lead screw driven by a stepper motor. The stepper and lead screw
travel with the frame on the linear slide.

- **Retract**: stepper drives carriage up, lifting cutter away from shoe
- **Engage**: stepper drives carriage down to the set cutting depth position
- **Cutting depth**: set by the stepper's engaged position — replaces the
  fixed standoff of the manual jig, giving precise and repeatable depth control

## Consequences

- Shoe-to-instrument contact force is set by spring counterbalance selection
  and is independent of the retract mechanism — tune springs separately
- Stepper must hold Dremel carriage position against gravity when retracted
  and when cutting; holding torque requirement is modest (~20 mN·m for 600g
  Dremel on T8 lead screw) — NEMA 17 or smaller is adequate
- T8 lead screw (8mm/rev) with NEMA 17 at 16x microstepping gives ~2.5μm
  per microstep — far finer than needed, ensuring smooth motion
- Cutting depth is now a firmware parameter, not a mechanical setting.
  Because the router bit can be inserted to varying depths in the Dremel
  collet, z=0 (bit tip at shoe surface level) must be established before
  each session. For the prototype this is done manually — the operator
  lowers the carriage until the bit tip is visually at shoe surface level
  and sets that as z=0 via a button press or firmware command.
- **Future enhancement (out of scope for prototype):** automated tool-setter
  zeroing using a conductive calibration plate under the shoe and electrical
  contact detection (standard CNC tool-length-offset practice). Two wires
  and one pull-up resistor. Eliminates manual judgement and enables repeatable
  depth presets.
- Lead screw stroke: 10mm sufficient for retract clearance; a longer screw
  allows depth adjustment range as well
- Spring selection must ensure positive downforce across the full weight
  range of different Dremel models and attachment configurations
- Linear slide for the frame must be smooth and low-friction so the spring
  counterbalance is effective and the shoe contact force is predictable
