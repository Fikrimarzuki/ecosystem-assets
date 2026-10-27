# M1.1e-A Gate A: comparison record (experimental)

**Status:** historical record. Nothing here is accepted, approved or production-ready; rights are unverified. Gate B has not started.

## Outcome

Gate A compared an SVG candidate (Claude Code, `momee-character-art` skill) with a painted candidate (Codex built-in `image_gen`) at 256 px and 144 px. The owner discontinued the SVG direction and Mom v1 on 2026-11-16, and their artwork was deleted. The SVG arm's own findings are kept as text in `../SVG-ARM-RECORD.md`.

The joint sheets (B | Mom v1 | SVG | painted) were deleted with them. The painted-only replacements are `../painted/review/sheet-{256,144,720}.png` (B portrait | painted candidate) and `../painted/review/eye-detail.png` (B eye tile | painted eyes).

## Inputs and crops (still valid)

- **B portrait:** `references/mom-art-direction-exploration-v1.png@541,191,294,351`
- **B eye tile:** `@541,730,112,109`
- **Painted candidate:** `../painted/mom-neutral-painted-v1.png`; eye crops `296,450,204,198` and `580,450,204,198`.

The sheets were built by the coordinating Claude Code session with `momee-character-art/scripts/compare-sheet.mjs`, because the Codex sandbox could not launch Chromium. The 2026-11-16 painted-only sheets replaced the earlier ones that also showed Mom v1.

## Technical notes for Gate B (observed or measured, not fixed)

- **Alpha:** almost every figure pixel is at alpha 253 of 255 (`../painted/review/measurements.json`); only 17 are fully opaque. Needs a clean-up inside the silhouette before layer work.
- **Framing:** the hair touches the left, right and bottom canvas edges; layer work needs more margin.
- **Edges:** a thin warm rim on the hair edges (`../painted/review/alpha-dark.png`).
