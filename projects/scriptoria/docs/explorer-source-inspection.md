# Explorer (neutral) — Source Asset Inspection

Milestone: M7.5c.1d · Inspected 2026-10-15 · Blender 5.2.2 LTS (CLI, `--factory-startup`)

Everything below was measured by `scripts/blender/inspect_glb.py`, which imports the file into an empty Blender scene and also parses the GLB's raw JSON chunk. Previously reported specifications were not reused. Raw output: [`data/inspect-source.json`](data/inspect-source.json).

## File

| Item | Value |
| --- | --- |
| Expected path | `characters/explorer/source/explorer-neutral-meshy-original.glb` |
| Where it actually was | `characters/explorer/explorer-neutral-meshy-original.glb` (one level up; `source/` was empty) |
| Action taken | **Copied** (not moved or renamed) into `source/`. Both copies have identical SHA-256 `0fd99a25…a13c74e7f`, confirmed again after all processing. The original at its old location is untouched. |
| Size | 8,983,896 bytes (8.57 MiB) |
| Container | GLB, glTF 2.0, generator `pygltflib@v1.16.5` |
| Extensions used / required | none / none |

## Geometry

| Item | Value |
| --- | --- |
| Meshes / primitives / nodes | 1 / 1 / 1 (object `Mesh_0`, identity transform) |
| Triangles | **119,246** (Blender loop triangles = raw index count / 3) |
| Vertices | 68,827 as stored (split along UV seams); **59,593 unique positions** after welding at 1e-5 m |
| Face types | all triangles (0 quads, 0 n-gons) |
| Vertex attributes | `POSITION`, `NORMAL`, `TEXCOORD_0` (no colors, tangents, joints or weights) |
| Custom normals | Present (imported as custom split normals); all faces smooth-shaded |
| Shape keys / vertex groups | 0 / 0 |

## Materials and textures

| Item | Value |
| --- | --- |
| Materials | 1 (unnamed in the file; imported as `Material_0`) |
| Base color | 2048×2048 JPEG, 2,122,872 B, sRGB |
| Metallic-roughness | 2048×2048 JPEG, 1,524,685 B. Channel means: R = 1.00 (unused by glTF), G (roughness) ≈ 0.57, B (metallic) ≈ 0.002, so effectively non-metallic despite `metallicFactor: 1.0` |
| Normal | 2048×2048 JPEG, 1,700,590 B, tangent space |
| Emissive | **none.** The cyan "illuminated" details are painted into the base color; nothing actually emits light. |
| Alpha / double-sided | `OPAQUE` / `doubleSided: true` |
| Textures embedded | yes, all three in the GLB binary chunk (5,348,147 B, about 60% of the file) |

## UVs

One UV map (`UVMap`), with every UV coordinate inside 0–1. The mesh has 348 connected pieces as stored, which equals its UV-island count, because Meshy splits vertices along every UV seam.

## Dimensions and orientation

| Item | Value |
| --- | --- |
| Bounds (Blender Z-up) | X −0.553…0.548, Y −0.193…0.196, Z −0.951…0.947 |
| Size | **1.101 m wide** (A-pose arm span) × **0.388 m deep** × **1.898 m tall** |
| Origin | At the body's **center** (z = 0 is mid-height), **not** at the feet |
| Facing | Front faces Blender −Y, which is glTF +Z (verified in the front-camera renders) |
| Pose | A-pose, arms about 45° below horizontal (visual) |

## Rig and animation

No armature, skin, joints or animations, either in the raw JSON or after import.

## Topology observations

- **The seam-split mesh is closed underneath.** As stored there are 17,712 boundary edges, which also count as non-manifold. After welding coincident vertices (1e-5 m) there are **0 boundary edges and 0 non-manifold edges**: a closed, manifold surface. Every "hole" was a UV-seam split.
- It is a typical image-to-3D triangulation: uniformly dense, with no edge loops or quad flow. That is fine for static rendering, but it gives no deformation-friendly loops at the shoulders, elbows, knees or fingers (relevant for rigging).
- The head region (top 0.25 m of the bounds, so head plus hair plus the top of the collar) holds 30,959 triangles, **26%** of the total. The split between hair and face was not measured.
- No loose vertices.

## Implications noted for later milestones (not acted on here)

- The origin is at the center, not the feet, and the height is 1.898 m. The game plan (`code-fps` M7.5 plan §5.3) assumes feet-origin and about 1.72–1.78 m. Re-origin and scale belong to rigging or integration, not this milestone.
- `doubleSided: true` on a closed mesh disables back-face culling for no visual benefit.
- No emissive map: the cyan details will not glow in Babylon unless an emissive mask is authored later.
