# M7.2 animated astronaut export candidate

Local asset preparation, 2026-10-12. Blender **5.2.2 LTS** in background mode.
The assembled source previously passed the owner's manual visual review.

**Status: technically valid candidate, not unconditional final approval.**
The exported Walk retains existing boot penetration. Review that ground-contact
issue and explicitly accept the measured four-influence conversion before calling
the asset final. No source asset, Gateway runtime, feature flag, repository data,
dependency, commit, deployment or publication was changed.

## Deliverable and identity

- Output: `../../../astronaut/animated/m7.2/astronaut-animated-candidate.glb`
- Size: **4,237,980 bytes**, 4.238 MB / 4.042 MiB.
- SHA-256: `63c9b16b613931d9a5285aaee3db35bcb1f0619fcbd464b04553455c1810a53e`.
- Source: `../../../astronaut/animated/m7.2/astronaut-assembled.blend`.
- Source SHA-256: `e5d5bdadf31fafed416c3e919eec2f142a6d794109e0409f47b35c8c20cda193`.
- One intended skinned mesh, one material, one skin with **41 original joints**.
- **10,357 triangles**, unchanged. glTF has **11,188 render vertices** versus
  11,181 source vertices; export splits seven attribute discontinuities without
  adding triangles. Position, UV and named-weight correspondence was checked.
- Exactly two independent clips: **Idle 8.333333 s**, **Walk 1.033333 s**.
  Both start at zero; source ranges are 1-251 and 1-32 at 30 FPS.

The five inputs in `export-validation.json` were SHA-256 checked before/after.
The working blend, assembled blend, Idle/Walk FBXs and original 1K GLB are unchanged.
The assembled blend was opened read-only for processing; no blend was saved.

## Export choices

- Self-contained GLB 2.0; select only `Armature` and `output_unwrapped`.
- Preserve geometry, hierarchy, original object scale relationships and material.
  No modifier/transform application, extra leaf bones, cameras, lights, morphs,
  Draco, gltfpack, required decoder extensions or external image URIs.
- Four float skin weights per vertex (`JOINTS_0` / `WEIGHTS_0`), valid joint indices,
  normalized nonnegative weights and finite invertible inverse bind matrices.
- Actions mode, active Idle plus a separate muted Walk NLA stash **only in memory**.
  Force sampling every frame; optimize duplicate animation keys; each clip starts
  at zero. No merged timeline, artificial frames or trimmed duration.
- Current-frame node transforms at Idle frame 1, rather than a centered bind-pose
  presentation. Inverse bind matrices and animation channels retain proper skinning.
- Y-up export, **+Z-forward**; Blender inspection equivalent is Z-up / -Y-forward.
  Source facing and overall scale were preserved; no 180-degree facing correction
  or previous static-source centering correction was applied.
- Constant **+0.0096075517** Blender-world Z placement offset, equivalent to glTF Y,
  places the approved Idle reference soles at ground level. No animated root keys
  were changed. Default Three scene height is **1.891089 m** and minimum Y is
  approximately zero. This is a placement correction, not a gait correction.
- PNG automatic image mode preserves the three packed source image payloads
  **byte-for-byte**: base color, normal and metallic/roughness, all **1024x1024**.
  Their total payload remains 3,411,804 bytes. Correct PBR texture slots are present;
  metallic uses B and roughness G of the same original packed map.

The approximate 4 MB target is exceeded by about 6%, explained by added skeleton,
skin and clips. No additional lossy texture reduction was used to force that target.

## Skinning impact

The source has **522 vertices with five influences and 35 with six**, 557 total.
Only the temporary export scene retains each vertex's strongest four positive
weights and renormalizes them. The original weights remain in the assembled file.
Maximum discarded tail is **0.085863**; the effect was measured before export.

| Comparison | Idle max / mean | Walk max / mean |
| --- | --- | --- |
| Four-influence temporary mesh vs approved source | 8.772 / 0.0190 mm | 9.301 / 0.0219 mm |
| Reimported GLB vs approved source | 8.772 / 0.0202 mm | 9.299 / 0.0235 mm |
| Reimported GLB vs four-influence export input | 0.0119 / 0.00120 mm | 0.0284 / 0.00155 mm |

Distances use preserved glTF meter units. The first two rows quantify an intentional
skinning approximation, not a lossless conversion. Worst source vertices are the
neck/shoulder region at Idle frame 56 and wrist/glove at Walk frame 12.
Among the 557 affected vertices, mean reduction error is 0.381 mm Idle / 0.439 mm
Walk, with 95th percentile 1.810 mm / 2.052 mm.

The installed Blender exporter also removes influences <= 0.0001 on **1,204
vertices**, then normalizes. That inspected exporter behavior is accounted for in
weight correspondence and included in the third row's measured deformation error.
No exporter or source-file patch was made.

Matching full-body front/back renders and 512px neck/wrist closeups were inspected.
Helmet, backpack, shoulders and knees remain coherent; no obvious tearing or major
silhouette damage appeared. Closeups show small local shape/shading differences.
This preview review is not a substitute for the owner's moving, close-range review
of the newly reduced skin, nor validation of future animation clips.

## Animation and import validation

Compared **501 Idle + 63 Walk** integer/half frames: **564 poses**, **23,124 joint
comparisons**, plus every imported mesh vertex at those poses.

| Metric | Idle | Walk |
| --- | --- | --- |
| Maximum joint head position error | 0.00594 mm | 0.00619 mm |
| Mean joint head position error | 0.00280 mm | 0.00286 mm |
| Maximum relative world rotation error | 0.0000514 degrees | 0.000312 degrees |
| Mean relative world rotation error | 0.0000149 degrees | 0.000117 degrees |
| Net horizontal hips displacement | 0 | 0.0000000120 m |

