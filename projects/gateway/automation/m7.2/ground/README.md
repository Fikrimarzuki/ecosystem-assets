# M7.2 Walk boot-contact investigation and correction

Local-only Blender **5.2.2 LTS**, 2026-10-12. No GLB export, runtime change,
dependency installation, commit, push, deployment or publication.

**Created:** `../../../astronaut/animated/m7.2/astronaut-ground-corrected.blend`

- 4,885,962 bytes; SHA-256
  `ef7b3984d25fbe0a82dfdf921b83388c1d4e04932ca0e2b899a658c5379019f0`.
- One original skinned mesh/material, 41-bone armature, 11,181 vertices,
  10,357 triangles and exactly `Idle` / `Walk` actions.
- `Idle`: frames 1-251, 8.333333 seconds. `Walk`: frames 1-32, 1.033333 seconds.
- Default active action/timeline: **Walk, 1-32**, ready for manual playback.
- **Ready for manual visual inspection, not final animation approval.**

The original assembled blend, first animated GLB, Idle/Walk FBXs and 1K source
material GLB are hash-guarded and unchanged. In particular the first GLB stays at
SHA `63c9b16b613931d9a5285aaee3db35bcb1f0619fcbd464b04553455c1810a53e`.
No existing source file was overwritten. All scripts/reports/renders are separate
from the asset directory in this new `automation/m7.2/ground` folder.

## Ground reference: preserve Idle exactly

All clearances below use the **same +9.6075517 mm common placement offset** as the
first GLB. In the source Blender coordinate system, that means a reference floor
at **Z = -0.0096075517**. Comparison renders use that floor.

The new blend deliberately preserves original object transforms and **exact Idle
world poses**, so this common placement offset is **not baked into the blend's
objects or Idle keys**. The saved scene has no inspection floor/cameras/lights.
For manual floor inspection, put a temporary floor at Z = -0.0096075517, or preview
a copy with the same +0.0096075517 common world-Z offset. A future export must apply
that existing placement offset once, not twice. The corrected Walk otherwise sits
about 8.9 mm below Blender's zero grid; that is the preserved coordinate reference,
not a return of the 45 mm Walk-specific penetration. Metadata records both values.

## Phase 1: diagnosis and source attribution

The astronaut is **one mesh**, not separate boot objects. Fixed rest-space regions
isolate the Left boot/cuff (954 vertices) and Right boot/cuff (974 vertices): below
the respective ankle head plus 0.12 m, split by rest X side. Every mesh vertex that
penetrated the floor during diagnosis was within these regions. Regions include
boot cuffs; they were not manually cut or detached from the mesh.

Diagnosis samples **249 poses at 1/8 frame / 240 Hz** through the entire cycle,
including between every native 30 FPS key. `diagnosis.json` records per-side lowest
vertex/position, ankle/toe positions, foot world quaternion, velocity, hip height,
native comparison and contact/swing/transition estimates for every sample.

- Left minimum: **-29.006 mm**, frame 9.
- Right minimum: **-45.215 mm**, frame 23.75; denser final sampling finds
  **-45.221 mm**. This slightly exceeds the first GLB audit's -45.126 mm because
  sampling is denser and the assembled source retains its original six-influence
  skin rather than the GLB's four-influence approximation.
- Hip height ranges **697.728-779.512 mm**, an existing 81.785 mm excursion.
  The initial Idle-derived floor reference is valid; it does not accommodate the
  rolled heel during walking simply by being shifted globally.
- At the two worst frames, substituting the Idle **foot world orientation** while
  keeping the same ankle and hips positions changes clearance from -29.006 to
  **-4.859 mm** Left and -45.215 to **-2.485 mm** Right. Foot rotation differs from
  Idle by 27.59 / 44.60 degrees at those poses. The lowest vertices are over 92%
  weighted to the Foot bone. This implicates rolled heel geometry relative to the
  ankle, with smaller baseline height/skinning effects; it is not solely hips height.

### Native Mixamo comparison and its limit

The native Walk FBX is **Without Skin**, so there is no native skinned boot surface
to inspect independently. Both hierarchies have the same 41 names/parents. Compare
native evaluated world poses with the assembled Walk at all 249 samples:

- Maximum joint-position difference **0.00200 mm**, mean **0.000406 mm**.
- Maximum bone-orientation difference **0.000210 degrees**.
- Apply native world poses directly through the original Idle inverse binds in a
  temporary, rest-aware target evaluation: maximum mesh difference **0.00131 mm**,
  mean **0.000142 mm**; boot minima reproduce the same intersection.

**Conclusion:** no material numerical error was introduced by the existing
rest-aware bake. Native pose + the approved astronaut's bind/skinning/boot geometry
already reproduces the problem. The dominant issue is the walking foot roll and
stylized heel envelope interacting with that native pose. This does **not** prove
that an independently skinned native Mixamo character would penetrate: a Walk
With Skin export would be needed to separate original auto-rig/bind choices from
native animation/geometry behavior conclusively. No such source was invented.

### Contact inference

