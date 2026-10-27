# MOMEE M1.1f: Painted Mom visual redesign

Experimental three-technique exploration for owner review. Preserve Mom’s adult identity while comparing refined Candidate B contours, premium picture-book paint, and matte gouache adventure paint.

Nothing is selected or approved. Rights are unverified. Per-candidate retained source choices are technical choices for review deliverables only. All three remain **not visually successful yet** because none met the fully opaque figure contract after the three-call cap.

## Candidates

| Candidate/style | Calls | Deliverable | Retained generation |
| --- | ---: | --- | ---: |
| A: Refined B Portrait | 3 | [candidate-a-refined-b/mom-a-v1.png](candidate-a-refined-b/mom-a-v1.png) | 2 |
| B: Premium Painted Storybook | 3 | [candidate-b-premium-painted/mom-b-v1.png](candidate-b-premium-painted/mom-b-v1.png) | 2 |
| C: Gouache Adventure Storybook | 3 | [candidate-c-gouache-adventure/mom-c-v1.png](candidate-c-gouache-adventure/mom-c-v1.png) | 3 |

Total: 9 built-in image_gen calls. All nine generated originals are preserved byte-for-byte in the candidate generations/ folders, along with exact prompt text and input/output hashes. Model: not recorded by the tool. CLI: codex-cli 0.167.1. Date: 2026-11-16 UTC.

## Source inputs and SHA-256

- projects/momee/styles/soft-storybook-adventure/references/mom-art-direction-exploration-v1.png — 118eca2c37ebc4db123e512c369998875cd87beffefb0861a206f21825989481
- projects/momee/styles/soft-storybook-adventure/experiments/m1.1e-a-neutral-bakeoff/painted/mom-neutral-painted-v1.png — 9f6a61d128ebdb5c7cc392edc3702a7ddfd0e974678a2a3e79f041d1599baa78
- projects/momee/styles/soft-storybook-adventure/references/momee-soft-storybook-master-reference-v1.png — 907a9bd82ed5aec0fe7f50c0494bcdda1d74fddf59a1d51c2b07cd34fb77dd36
- projects/momee/styles/soft-storybook-adventure/docs/mom-visual-spec-v1.md — 15bad5a371cd87fdc99e7ffb4a87fe879ad22c2370955a82910c6ccbf91c7e30

## Image inputs fed to generation

- [inputs/b-portrait.png](inputs/b-portrait.png) — 2e800d62b0f1f127c032f0ac1ec8d7935edecf965fdb6d350af4ba81ab912a53; crop 541,191,294,351. integer crop only; pngjs RGBA encoding.
- [inputs/b-eye.png](inputs/b-eye.png) — 5dd12cff19214d31175114d2a6841b5b710b44742ab186bb98fbb523245a816b; crop 541,730,112,109. integer crop only; pngjs RGBA encoding.
- [inputs/gate-a-painted.png](inputs/gate-a-painted.png) — 9f6a61d128ebdb5c7cc392edc3702a7ddfd0e974678a2a3e79f041d1599baa78; crop 0,0,1024,1280. full image, byte-for-byte copy.
- [inputs/family-master.png](inputs/family-master.png) — 907a9bd82ed5aec0fe7f50c0494bcdda1d74fddf59a1d51c2b07cd34fb77dd36; crop 0,0,1536,1024. full image, byte-for-byte copy.

Coordinates and source hashes are in [inputs/crops.json](inputs/crops.json). Candidate B portrait uses exactly 541,191,294,351; eye tile uses 541,730,112,109. Painted and family references are full-image byte copies. No characters/mom assets were opened or used.

## Verification and limits

All deliverables are 1024 × 1280 RGBA. Padding and uniform scaling provide more than 6% clear margins on left/right/top; no nontransparent pixel touches an edge. Interiors remain mostly partial alpha, and coloured boundary flecks persist. No alpha correction or retouching was performed. Candidate READMEs contain separate-image visual review and remaining gaps; same-height comparison sheets are reserved for the coordinator and were not created. Individual 144 × 180 thumbnail PNGs are included.

Run from the repository root: node projects/momee/styles/soft-storybook-adventure/experiments/m1.1f-painted-redesign/measure.mjs. The small script records only and never changes image pixels. derive.mjs documents/reproduces padding and scaling. provenance.json records all prompts, input/output SHA-256 values, the retained output and derivation parameters.

Repository status is recorded verbatim in [git-status-before.txt](git-status-before.txt) and [git-status-after.txt](git-status-after.txt). Existing modifications and deletions were left untouched; the new experiment folder is the only added status entry. No commits, installs, network services, or registry changes.
