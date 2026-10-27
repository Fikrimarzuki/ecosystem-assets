# M7.2 — Final astronaut export validation

**Local asset validation passed; ready for final asset approval.** Exported with
Blender **5.2.2 LTS** in background mode. The corrected source was already manually
approved by the owner. Fresh Blender reimport, offline Three.js playback and matched
deformation renders passed. This does not approve public release or runtime integration.

## Output and identity

- Output: `../../../astronaut/animated/m7.2/astronaut-animated.glb`
  (absolute: `D:/Code/porto-projects/gateway-assets/astronaut/animated/m7.2/astronaut-animated.glb`).
- Size: **4,982,776 bytes / 4.98 MB / 4.75 MiB**.
- SHA-256: **`cbe687ee68998b318a9faebcb1a9c93697f50419e9624ab6c1f6b5c278362544`**.
- Source: `astronaut-ground-corrected.blend`, unchanged SHA-256
  `ef7b3984d25fbe0a82dfdf921b83388c1d4e04932ca0e2b899a658c5379019f0`.
- Previous candidate remains unchanged, SHA-256
  `63c9b16b613931d9a5285aaee3db35bcb1f0619fcbd464b04553455c1810a53e`.
- Protected-input hashes before/after are in [export-validation.json](export-validation.json).
  No source GLB, FBX or BLEND was saved, replaced or renamed.

## Export settings and structure

Selected mesh `output_unwrapped` and `Armature` only. GLB 2.0, Y-up conversion,
PBR material export, AUTO embedded PNGs, ACTIONS mode, independent clips slid to
zero, sampled bone transforms, four influences, animation-size optimization.
No transform application, geometry simplification, morphs, leaf bones, cameras,
lights, reference objects, Draco, gltfpack or required decoder extensions.

| Property | Final result |
| --- | --- |
| Skinned meshes / primitives / materials | **1 / 1 / 1** |
| Triangles | **10,357**, unchanged |
| Source vertices / exported vertices | **11,181 / 11,188**; existing seven attribute-seam splits |
| Skins / joints | **1 / 41**, original named hierarchy |
| Skin attributes | `JOINTS_0`, `WEIGHTS_0`; normalized, finite, valid joint indices |
| Inverse bind matrices | 41 finite, invertible matrices; identical to previous candidate |
| Clips | Exactly **Idle**, **Walk** |
| Idle duration | **8.333333015 s** |
| Walk duration | **1.033333302 s** |
| Images | Three embedded **1024 × 1024 RGB PNGs** |

The corrected Walk contains 1/8-source-frame keys. All actions were retimed **only
in memory** by factor eight around frame 1, with export FPS changed from 30 to 240.
This preserves durations while retaining the correction's **240 Hz** sampling.
Idle has up to 2,001 keys per sampler, Walk 249. The source remains at 30 FPS.
Constant-channel optimization is enabled; animations remain independent. Imported
actions span 0–2000 and 0–248 at 240 FPS. glTF playback uses seconds, not scene FPS.

Blender's fresh importer creates an Icosphere bone-display helper. It is not an
exported mesh; binary inspection and Three both confirm exactly one asset mesh.
Blender's shared metallic/roughness image-sampler warning was checked: PBR bindings,
samplers and image bytes match the previous validated candidate. Cache-write warnings
from Blender/fontconfig did not prevent inspection or export.

## Animation, scale and ground validation

**Fresh empty Blender scene:** compared **501 Idle poses** (60 Hz) and **993 Walk
poses** (960 Hz), including between export keys. UVs and named weights independently
verify source/import vertex correspondence. Joint motion is compared in world space
with relative rotations, avoiding importer bone-roll differences.

| Measurement | Idle | Corrected Walk |
| --- | --- | --- |
| Maximum joint-position error vs corrected source | **0.00595 mm** | **0.00805 mm** |
| Maximum relative joint-rotation error | **0.000052°** | **0.001263°** |
| Maximum additional mesh error vs four-influence input | **0.01197 mm** | **0.02796 mm** |
| Mean additional mesh error | **0.00120 mm** | **0.00158 mm** |
| Minimum left boot clearance | **1.44048 mm** | **0.71374 mm** |
| Minimum right boot clearance | **0.000036 mm** | **0.70350 mm** |
| Accumulated horizontal hips endpoint drift | **0** | **0.000012 mm** |

Applied **+0.009607551704849298 m** to the armature's Blender world Z in the export
scene; its parented mesh follows. This becomes glTF Y and is already included in
the output. No Idle curves were edited, no additional gait correction was made,
and hips oscillation was retained. No ground correction is needed after this export.

**Offline Three r186:** GLTFLoader parsed embedded images using existing Sharp as
an ImageBitmap stand-in. AnimationMixer matched 492 source joint comparisons with
maximum error **0.00110 mm**, played each clip alone, and observed two LoopRepeat
cycles per clip with repeated-pose error below 1e-14 m. CPU skin evaluation across
**993 Walk samples / 960 Hz** measured minimum Y **+0.70267 mm**, **zero penetration**.
These are CPU checks, not GPU uploads or browser performance measurements.

