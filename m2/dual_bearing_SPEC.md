# m2 Dual-Bearing Carriage — Design Spec

## Purpose

Replace the single ø22 mm (608) bearing follower on the m2 purfling cutter with
a small printed carriage carrying **two ø8 mm nylon bearings** on ø2 mm steel
pin axles. The single bearing has a known failure mode: the cutter can rotate
about the bearing's vertical axis when the operator's grip tilts, and any
rotation changes the effective bit-to-edge distance. Two contact points lock
the cutter's orientation against the violin rib's local tangent, so the
bit-to-edge distance becomes a true geometric constant rather than a tangent
line.

## Scope — what stays unchanged

The shoe slot and its slide-adjustment mechanism in `m2/cutter.py` are **fixed
hardware**:

- Slot geometry: `SLOT_LEN = 18`, `SLOT_W = 6.5`, position `SLOT_X_CENTER`
- The stadium ø6 × 9 mm stem (currently `build_upper_sleeve` in `m2/cutter.py`)
  that fits in the slot
- The captive M4 nut in the top flange of the upper sleeve / carriage
- The M4 clamp bolt rising from below the carriage, threading into the captive
  nut, locking the carriage's X position in the slot
- All the surrounding cutter geometry (plate, shoe, standoffs, Dremel mount,
  surround/bit hole) is untouched

The carriage must accept the same M4 clamp arrangement as today, with the same
sliding range, so bit-to-edge distance remains operator-adjustable.

## What changes

The components below the shoe are replaced:

- **Removed:** lower_sleeve, 608 bearing, washer
- **Added:** a printed dual-bearing carriage carrying 2× nylon rollers on
  steel pin axles

## Bearing geometry — reuse from `mechanics/contact_head.py`

The contact_head module already models a ø8 mm nylon roller on a ø2 mm steel
pin with established constraints (C-011 .. C-014). All those constraints carry
over to each bearing in the new carriage.

| Parameter | Value | Source |
|---|---|---|
| Roller OD | **8.0 mm** | nylon FDM print; chosen so that a ø6 mm holder housing leaves ≥1.5 mm wall around the pin (per user) |
| Roller bore | 1.7 mm | running fit on ø2 pin (`PIN_D + BORE_FIT`) |
| Roller wall around bore | 3.15 mm | (8 − 1.7) / 2; well above `FDM_WALL_MIN` |
| Roller printed height | (12 − 0.2) = 11.8 mm | nominal 12 mm with 0.1 mm axial play each end; **TBD** — sized to violin rib height |
| Pin axle | **ø2 mm × 18 mm steel** | user's existing stock |
| Pin length budget | `2 × pocket_depth + roller_height = 18 mm` | matches stock with `pocket_depth = 3 mm`, `roller_h = 12 mm` |

## Bearing layout — fixed by user

