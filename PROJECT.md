# Spurfle — Safe Purfling Device

## What we're building

A purfling router system for stringed-instrument tops that adds force sensing and
automatic cutter retract to the existing manual jig design. When lateral cutting
force exceeds a threshold, the cutter lifts automatically to prevent overcuts and
damage to the instrument.

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