The asset is upright **Y-up, +Z-forward**, with glTF meter units and no rescaling.
Default standing Idle bounds are approximately X **−0.44438…+0.45319 m**, Y
**0…1.89109 m**, Z **−0.37423…+0.39141 m**. Front/back renders verify facing direction;
Three bounds and joint positions independently verify conversion and placement.

## Skinning and visual review

Retained the same previously validated reduction: **557 vertices** with more than
four positive weights (maximum six) keep their strongest four and are normalized
in memory. Maximum removed weight sum is **0.085863**. Exporter's existing <=0.0001
weight cleanup is included in measured roundtrip error. Final joint/weight buffers
are **byte-identical to the previous candidate**; source skinning is untouched.

Versus the original six-influence corrected source, maximum displacement is
**8.772 mm Idle / 9.299 mm Walk**; all-vertex mean **0.0202 / 0.0240 mm**. These are
existing reduction costs, distinct from the tiny additional GLB roundtrip error.
Detailed region statistics are in the JSON: helmet/neck, shoulders, wrists,
backpack, knees and boots. Region masks are bone-weight proxies, not separate
anatomical mesh parts, and may overlap.

[Overview](deformation-overview.png) and [closeups](deformation-closeups.png) compare
the untouched corrected six-influence source with the final reimport. Reviewed
Idle frame 56 (neck/helmet/shoulder and backpack), Walk 12 (wrist), 23 (knees) and
23.75 (boots). No obvious new collapse, tearing or silhouette degradation appeared.
Existing stylized faceting and neck/limb crease shapes remain; this is not a claim
of zero-loss influence reduction. Initial closeup cameras were too near the geometry;
only those inspection views were moved farther away and rerendered. No asset changed.

## Previous-candidate comparison

See [previous-comparison.json](previous-comparison.json). **No unexpected differences.**
Positions, normals, UVs, indices, joint weights/indices, inverse binds, node hierarchy,
material definitions, texture samplers and all embedded texture payloads match exactly.
Idle transforms at every previous sample are exactly equal. Walk changes at previous
sample times are confined to the six intended leg bones. Names/durations are unchanged.

File size increased **744,796 bytes / 17.57%** from 4,237,980 bytes because of dense
animation sampling. The approximately 4 MB earlier target is exceeded modestly to
preserve the subframe ground correction; texture/geometry complexity has not increased.
Do not reduce Walk sampling without repeating dense ground validation.

## Textures

Original PBR material **AstronautOriginalPBR** is preserved. Base color uses sRGB;
normal and metallic/roughness use data color space. MR uses B for metallic/G for
roughness. All four Three material map slots resolve to the correct three images.
Embedded PNG payloads are **byte-identical** to the prepared original GLB:

| Map | Bytes | SHA-256 |
| --- | --- | --- |
| Base color | 1,312,224 | `3d7f4fb3fe6b522d4ee95343d4789d6750ba46115e90e3f82b4718101102012e` |
| Normal | 1,287,000 | `846aaa38810c512dcd4f05a27c45874267202a4d7c5fa0328cddd3188fc7e2ae` |
| Metallic/roughness | 812,580 | `5370b50c50c889b9905a2e137ef9bc21987cbf05f6d7b998368f72d1851a526f` |

## Evidence, automation and remaining risks

New files consist of the GLB and this separate `automation/m7.2/final/` directory:
eight Python/Node utilities, quantitative JSON reports, a source-sample NPZ,
engine reference JSON, 16 matched render PNGs, two comparison sheets, this report,
the [integration contract](integration-contract.md), and consolidated
[final-validation.json](final-validation.json). Prior workflows/evidence are unchanged.

Workflow: `prepare_validation.py` → `export_and_validate.py -- --no-renders` →
`check_three.mjs`; `compare_previous.py`, `review_deformation.py` and
`compose_review.cjs` supply comparisons. Python runs inside installed Blender;
Node uses Gateway's installed Three/Sharp. Export refuses an existing output;
do not remove that safeguard. Full settings/hashes are recorded in JSON.

- Local technical checks passed; final binary is ready for owner approval.
- Asset-specific **Meshy/Mixamo provenance, redistribution and attribution rights
  remain undocumented locally**, so publication remains blocked on that evidence.
- Real WebGL upload, representative hardware memory/FPS, live transitions and
  movement-speed synchronization remain integration checks. No browser matrix,
  Universe regression, production build or runtime modification was needed.
- Existing Walk endpoint velocity mismatch inherited from native gait remains;
  endpoint pose/root drift and repeated playback pass. Runtime crossfades have not
  been assessed, and two clear clips alone do not guarantee clear blended contacts.
- Still renders sample representative worst regions; they do not substitute for
  final binary playback review under intended runtime lighting.
- Scripts passed syntax/whitespace checks. Gateway `git diff --check` passed;
  its two pre-existing untracked M7.1 files were not changed. No dependencies,
  commit, push, publication or deployment.