- **Two bearings**, axles **vertical** (perpendicular to the violin top — "right
  angles to the work")
- **Centre-to-centre spacing: 10 mm** (edge-to-edge gap 2 mm — bearings nearly
  touching)
- Both bearings at the **same X position** in the cutter local frame (same
  distance from the cutter bit)
- Spaced along **Y** (perpendicular to the cutter's long axis / perpendicular
  to the slot length) — bearings sit side-by-side across the cutter's width
- Carriage centred laterally on the cutter's Y = 0 axis
- Both bearings contact the violin rib simultaneously → the rib's local
  tangent direction is enforced on the cutter → bit-to-edge distance locked

## Sagitta tradeoff (noted, not solved)

The dual-bearing geometry trades **tangency error** (current single-bearing
failure mode) for **sagitta error**: because the bit is offset from the
bearings along the cutter's X axis, and the bearings define a chord of the
violin's edge curve, the bit's perpendicular distance to the edge varies with
the local curve radius.

At 10 mm bearing spacing, ø8 mm bearings, across the full violin body outline:

| Local curve | Radius | Midpoint-to-edge distance |
|---|---|---|
| Convex bout (tightest convex) | R = 100 mm | 3.88 mm |
| Convex bout (smallest) | R ≈ 25 mm | 3.57 mm |
| Straight edge | R = ∞ | 4.00 mm |
| Concave waist | R = 25 mm | 4.60 mm |

**Bit-to-edge variation: ~1.0 mm** (convex tight bout to concave waist).

This is more than the ~0.4 mm initially estimated and is the principal known
weakness of the design. It is comparable to but smaller than the variation
that led ADR-002 to reject the dual-bearing geometry at 20 mm spacing for the
automated jig (where ~1.4 mm sagitta variation was rejected). The manual
cutter context is more forgiving: the operator can compensate visually, and
the alternative (current single-bearing tangency error) gives unbounded error
under hand-grip tilt rather than bounded sagitta error.

**Open decision:** is 1 mm bit-to-edge variation acceptable for this manual
cutter? If not, the spacing must shrink (but 10 mm is already near the minimum
for ø8 mm bearings — 8 mm spacing gives bearings touching).

## Pin retention — two options on the table

### Option A — sandwich plates with blind pockets

Two ASA plates (upper, lower) each with a 3 mm blind pocket per pin position.
Pins are captive between the plates with no fasteners passing through the
pins. The two plates are joined by separate fastening: 2× M3 bolts and
heat-set inserts, snap-fit features, or a similar scheme — TBD.

This mirrors the existing `mechanics/contact_head.py` retention.

- **Pros:** well-understood; FDM-friendly; structurally robust against shock;
  no friction-fit accuracy dependency
- **Cons:** plates need to be ≥3 mm thick each (per C-012); user has noted
  preference for thinner top plate than `contact_head.py` uses (4.5 mm);
  requires designing a join mechanism between plates

### Option B — single-piece carriage with friction-fit pins

A one-piece printed carriage with two through-bores (or bottom-blind bores)
for the pins. Pins press-fit into the bores with ~0.05–0.1 mm interference.
Bearings slip onto pins before pressing, or whole assembly is print-in-place.

- **Pros:** simpler — one printed part instead of two; thinner overall
  (no double-plate sandwich); potentially print-in-place if tolerances allow
- **Cons:** FDM ASA friction fits are tolerance-sensitive; the bore may crack
  during press-fit or loosen with thermal cycling; depends on print accuracy
  and consistency

User has flagged Option B specifically as worth evaluating because the
preference is for thinner plates and a more "print in place" assembly. The
choice between A and B is the principal open design question.

## Carriage attachment to shoe — unchanged

- M4 clamp bolt rises from below the carriage through an M4 clearance bore in
  the carriage body
- Bolt threads into the captive M4 nut in the upper part of the carriage that
  sits inside the shoe slot
- Tightening clamps the carriage stationary against the shoe; loosening
  allows sliding in the slot for bit-to-edge adjustment

## Constraints inherited from `mechanics/contact_head.py`

All per-bearing constraints apply per bearing in this design:

- **C-011** — holder OD < roller OD (so the bearing contacts the work first,
  not the holder); holder wall around pin ≥ `FDM_WALL_PREF`
- **C-012** — holder plate thickness ≥ 3 mm (shock-load bearing depth)
- **C-013** — axial pin retention by blind pockets (Option A) or friction fit
  (Option B); pocket depth ≥ 1.5 mm if Option A, with solid wall ≥
  `FDM_WALL_MIN` behind the pocket
- **C-014** — radial gap between roller OD and any holder face ≥ 1 mm

## New constraints — to add when the model is written

- **CN-1** — Bearing spacing vs minimum violin curve radius. Half-chord
  (S/2 = 5 mm) must be < waist radius (25 mm). ✓ — satisfied.
- **CN-2** — Sagitta variation across operating envelope ≤ acceptable
  threshold. **Threshold TBD** by operator review. Current value ~1.0 mm.
- **CN-3** — Pin retention method must survive operator handling and the
  cutter rotating around the violin perimeter without releasing the pin.
  Verification differs for Option A (assertion on pocket depth) vs Option B
  (assertion on interference fit + empirical print check).

## Open decisions summary

1. **Pin retention scheme:** Option A (sandwich plates + join) or Option B
   (one-piece + friction fit)
2. **Roller height:** match `contact_head.py`'s 12 mm or shorter, sized to
   violin rib geometry — needs measurement
3. **Plate thickness if Option A:** ≥3 mm per C-012; could be thinner than
   contact_head's 4.5 mm if shock-load analysis allows
4. **Joining mechanism between plates if Option A:** M3 bolts + heat-set
   inserts? Snap-fit? Glue?
5. **Sagitta tolerance:** is 1.0 mm bit-to-edge variation acceptable for
   manual operation, or do we need tighter (and thus narrower bearing
   spacing, which means smaller bearings or accepting bearings that touch)?
6. **Carriage outer profile:** rectangular block? Stadium following the two
   pin positions? Constrained by what clears adjacent shoe features when
   slid through the full adjustment range

---

## Alternative — Fixed slider stubs (Option 2, current direction)

Instead of rolling bearings, use **two fixed cylindrical stubs** that slide
against the violin rib. The carriage is a single printed piece; the stubs
are either integrated (prototype) or short bored-in pieces of solid extruded
acetal/Delrin rod (final).

Sagitta variation scales with `(S/2)² / R_min`, so dropping the spacing more
than makes up for losing the roller. Smaller stub OD → tighter S → tighter
sagitta.

### Geometry

| Parameter | Value | Notes |
|---|---|---|
| Stub OD | **5 mm** | Final stock: ø5 mm Delrin rod (POM-C) |
| Stub spacing centre-to-centre | **5 mm** | Stubs touching (zero edge-to-edge gap; OK because they don't rotate) |
| Stub Z protrusion below carriage body | **7 mm** | Matches current bearing Z extent — contacts the rib over ~7 mm of vertical range |
| Sagitta variation across body outline | **0.25 mm** | (S/2)² / 25 = 6.25/25 |
| Stub material (prototype) | FDM nylon | Print integrated with carriage |
| Stub material (final) | Solid extruded Delrin | Press-fit / glued into bores; smoother surface than any FDM material |

### Carriage construction

- One printed piece in ASA (or nylon, for prototype) — replaces the existing
  `lower_sleeve + 608 bearing + washer` stack
- Top face flush against the shoe bottom (z = 0)
- M4 clamp bolt clearance bore through the body's centre — bolt comes from
  below the carriage, through the body, through the shoe slot, into the
  captive M4 nut in the **existing** `upper_sleeve` at the top
- Two stubs (or stub bores) hang down from the body's underside, centred on
  the carriage's X position (= the M4 bolt axis = the slot-adjustable
  bit-to-edge distance)
- Stubs span y = ±2.5 (touching at y = 0), both at the same X
- Rotation lock: friction between the carriage top face and the shoe bottom
  (relies on M4 bolt tension). If lab testing shows the carriage rotates
  under sliding load, add a tongue feature that engages the slot from below.

### Why FDM-nylon prototype before Delrin

The risk with this design is that **layer-line texture** on the side of the
printed stub will produce stick-slip against the violin rib and may dull the
varnish. A nylon prototype lets us evaluate this empirically before
committing to ø5 Delrin rod stock. If the nylon stubs feel rough, swap to
Delrin (bores in the carriage hold the rod) and the rest of the design is
unchanged.

### Pros / cons vs the rolling-bearing variant

Pros:
- 0.25 mm sagitta variation vs 0.49 mm
- One printed part instead of two-plus-pins-plus-rollers
- No FDM friction-fit risk on pins
- Cheap stock for final version (~£3 of Delrin)

Cons:
- Sliding friction (not rolling) — operator pushes harder
- Potential surface marking on varnished rib
- Less proven for purfling work

### Prototype model

Built in `m2/slider_carriage.py`. The prototype has the stubs integrated; a
parameter switches the model to "Delrin bores" for the final version.
