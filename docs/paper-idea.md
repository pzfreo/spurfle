# Paper Idea — Software Engineering Practices for Physical Engineering Design

## Thesis

Software engineering has developed powerful practices for managing complexity,
reproducibility, and correctness over decades. Physical engineering design —
CAD, 3D printing, electronics, firmware — has not adopted equivalent practices,
and suffers for it: design rationale is lost, geometric constraints are
violated silently, builds are non-reproducible, and decisions are relitigated.

This paper proposes and demonstrates a coherent methodology that applies
software engineering practices to the full physical engineering stack, using
three real projects as case studies.

## Practices and analogies

| Practice | Software analogy | Project |
|----------|-----------------|---------|
| Version-controlled parametric design | Source code in git | purfel, purfroller, spurfle |
| Spec/code as a coupled pair | Interface + implementation | All |
| Parametric model assertions as test suite | Unit tests | spurfle |
| Physical constraint dependency chains | Type system / import graph | spurfle |
| Architecture Decision Records (ADRs) | Architecture records | spurfle |
| Reproducible slicer pipeline | Dockerfile / Nix / lockfile | estampo |
| Git branches, PRs, and review | Standard SW workflow | All |

## Case studies

### purfel / purfroller — baseline
Parametric 3D-printed tooling for instrument making. Demonstrates
version-controlled parametric design and spec/code coupling: `SPEC.md` and
the `.py` model file are a coupled pair — drift between them is treated as a
bug. Establishes the git workflow for hardware.

### estampo — reproducible manufacturing builds
A pipeline tool that pins the slicer version, printer profile, material,
all slicer overrides, and part orientations in a `estampo.toml` committed
alongside the design. A git commit hash + `estampo.toml` = a fully
reproducible physical artifact. Direct analogy to Dockerfile / Nix / lockfiles
applied to 3D printing.

### spurfle — full methodology
A safe purfling device for stringed-instrument making (violin, viol da gamba).
Multi-domain project: 3D-printed mechanics, force and displacement sensors,
stepper motor control, electronics, firmware. Demonstrates:
- ADRs for hardware design decisions (sensor type, contact geometry, retract
  mechanism, MCU platform)
- `CONSTRAINTS.md` — explicit physical constraint dependency chains, each
  constraint numbered, sourced, and cross-referenced to the model code
- Assertion convention: derived dimensions calculated not typed; constraints
  expressed as `assert` statements in model `.py` files; running the model
  is the test run
- Cross-domain `interfaces.md` for constraints that span mechanical,
  electrical, and firmware boundaries

## Key insight

In software, dependency chains are structural — the compiler or import system
makes them explicit. Tests verify behaviour at any time. In physical design,
both are absent: constraints are implicit in the geometry, and the only "test"
is building it and finding it doesn't fit.

The assertion approach in parametric models bridges this gap: a constraint
violation surfaces immediately as a Python error with a human-readable message,
before any material is committed. This is the closest practical analogy to
a compile-time type error for physical geometry.

## Target venues

- *International Journal of Advanced Manufacturing Technology* (Springer)
- *Journal of Manufacturing Systems* (Elsevier)
- *Design Studies* (Elsevier)
- *Proceedings of the Design Society* (Cambridge)
- A practitioner-facing outlet (Make:, Hackaday, or similar) for a shorter
  version aimed at the maker/open hardware community

## Status

Methodology in active development on the spurfle project. Paper to be drafted
when spurfle reaches a working prototype. The three projects together provide
a complete narrative arc from baseline practice to full methodology.
