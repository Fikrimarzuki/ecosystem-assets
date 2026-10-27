# M7.2 assembled astronaut — manual review handoff

Created using Blender 5.2.2 LTS. This is a separate local Blender assembly, not a GLB export or runtime integration.

## Files

- `../../astronaut/animated/m7.2/astronaut-assembled.blend` — one intended skinned mesh and one Idle armature; actions `Idle` and `Walk`; three packed original 1K textures.
- `assemble_astronaut.py` — automated assembly with fixed input hashes, pose-error gates and no input/output overwrite. Refuses to run if the assembled output already exists.
- `review_assembled.py` — reopen validation and six temporary PBR inspection renders. Render-only camera/lights/ground are never saved into the assembled blend.
- `verify_saved_assembly.py` and `saved-file-validation.json` — independent reopened-file comparison confirms unchanged Idle curves, mesh/UV/weights/rest matrices and byte-identical original embedded PNGs.
- `assembly-validation.json` — full 63-frame/41-bone pose comparison, clip ground/hips/foot samples, deformation indicators and input/output hashes.
- `assembly-contact-sheet.png` plus six `review-*.png` — local appearance review artifacts.

Use `blender.exe --background --factory-startup --disable-autoexec --python-exit-code 1 --python <script>` with Blender 5.2.2. Scripts are outside source asset directories. No source asset is overwritten. No GLB exporter is called.

## Retargeting

Evaluate the native Walk skeleton's world-space bone matrices; convert them into target-armature coordinates and solve each target local basis with `Bone.convert_local_to_pose(..., invert=True)` using the unchanged target rest matrix and the desired parent's pose matrix. Bake location/quaternion/scale at 30 FPS with quaternion sign continuity and linear keys. This compensates the different bind/rest frames; it does not reuse the source F-curves or alter the target bind skeleton/weights.

Validate all 41 bones over all 32 integer Walk frames and 31 half frames (2,583 bone-pose comparisons). Maximum/average head-position error: **1.98745e-6 / 3.98191e-7 Blender units**. Maximum/average orientation error: **0.00019764° / 0.00002238°**. No significant retargeting error was found at those samples. Native animation is a reference, not a proof that auto skinning is visually perfect.

Idle F-curves, target rest matrices, original mesh vertices/UVs, parenting, transforms, vertex groups/weights and Armature modifier are unchanged. The source GLB material is assigned to the existing skinned mesh; three 1024² packed images preserve base-color, normal, and blue-metallic/green-roughness connections. Temporary imported armature/reference mesh and the native temporary action are removed.

## Manual review

The file opens on Idle frame 1 with the armature selected. Select `Idle` or `Walk` in the Action Editor; both are kept with fake users. There are no NLA tracks blending them. Review:

- **Idle:** frames 1–251, 30 FPS, 8.333 seconds. Scene end is 251 so the final source key is retained.
- **Walk:** frames 1–32, 30 FPS, 1.033 seconds; set playback end to 32 for a Walk loop.
- Front/back helmet and backpack, shoulders/elbows and knees/boots at frames 1, 8, 16, 24 and 32; inspect motion between frames and loop contact/sliding as well as silhouettes.

The six PBR stills preserve the recognizable white/teal character, coherent limb poses and helmet shape. The rear still does not show catastrophic backpack collapse; it does not clear every local weight artifact. Detailed deform/ground review remains required before any final export.

## Remaining limitations — not corrected silently

- Mesh minima reach **−0.009608** (Idle) and **−0.054614** (Walk) against the Z=0 Blender ground reference. Walk foot/ground alignment needs review. A per-frame vertical correction would change native poses and has not been applied.
- Walk hips end-minus-start horizontal displacement is **1.15674e-8 units**, effectively zero; vertical difference is −1.19209e-7. Native lateral sway and bob remain. No accumulated forward motion was introduced.
- Helmet edge ratios stay approximately **0.980–1.017**. Automatic weighting produces more significant local edge changes at backpack/shoulders/knees; per-frame pooled p95 ratios are **1.652 / 1.217 / 1.314**, with isolated maxima **5.124 / 4.570 / 2.782**. Ratios include short edges and articulation, so they flag inspection regions rather than establish a visible defect or absolute deformation tolerance. Existing weights are intentionally preserved.
- The original auto rig has up to six influences; four-influence GLB compatibility/deformation acceptance remains future work. No weights were reduced, normalized again or repainted here.
- Rig/object unit conversion is unchanged. Ground/forward orientation and scale normalization must be planned consistently for final export; do not apply independent mesh/rig transforms or the former static-model pivot offset blindly.
- Licensing/publication approval and eventual GLB/Three playback verification remain outstanding.

**Ready for manual visual inspection; not signed off for final GLB export or runtime release.** Source hashes remained unchanged; no Gateway code, source asset, commit, push or deployment was modified.
