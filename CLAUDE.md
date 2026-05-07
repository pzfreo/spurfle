# Spurfle — Claude project notes

## Read first

At the start of every session, read:
1. `PROJECT.md` — what we're building, current state, open questions
2. `docs/interfaces.md` — cross-domain constraints (if it exists)
3. The spec file for whichever layer you're working in

## Physical constraint chains

Physical designs have dependency chains that are easy to lose track of.
The project treats parametric model assertions as a test suite:

- Every derived dimension must be **calculated** from its source, never
  typed as a magic number
- Every constraint between two values must have an `assert` with a message
- Running `python <model>.py` must pass cleanly — a failure is a broken
  constraint, treated like a failing test
- Constraints that cannot be asserted in code (kinematic direction, assembly
  order) must be documented in `docs/CONSTRAINTS.md` with a **Note:** entry
- When adding a new constant, ask: what does this depend on? What depends
  on it? Add both the derivation and the assertion.
- When a dimension is unknown, mark it TBD in `docs/CONSTRAINTS.md` with
  a placeholder assert `assert False, "C-NNN: TBD — <what needs deciding>"`
  so the model fails until the constraint is resolved

## Layer specs and code are coupled pairs

Each layer has a spec (e.g. `manual/SPEC.md`, `sensing/SPEC.md`) that describes
as-built geometry, constants, and design intent. The spec and the implementation
(`.py`, `.ino`, `.kicad_sch`, etc.) are a **coupled pair** — drift between them
is a bug. When you change one, update the other in the same commit.

## Cross-domain changes

When a change in one layer affects another (e.g. mechanical dimensions change a
PCB keepout, or sensor range changes a firmware threshold), update `docs/interfaces.md`
and flag it in the PR description. Don't silently update only one side.

## ADRs

Significant design decisions (choice of MCU, sensor type, retract mechanism) go
in `docs/adr/NNN-title.md`. Use the format: Context / Decision / Consequences.
Link ADRs from `PROJECT.md` open questions when they're resolved.

## Branches and PRs

- Never commit directly to main
- One logical change per branch/PR
- STOP after creating a PR — wait for review before merging

## Build and verify

- `manual/`: run `python manual/cutter.py` to regenerate STLs
- Other layers: document their build commands in their own SPEC.md
