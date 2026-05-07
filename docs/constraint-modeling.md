# Physical Constraint Modeling for build123d Assemblies

Notes from a discussion about applying physical/dimensional constraints to
build123d assemblies, with a focus on testable CAD-as-code workflows (CI for
3D printed assemblies).

## Context and Goal

The aim is to shift left from "did it interfere?" to "by construction, it
can't." Interference, clearance, and volumetric tests already work well as
post-construction checks. The harder, more interesting problem is encoding
design intent so that interference becomes structurally impossible — catching
problems before they become an interference test.

This is the constraint-first vs check-after split. It has names in the
literature: *design intent capture* and *constraint propagation*. The core
insight is that interference is a *symptom*; the *cause* is that two parts
both made independent decisions about a shared dimension. The fix is to stop
letting them.

## What Already Exists in build123d

build123d has a Joints system (Rigid, Revolute, Linear, Cylindrical, Ball)
for connecting parts in assemblies — the same idea as mates in
SolidWorks/Fusion. It's lighter than CadQuery's full constraint solver but
solid for most assembly work: you declare "this part goes right here" via a
static joint rather than solving a system of mate constraints.

The official roadmap flags constraint-based sketching and intelligent
placement as future directions, and notably suggests pairing build123d with
Experta (a Python rules engine using the Rete algorithm) for symbolic
constraint reasoning over geometry. Facts can track geometry and computed
properties; rules can call methods like `a.intersect(b)` or perform custom
layout logic.

## The Three Layers

A staged approach, roughly in order of effort:

### Layer 1: Single Source of Truth via Parameter Propagation

Every dimension that crosses a part boundary lives in one place — a frozen
dataclass, a TOML file, a pydantic model — and parts derive from it.

If part A has a 5mm boss and part B has a hole for it, neither hardcodes
5mm. Both reference `params.boss_diameter`, and B's hole is computed as
`params.boss_diameter + params.clearance_fit`.

build123d makes this trivial because the model is just Python. The
interference test still exists, but now it's a *redundant* check — the
geometry was constructed such that it can't fail. This is essentially what
the Queen's Belfast Finite Element Modelling Group advocates: identify
parametric relationships between parts, and constrain the assembly according
to those relationships.

### Layer 2: Mating Features as First-Class Objects

Instead of "part A has a hole here, part B has a peg here, hope they line
up," define a `PegHoleMate` object that *generates* both the peg and the
hole from shared parameters (diameter, depth, fit class, chamfer).

The peg part calls `mate.peg_geometry()`. The hole part calls
`mate.hole_geometry()`. They share a Joint location.

This is the abstraction the AutoMate paper formalizes — CAD assemblies as a
system of pairwise constraints (mates) defined relative to BREP topology
rather than world coordinates — except you're building it as Python classes
rather than relying on a CAD kernel's mate solver.

ISO fits (H7/h6, etc.) become a lookup table. Tap drill sizes for threaded
inserts become a function. Once you have these primitives, assembling a
design feels much more like wiring up components than positioning geometry.

### Layer 3: Manufacturability and Physical Realizability as Types

Wrap dimensions in types that carry constraints:

- `WallThickness(value, min_for_process=0.8)`
- `OverhangAngle`
- `BridgeSpan`
- `ScrewBoss(insert=M3_brass_heatset)` — knows its own minimum wall
  thickness, hole depth, lead-in chamfer, required clearance to other
  features

Construction validates. You can't construct an invalid feature.

Tests then assert at the *type level* — "every screw boss in this assembly
has at least 1.5×wall_thickness clearance to other features" — which catches
problems the moment a feature is placed, not after the whole model is built.

This is essentially feature-based design, which is mature in commercial CAD
(SolidWorks Hole Wizard, Onshape FeatureScript) but underdeveloped in
code-CAD.

## The CI Angle

What you can do that commercial CAD can't easily: test the parameter space,
not just one instantiation.