Broad stance: backward ankle travel relative to the in-place body (+Y in Blender),
velocity >0.08 m/s with low boot geometry. Swing: opposite travel; transitions kept
separate. More specific contact for before/after comparisons uses original backward
ankle velocity >0.08 m/s and original ToeBase height <20 mm over the reference floor.
Correction blending fades across 20-40 mm toe height and 0-0.08 m/s ankle velocity.

These are **kinematic estimates**, not ground sensors, physical contact simulation
or manually annotated phases. Before/after statistics use the same original-pose
contact labels so the correction cannot improve its score by changing the labels.

## Phase 2: least invasive method selected

A varying whole-character lift would require up to 45.215 mm and make the other
backward-travelling stance boot float up to **39.576 mm Left / 32.702 mm Right**.
It also changes the existing hips bob. That approach was rejected; neither the
character nor the pelvis is raised by the maximum penetration.

Use **independent foot-specific vertical correction**, evaluated offline:

1. Preserve the original hips/root trajectory and each foot's horizontal path and
   world rotation. Infer contacts from the original motion.
2. Solve minimum ankle height for 0.5 mm boot clearance using the actual deformed
   boot geometry, not just the ankle/toe joint. During confidently inferred contact,
   permit small downward corrections to reduce existing positive sole gaps.
3. Solve thigh/shin analytically as a two-bone chain, preserving original lengths,
   the projected original knee bend plane and minimal rotational change. Restore
   original foot world rotation at the new ankle target. No knee flip or bone stretch.
4. Smooth periodic vertical targets with a Gaussian sigma of **0.25 source frame**.
   Add localized, periodic clearance envelopes (sigma 0.5 frame), plus only **0.25 mm**
   numerical margin. This avoids a constant 45 mm body lift and unnecessary stance
   padding throughout the cycle.
5. Bake location/quaternion channels of **UpLeg, Leg, Foot on both sides** at 1/8
   frame / 240 Hz. Toe channels and all other original Walk curves remain unchanged;
   toes move through their corrected Foot parent. The original Scale channels remain.
6. Match first/last correction interval slopes by adjusting only frames 1.125 and
   31.875 by at most **0.04465 mm**. Seam poses stay unchanged. No live IK constraints,
   extra bones, controllers or new animation dependency remain in the saved file.

This is a baked IK authoring solution, **not a runtime IK system**. Foot-specific
correction was necessary because a swing heel can penetrate while the opposite boot
is already near the floor. A pelvis-only correction cannot preserve that contact.

Earlier lift-only/global-padding trials are preserved as evidence. The selected
local-envelope/contact version reduces unwanted stance gaps. The final seam tweak
was revalidated without repeating the unaffected still renders.

## Phase 3: final before/after validation

**993 poses at 1/32 frame / 960 Hz**, including four interior samples per baked
interval. Source/updated Walk compared at every pose; fresh-process saved-file
verification repeats the same 993 boot-clearance samples.

| Measurement | Left | Right |
| --- | --- | --- |
| Source minimum clearance | -29.006 mm | -45.221 mm |
| Corrected minimum clearance | **+0.714 mm** | **+0.702 mm** |
| Maximum remaining penetration | **0** | **0** |
| Source maximum inferred-contact gap | 5.777 mm | 7.911 mm |
| Corrected maximum inferred-contact gap | **5.799 mm** | **3.312 mm** |
| Corrected mean inferred-contact gap | 1.007 mm | 0.929 mm |
| Corrected 95th-percentile inferred-contact gap | 1.766 mm | 1.402 mm |
| Maximum ankle lift | 29.469 mm | 45.786 mm |
| Maximum ankle lowering | 0.324 mm | 6.750 mm |
| Maximum ankle velocity change | 0.529 m/s | 0.809 m/s |

No sampled penetration remains. This is a **small-clearance solution, not exact
physical foot locking**; the brief left-contact maximum is essentially the original
5.8 mm gap and must be assessed in playback. The contact corrections largely hold
soles within about 1 mm of the floor while keeping airborne phases airborne.

Gait/pose changes are explicit, not claimed to be zero:

- Hips displacement **0** at every compared frame; the full original hips trajectory
  and bob remain unchanged. Horizontal root drift remains **1.16e-8 m** per loop.
- Maximum thigh world-rotation change **14.345 degrees**, shin **10.820 degrees**;
  maximum knee shift **70.717 mm** at Right frame 23. This is noticeable extra leg
  flex and requires manual moving review, even though stills look coherent.
- Maximum foot world-orientation difference **0.002184 degrees** (dense bake
  interpolation); horizontal ankle-path difference **0.01143 mm**.
- Maximum segment-length difference **0.000148 mm**: no appreciable stretch.
- Whole-mesh positional difference: maximum **76.699 mm**, mean **2.356 mm**.
  Skin vertices outside the affected leg hierarchy move **0**.
- Every unmodified Walk channel fingerprints identically. Idle fingerprints and
  fresh saved-file world poses at frames 1,126,251 are **exactly identical**.
- Mesh positions/topology/UV, all original vertex groups/weights (including >4
  influences), armature modifier/rest matrices/object transforms and packed PBR
  images fingerprint identically. No four-influence reduction was repeated here.

