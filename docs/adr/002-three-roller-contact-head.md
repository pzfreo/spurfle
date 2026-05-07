---
id: ADR-002
title: Three-roller contact head with fixed centre and spring-loaded outer pair
status: decided
date: 2026-05-07
---

## Context

The manual jig uses a single 608 bearing (Ø22mm OD) as the edge follower. The
operator holds the jig against the violin edge and the bearing OD sets the
cutter-to-edge distance. This suffers from the two failure modes documented in
PROJECT.md: edge slip and tangency error.

The new design fixes the jig and feeds the instrument edge against it. This
requires the contact head to:

1. Maintain a precise, consistent cutter-to-edge distance reference
2. Detect loss of edge contact (triggers retract)
3. Detect and indicate tangency error (jig not aligned with edge curve)

Several contact head geometries were considered.

### Option A — single bearing (as per manual jig)
- Provides distance reference
- No contact detection, no tangency detection
- Rejected: does not address either failure mode

### Option B — dual bearing with force balance
- Two bearings, both measuring force
- Equal force = tangential; unequal = off-tangent
- Problem: with the cutter between the two bearings, sagitta error introduces
  cutter-to-edge variation of ~1.4mm across the full violin body outline
  (convex bouts R≈100mm to concave waist R≈25mm). This is unacceptable for
  purfling work where channel placement accuracy is critical.
- Rejected: sagitta error unacceptable

### Option C — three contacts: fixed centre + spring-loaded outer pair
- Centre contact is fixed and is the sole distance reference — identical
  geometry to the manual jig's single bearing, no sagitta error
- Two outer contacts are spring-loaded and sense tangency only
- The outer contacts move naturally with convex/concave curves (sagitta
  variation); their absolute position cannot infer whether the centre is
  in contact — that requires an independent force sensor on the centre
- Accepted

## Roller type

Ball plungers (spring-loaded spherical tip) were initially considered for the
outer contacts as they offer point contact regardless of surface height.
However, against the violin plate overhang (~3mm tall), a ball plunger has
insufficient surface height to remain reliably engaged — the ball rides off
the thin edge.

**Needle rollers (~4mm OD)** constrained in slots are used for all three
contacts. They:
- Track reliably against both the 3mm violin overhang and the full viol da
  gamba rib (line contact against a vertical face, height variation handled
  by the slot constraint)
- Are small enough for three to fit within a 20mm total span
- Are available as standard components

## Sensor allocation

The outer rollers move in and out with the natural curvature of the instrument
body (spring travel ~3mm required across the full violin outline). Their
absolute displacement cannot indicate whether the centre roller is in contact.
Therefore:

- **Centre roller**: load cell (ADR-001) measures contact force → retract trigger
- **Outer rollers**: Hall effect displacement sensors measure position →
  tangency feedback. Differential between the two = tangency error signal.

Both outer rollers report GREEN/YELLOW/RED based on the magnitude of the
differential. Either outer going RED triggers retract (tangency error too
large). See PROJECT.md control logic.

## Decision

**Three needle rollers (~4mm OD), ≤20mm total outer-to-outer span:**
- Centre: fixed, load cell force sensor
- Outer left and right: spring-loaded, Hall effect displacement sensors

## Consequences

- Centre roller mount must transmit force cleanly to the load cell with no
  side-loading (mount design critical)
- Outer roller springs must provide ~3mm travel without bottoming out or
  losing preload across the full range of violin body curvature
- Hall effect sensors require a small magnet on each outer roller mount and
  a fixed sensor on the jig body (~0.1mm resolution adequate)
- 20mm outer span must be confirmed against minimum violin waist radius
  (~25mm) to ensure both outer rollers can simultaneously contact the edge
- Roller height must be set for each instrument type (violin ~3mm overhang
  vs viol da gamba ~50–60mm rib); interchangeable contact head configurations
  may be required