Property-based testing with Hypothesis — generate plausible parameter sets
within their declared ranges and assert no assembly violates clearance, no
wall goes thin, no overhang exceeds limit. This is the analog of fuzz
testing for CAD.

The Queen's Belfast sensitivity-analysis approach is a more numerical version
of the same idea: perturb the parameters in the assembly by a small amount,
recalculate the clash, calculate the sensitivity of each parameter as the
change in clash with respect to the parametric value. It's a great way to
find which parameters are *load-bearing* for your design's correctness.

### Suggested CI Test Categories

- **Parameter-driven assertions** — derived values stay in declared ranges
  across the parameter space
- **Mate consistency** — for each mate, the two halves match (diameter pair,
  depth, clearance class)
- **Clearance/interference** — still run as a regression catch, but now
  expected to always pass
- **Manufacturability** — overhang angles, minimum wall thickness, bridging
  spans, trapped volumes (resin), unsupported islands
- **Volume/bounding-box drift** — smoke test for surprising topology changes
- **Visual regression** — fixed-camera renders to PNG, image-diff
- **Mesh sanity** — watertightness, manifold-ness, genus (via trimesh)
- **Kinematic sweeps** — for revolute/linear joints, sample the range of
  motion and assert no collision

## The Hard Problem

What you can't easily do in code-CAD that commercial systems do: bidirectional
constraint solving.

SolidWorks' sketcher lets you say "these two edges are tangent" and solves
for the geometry. build123d makes you compute the geometry yourself.

- For 2D, python-solvespace exposes SolveSpace's solver as a library — you
  can solve a sketch and feed results into build123d.
- For 3D mates between BREPs, there's no good open-source solver. Everyone
  falls back to "place by joint, check by intersection."

This is the gap that the Layer 2 mating-feature abstraction works around:
you don't *solve* for mate consistency, you *generate* both sides from a
shared specification, which is consistent by construction.

## The Honest Gap

There's no off-the-shelf "pytest for CAD" library. People assemble it from
pytest + build123d + trimesh + a slicer in headless mode. That's also the
opportunity if you wanted to publish something — the abstractions in Layers
2 and 3 don't really exist in the open-source code-CAD world yet.

## Concrete Next Step (when reaching code)

A Mate / Feature class hierarchy for build123d demonstrating Layer 2 — e.g.
`PegHoleMate`, `ScrewBossMate`, `HeatsetInsertMate`, each generating both
halves from a shared spec, with associated pytest fixtures that validate
consistency by construction.

## Reading List

### Active and directly relevant

- **AutoMate** (Jones et al., UW/PTC/Adobe, 2021) — large-scale dataset of
  BREP CAD assemblies and mates; SB-GCN learns to predict mates from
  topology. Useful for understanding how mates are formalized in modern CAD.
  https://arxiv.org/pdf/2105.12238
- **Queen's Belfast Finite Element Modelling Group** — design intent for CAD
  assemblies, sensitivity analysis to identify clash-driving parameters
- **build123d Roadmap** — Experta integration for rules-based geometry
  reasoning

### Foundational

- Jami Shah, *Parametric and Feature-Based CAD/CAM* — canonical textbook on
  feature-based design
- Search terms: "feature-based design," "assembly feature recognition,"
  "design-by-feature," "constraint-based assembly modeling," "design intent
  capture"

### Adjacent culture worth borrowing from

- **KiCad ERC/DRC rules** — electronics has a much more mature
  design-rule-check culture than mechanical CAD, and many patterns transfer
  directly
- **OpenSCAD test suite** — patterns for geometric regression testing
- **Slicer rule sets** (PrusaSlicer, Cura) — the DfAM rules already exist as
  warnings; you want them as assertions

### DfAM / printability rule sources

- Search: "design for additive manufacturing rule checking,"
  "manufacturability analysis additive," "geometric feature recognition for
  3D printing"
- Commercial implementations: Autodesk Netfabb, Materialise Magics — rules
  are well-documented and reimplementable