### Loop continuity

- Maximum joint-head endpoint difference is **0.000916 mm**, same as the source.
- Maximum bone endpoint rotation difference is **0.000358 degrees**, same as source.
- Native source ankle **velocity** seams already exist: 0.667 m/s Left / 0.156 m/s
  Right under one-sided sampling. The correction preserves their timing instead of
  silently smoothing the original gait. Added correction velocity seam is only
  **0.000067 m/s Left / 0.002726 m/s Right** after refinement.
- No new significant position jump or accumulated translation was found. Perfect
  velocity continuity is **not** claimed; inspect the existing loop cadence manually.

### Deformation review

Matching before/after front views at Left frame 9, Right frame 23.75, a side view
at maximum knee adjustment frame 23, and the worst heel closeup were inspected.
Knees flex more; ankle/boot shapes, hips and material surfaces remain coherent.
No obvious tearing, knee inversion or catastrophic compression appeared in these
stills. Upper-body poses and materials remain unchanged.

Regional edge measurements compare matching posed meshes, excluding original edges
shorter than 3 mm. 95th-percentile length ratios: boots **1.00575**, knees **1.02953**,
ankles **1.00322**, hips **1.01032**. Sparse outliers reach **1.649x** at knees and
**1.537x** in the broad hip/thigh region; maximum local edge differences are
22.70 / 17.64 mm. These are flags for close moving review, not proof of visible
damage. No original weights were edited to conceal such changes.

All explicit numerical safety gates pass (including contact gaps <7 mm, no
penetration, length/orientation/path tolerances, Idle/skin/channel preservation,
duration/root drift and seam pose continuity). These local authoring thresholds
are not a substitute for the owner's final gait-quality judgment.

## Manual inspection instructions and remaining risks

1. Open the **new corrected blend**; Walk is active with timeline 1-32 at 30 FPS.
2. Use a temporary reference floor at **Z=-0.0096075517** to inspect soles. The
   preserved zero-grid mismatch is documented above; no floor is saved in the asset.
3. Play several loops from front and side. Inspect heel-strike, toe-off, the Right
   swing lift around frames 21-25, knee flex around frame 23, and lower-leg/hip seams.
4. Watch brief inferred-contact gaps and existing loop speed changes. The source
   cadence is retained; exact ground locking/stride matching is not implemented.
5. To inspect Idle, select Idle and set the timeline to 1-251. Its animation and
   absolute source poses were not modified.

If the added leg flex looks unnatural, retain this derivative as a trial and choose
an explicitly reviewed alternative (for example limited heel-roll adjustment or a
different licensed native clip). Do not export/replace the first GLB automatically.
A future four-influence export must revalidate clearance and deformation; this
blend still has the original skin. Real runtime blending/stride matching and rights
verification remain outside this asset-only task. No later milestone was started.

## Evidence, scripts and verification

- `diagnosis.json`, `diagnosis-samples.npz`: full boot/native/hips/rotation scan.
- `correction-trial.json`, `correction-contact-trial.json`,
  `correction-final-trial.json`: measured alternatives and foot-rotation
  counterfactuals. Their corresponding curve NPZ files are retained.
- `baked-leg-loop-keys.npz`, `correction-loop-curves.npz`, `loop-refinement.json`:
  exact selected leg keys and tiny seam adjustment.
- **`final-correction-validation.json`**: authoritative source/final pose comparison;
  `contact-samples-final.json` contains dense before/after clearance and foot paths.
- `correction-validation.json`: pre-seam-refinement audit, retained for traceability.
  Its old direct-influence-only vertex metric includes Toe-only vertices moved by
  Foot parents; the final audit correctly excludes the whole affected leg hierarchy.
- `ground-comparison.png` and eight individual PNGs: matched before/after evidence.
  The final seam refinement does not change these captured frames.
- `visual-review.json`: still-review findings and limitations.
- `saved-correction.json`: new blend hash, action/skin fingerprints and provenance.
- **`saved-file-validation.json`**: fresh Blender reopen, exact action serialization,
  identical Idle/skin/textures, two actions, one mesh/rig and 993 clearance checks.

Automation uses installed Blender/numpy and existing Gateway Sharp only. The initial
diagnostic corrected a read-only numpy Vector view; an empty region-edge statistic
was handled explicitly and region coverage expanded before recording validation.
Those inspection-script errors changed no assets. No external services or uploads.

Workflow: `diagnose_ground.py` -> `explore_correction.py` variants ->
`review_and_validate.py` -> inspect comparison -> `refine_loop.py` ->
`review_and_validate.py -- --loop-refined --no-renders` -> `save_corrected.py` ->
`verify_saved.py`. `ground_utils.py` and `bake_utils.py` provide shared helpers;
`make_review.cjs` composes the contact sheet. Scripts refuse existing final output
and key reports. Do not remove safeguards to overwrite prior source/derivative files.

Saved-file and protected-input hashes were checked after processing and reopen.
No production build, browser matrix or Universe regression was needed. Gateway
`git diff --check` and automation syntax/whitespace checks are recorded separately
at final verification; pre-existing untracked M7.1 files are outside this change.
