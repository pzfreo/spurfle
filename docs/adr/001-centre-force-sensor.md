---
id: ADR-001
title: Load cell for centre roller force measurement
status: decided
date: 2026-05-07
---

## Context

The centre roller force sensor is the safety-critical measurement in the
system. It is the sole detector of edge contact loss and the primary trigger
for cutter retract. False negatives (missed retract) risk catastrophic overcut
into the instrument. False positives (unwanted retract) interrupt the workflow.

Both failure modes require the sensor to have accurate, consistent, repeatable
readings so that the GREEN/YELLOW/RED thresholds can be reliably calibrated and
trusted across sessions and temperature variation.

Two options were considered:

**FSR (Force Sensitive Resistor)**
- Simple: resistor voltage divider, direct to MCU ADC
- Cheap (~£3)
- Significant hysteresis (~±15%), drift over time, non-linear response
- Thresholds would shift with temperature and wear
- Not appropriate where threshold consistency is safety-critical

**Load cell + HX711 amplifier**
- Load cell is a machined metal flexure with bonded strain gauges in a
  Wheatstone bridge configuration
- HX711 is a dedicated 24-bit ADC for Wheatstone bridge sensors (~£3 for
  breakout board)
- Accurate, consistent, and repeatable — thresholds calibrate once and hold
- Well-established in hobby/maker projects; good library support for all
  common MCU platforms
- Slightly more complex wiring (4-wire bridge + HX711 breakout) but
  straightforward in practice

## Decision

Use a **small load cell + HX711 amplifier** for the centre roller force
measurement.

Accuracy and consistency are the primary requirements for a safety-critical
trigger. The additional complexity of the HX711 is modest and fully justified.

## Consequences

- Load cell must be selected for the expected force range (~1–20 N violin
  edge contact — to be confirmed by measurement)
- Load cell must be integrated into the centre roller mount such that the
  roller force is transmitted cleanly through the cell (no side-loading)
- HX711 breakout requires 4 signal lines to MCU (VCC, GND, DATA, CLK)
- Calibration procedure required at first setup to establish N→ADC mapping
  and set GREEN/YELLOW/RED thresholds
- Same approach should be considered for any future force measurements added
  to the system
