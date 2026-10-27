# M7.3c.4 environmental clearance diagnostics

Local-only scripts and evidence; no asset exports or runtime instrumentation added.

## Measurements

Run from `D:/Code/porto-projects` with existing Gateway dependencies:

```powershell
node gateway-assets/automation/m7.3c.4/measure-clearance.cjs baseline
node gateway-assets/automation/m7.3c.4/measure-clearance.cjs corrected
```

`baseline-recipes.ts` and `baseline-navigation.ts` preserve the pre-change recipes/navigation. The script uses the existing player, exact GLB, calibrated AnimationMixer/ground correction and installed Sharp. Each location samples 180 poses at 120 Hz, including the entry fade and multiple 1.75x Walk cycles. 1,930 boot vertices are evaluated per pose. Depth is nearest box-face depth for vertices inside exact solids, not vertical distance from the road top. Counts are vertex-frame intersections, not unique vertices. `measurement-summary.json` and `walkability-comparison.json` summarize the full reports.

Historical attribution: the M7.3c.1 snapshot with 235 intersecting vertices and 18.509 mm depth intersects Tools' road. Its prior prose labelled the bench. The old 24.097 mm road point also belongs to Tools. Independently reproduced bench and Latest road findings justify the current corrections. The old bench pose still intersects if teleported there, but movement now rejects that position; the legitimate wall-stop comparison has no bench intersection.

The .02-unit navigation grid has zero newly allowed samples in either world. Tools: 5,733 to 5,462 allowed; Latest: 6,665 to 6,566. Latest's 6 mm low-roof clearance prevents newly allowed helmet-risk fringe positions after reducing support height. The measured maximum posed avatar height, including sampled stop fades, is .305727, versus the unchanged .30 player height. This is a focused roof guard, not global avatar collision certification.

## Visual evidence and native input

`clearance-comparison.html` is a local Three.js scene using exact GLB/PBR textures and original box geometry. `environment-before-after.png` pairs Tools bench stop and Latest road edge at identical Walk phases. It is controlled comparison evidence, not a replacement for native camera checks.

`browser-qa.cjs` ran the 1440x900 Tools/Latest native-input flows with SwiftShader. Its `tools-bench-stop.png` is MISLABELLED: that first D traversal reached the world boundary, not the bench. Do not use it to claim bench stopping. `bench-stop.cjs` is the specific west-face bench follow-up and affected Tools project/Return flow. Pointer-lock mouse angles are quantized; its held-key Idle check permits <.001 residual face-slide speed and <1 mm Z drift.

The initial broad test filter accidentally selected three FPS browser tests before the restarted Next server was ready. `focused-pre-server-start.json` records navigation-only failures, not product failures. These unrelated flows were not expanded into a browser matrix. Unit collision/camera checks were selected explicitly afterwards. Earlier fixture failures came from process opt-in omission, intended spawn/view changes and machine-precision settling; the final affected checks use the final geometry/margins.

Use direct Next/TypeScript/ESLint/Playwright CLIs to avoid ecosystem sync prehooks. Walking is enabled only for the QA process; production/default remains false. Existing cadence and ground algorithms, source/final GLBs and Blender files are unchanged. No M7.3d, commit, push or deployment. Real hardware/browser perception and licensing clearance remain manual.

## Final checks

20 distinct focused tests passed across runs; 14 affected unit checks passed after the final roof margin. Typecheck, lint, one production build (walking=false) and git diff --check passed. Final native bench/project follow-up passed; the development server was stopped. See verification-summary.json and the milestone record for limits.