Both clips retain cyclical hips sway; endpoint translation has no significant
horizontal drift. Motion was compared after subtracting the documented constant
ground offset. Joint heads and relative world rotations account for Blender
importer's bone-axis/rest reconstruction instead of comparing incompatible rolls.

Fresh Blender import confirms the intended mesh, 41-bone armature, two named
actions, exact durations, armature modifier, three linked maps and valid skinning.
The importer creates an **Icosphere custom bone-display helper**; it is not a second
asset mesh and does not exist in the GLB. glTF binary structure independently has
one mesh and one skin. Imported animation keys are zero-based (0-250 / 0-31), while
NLA stashes start at frame 1; active-action comparisons correctly use source frame
minus one. Vertex matching additionally checks UVs (max error zero), bone weights
(max error 1.07e-7) and equivalent coincident trajectories.

An offline check with Gateway's installed **Three revision 186** GLTFLoader and
AnimationMixer passes: one SkinnedMesh, 41 bones, two clips, embedded decoded 1K
maps, four weights and correct Y-up default grounding. It compares all joints at
four Idle/six Walk times against source world heads converted to glTF axes:
maximum errors **0.000704 mm / 0.001247 mm**; no significant root drift.
Three sanitizes bone namespaces for its animation bindings; clip names stay intact.
This uses a local Sharp ImageBitmap stand-in and CPU transforms, **not GPU rendering
or Gateway runtime integration**. No package installation or browser matrix.

## Ground contact: unresolved

- Idle soles are on the floor in the reference pose; across all sampled Idle poses
  the lowest point is 0 to +0.485 mm above it.
- Walk lowest point is **-45.126 mm** at source frame **23.5** (imported frame 22.5).
  At that pose **46 mesh vertices** lie more than 1 mm below the floor.
- This is retained source penetration: the original Walk reaches -54.733 mm before
  the +9.608 mm placement offset. Four-influence reduction does not change the
  source ground minima; export/import contributes negligible additional error.
- The diagnostic **1 mm floor-clearance check fails**. All other 32 binary/import/
  correspondence/motion checks pass. `allChecksPassed` is intentionally **false**.
- The sole/heel intersection is visible in the dedicated boot closeup. A ground-
  contact correction or explicit acceptance of the stylized boot intersection is
  needed before final approval. Raising the whole asset another 45 mm would make
  Idle float; no per-frame root lift, foot locking or IK was silently applied.

For a correction, preserve these sources and author a separate ground-contact
derivative, then recheck gait, loop boundaries, Idle/Walk transitions, deformation
and in-place motion. This export task does not alter the manually approved gait.

## Evidence and automation

- `export-validation.json`: authoritative final binary + fresh Blender report.
- `approval-summary.json`: final asset hash guard, visual findings and approval status.
- `skinning-analysis.json`: source weights and pre-export reduction measurements.
- `source-samples.npz`: evaluated source poses, world joint transforms and rest
  positions for repeatable comparisons; inspection evidence only.
- `three-validation.json` / `engine-reference.json`: offline loader/mixer evidence.
- `ground-inspection.json`: lowest vertex and foot/toe joint positions.
- `export-comparison.png`: approved source / four-influence / GLB roundtrip poses.
- `skinning-closeups.png`: neck/wrist source-to-candidate comparisons.
- `walk-worst-ground-full.png` / `walk-worst-ground-boots.png`: ground intersection.
- Individual review PNGs are kept beside the comparison sheets.
- `initial-validation-diagnostic.json`, `roundtrip-diagnosis.json` and
  `correspondence-diagnosis.json` preserve intermediate **validator diagnostics**,
  not final asset results. Initial checks incorrectly used one-based imported keys,
  counted a display helper, and did not model the exporter's tiny-weight cleanup.
  Those issues were corrected without re-exporting or changing the candidate bytes.
  The rest-only inspection snapshot was corrected to use the mesh world matrix;
  evaluated animation samples were independent of that field.
- Some Blender extension/font cache writes were denied by the sandbox. Asset
  import/export, image generation and final validation completed successfully.
- `git diff --check` passed. Gateway's pre-existing untracked M7.1 documentation and
  offline preparation script remain unchanged; no production/build tests required.

Scripts are separate from source assets. Export refuses to overwrite an existing
candidate. Example commands from PowerShell:

```powershell
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$exportTools = 'D:\Code\porto-projects\gateway-assets\automation\m7.2\export'
# Existing candidate: validation only; does not rewrite its bytes.
& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 --python "$exportTools\export_and_validate.py" -- --validate-only --no-renders
node "$exportTools\check_three.mjs"
```

Initial workflow for a **new, non-existing output/version** is:
`measure_skinning.py` -> inspect source/reduced renders ->
`export_and_validate.py` -> inspect `export-comparison.png` ->
`inspect_ground.py` / `review_skin_closeups.py` -> `check_three.mjs`.
The measurements guard against overwriting existing inspection snapshots too.
Use `compose_comparisons.cjs` for full-body sheets and `--closeups` for the closeups.

## Final acceptance still needed

1. Resolve or explicitly accept the retained Walk floor intersection.
2. Owner review of candidate playback/loops and closeup skin changes, especially
   neck and wrist; the previous approval was for the six-influence assembled source.
3. Existing Meshy/Mixamo redistribution/attribution provenance remains unresolved
   for public release. This local export neither grants rights nor publishes it.
4. A later separately authorized runtime milestone should check real GPU appearance,
   Idle/Walk blending and actual device cost. No runtime integration was performed.
