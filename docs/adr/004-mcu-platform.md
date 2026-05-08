---
id: ADR-004
title: RP2350 (Raspberry Pi Pico 2) as MCU platform
status: decided
date: 2026-05-07
updated: 2026-05-08
---

## Context

The spurfle firmware must handle two distinct concerns simultaneously:

1. **Safety loop** — continuously read the centre load cell and outer Hall
   effect sensors, evaluate GREEN/YELLOW/RED state, trigger retract
   immediately when any sensor enters RED. Latency here is safety-critical.

2. **UI and motion** — manage the re-engagement countdown (timing, auditory
   and visual warnings), drive the stepper motor with smooth acceleration
   profiles, handle operator inputs (zero, re-engage).

These concerns must not compete for CPU time. A single-threaded MCU risks
the safety loop being delayed by stepper or display work.

The developer has prior experience with Arduino (ATmega328P) and ESP32.

## Options considered

**Arduino Uno/Nano (ATmega328P)**
- Single-threaded: safety loop competes with stepper control and UI
- 2KB RAM — tight with multiple libraries
- Not appropriate for a safety-critical real-time trigger
- Rejected

**ESP32**
- Dual core 240MHz — safety loop and UI can run on separate cores
- Good ADC, plenty of GPIO, familiar to developer
- Built-in WiFi/Bluetooth: not needed for this project, and RF emissions
  can introduce noise into sensitive analog circuitry (load cell, Hall
  effect sensors). Manageable with careful PCB layout but an unnecessary
  risk.
- Acceptable but not preferred

**RP2040 (Raspberry Pi Pico)**
- Dual core ARM Cortex-M0+ at 133MHz
- PIO, no WiFi, 12-bit ADC, 264KB RAM, 26 GPIO, ~£4
- Accepted initially; superseded by RP2350 (see below)

**RP2350 (Raspberry Pi Pico 2)**
- Dual core ARM Cortex-M33 at 150MHz — hardware FPU on each core
- **PIO**: 3 blocks (vs 2 on RP2040), same concept; handles HX711 clock
  timing without CPU overhead
- **Hardware FPU**: load cell signal filtering (moving average, Kalman)
  runs without cycle cost on either core
- 520KB RAM (vs 264KB) — headroom for firmware growth
- No WiFi/Bluetooth: eliminates RF noise concern near analog sensors
- 12-bit ADC — adequate for Hall effect displacement sensors
- 26 GPIO — sufficient for all spurfle I/O
- Pin-compatible with Pico; ~£5, widely available
- Strong library support (Arduino-Pico framework, C/C++ SDK); RP2350
  support confirmed in both as of 2025
- Accepted

## Decision

Use the **RP2350 (Raspberry Pi Pico 2)** as the MCU platform.

Updated 2026-05-08: upgraded from RP2040 to RP2350. Pin-compatible, no
firmware architecture change required. HX711 PIO library compatibility
with RP2350 to be verified before finalising firmware.

## Core allocation

| Core | Responsibility |
|------|---------------|
| Core 0 | Safety loop: read load cell (via HX711 PIO), evaluate force state, trigger retract |
| Core 1 | Motion and UI: stepper control, Hall effect reading, LED display, countdown, operator inputs |

PIO handles HX711 clock timing independently of both cores.

## Consequences

- Developer will need to learn RP2350 / Pico SDK or Arduino-Pico framework
  — this is intentional; the architecture benefits justify it
- 3.3V logic throughout — verify all peripheral modules (HX711 breakout,
  stepper driver, LED drivers) are 3.3V compatible or include level shifting
- HX711 breakout boards are widely available and work at 3.3V (confirmed,
  ADR-001: clone board rated 2.6V minimum)
- TMC2208/DRV8825 stepper drivers accept 3.3V logic signals
- Inter-core communication via RP2350 hardware FIFO (built-in, lockless)
  — use for passing state from safety core to UI core
- **Verify:** HX711 PIO library compatibility with RP2350 before finalising
  firmware — most libraries updated for RP2350 but confirm explicitly
