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

### Part selection (2026-05-08)

**Galoce miniature flat capsule load cell, 1 kg rated capacity**

| Parameter | Value |
|-----------|-------|
| Rated load | 1 kg (≈ 10 N) |
| Body diameter | ø13 mm |
| Body depth (force direction) | 9 mm |
| Output sensitivity | 2.0 ± 0.05% mV/V |
| Bridge impedance | 350 Ω |
| Excitation voltage | 5–10 V |
| Safety overload | 150% (≈ 15 N) |
| Material | Stainless steel |
| Source | AliExpress item 1005007884494411 |

Rationale for 1 kg over 5 kg: expected violin edge contact force is a few
newtons at most — pressing harder risks finish damage. Using full scale gives
maximum HX711 resolution over the operating range.

Flat capsule form chosen over button (ø20 mm, 12 mm deep) because it is more
compact in both footprint and depth, with higher sensitivity (2.0 vs 1.5 mV/V).
Pressure point capsule rejected: minimum range 300 kg, entirely unsuitable.

## Consequences

- Housing must provide a ø13 mm pocket, 9 mm deep behind the centre roller
  to seat the load cell (see C-001)
- Roller holder bears directly on the flat face of the load cell — housing
  pocket must locate the cell so force is applied perpendicular to the face
- HX711 breakout requires 4 signal lines to MCU (VCC, GND, DATA, CLK)
- 350 Ω bridge at 5 V draws ~14 mA — within HX711 AVDD supply capability
- Calibration procedure required at first setup to establish N→ADC mapping
  and set GREEN/YELLOW/RED thresholds
- Safety overload is 15 N — shock loads from accidental knock must be
  considered in the housing/mounting design
