# Scriptoria asset collection

Copied from `scriptoria-assets/` on 2026-10-23 under canonical project ID `scriptoria` (registry repository: `game-scriptoria`).

- `characters/explorer/`: original Meshy model, optimized meshes, Blender sources, rig revisions, animated exports and review images.
- `scripts/`: Blender production and validation tools, plus the historical Babylon load probe.
- `docs/`: source inspection, optimization, rigging and animation reports, including measured data and limitations.

On 2026-10-26 (C1 Stage 2a) 296 redundant individual preview renders were pruned (`previews/rig-v2/{textured,clay}/` and `previews/anim/{textured,clay}/`) and, in Stage 2b, 100 more from `previews/rig-v1/` (the historical deformation baseline keeps 4 representative renders and its 3 sheets) and, in Stage 2c, 57 clay body-view renders from `previews/rig-v3/clay/` (its 30 clay close-ups, all textured renders and sheet remain); in C3a, 71 of the 78 optimization renders in `previews/{textured,clay}/` (7 representatives and all 32 `previews/comparison/` sheets, which contain the removed renders pixel for pixel, remain); representative renders and all contact sheets remain, and the removed paths are recorded in the `excluded` list of `docs/collection-import.json`. The source model's original and `source/` copies are intentionally preserved; the inspection report documents this duplication. The import makes no new licence or approval claim. Original files remain untouched. See the [import guide](../../docs/collection-imports.md) and [checksum manifest](../../docs/collection-import.json) for provenance, exclusions, LFS and script-path limitations.
