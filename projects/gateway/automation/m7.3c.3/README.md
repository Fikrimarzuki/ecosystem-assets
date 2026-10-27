# M7.3c.3 — local stride diagnostics

Run from `D:/Code/porto-projects`. These scripts use installed Gateway dependencies,
read the existing GLB and leave source assets unchanged. No external uploads.

- `measure-stride.cjs` → `stride-analysis.json`, `foot-phases.json`: 480 Hz exact
  same-vertex near-floor motion, backward-foot-bone stance classification, 1–10 mm
  threshold sensitivity, fixed-rate comparisons, longest continuous stance drift.
  Contact proxies are not force measurements. All-floor RMS worsens at 1.75×;
  stance mean/RMS and all-floor mean improve. Do not hide this distinction.
- `baseline-animation.ts`: pre-change source snapshot for comparison only.
- `validate-contact.mjs` → `ground-compatibility.json`: reuse the old 8,000-case
  schedule at the new cadence plus 4,800 variable-speed samples. Old and new poses
  intentionally differ at the same wall time. Check clearance/cap/full-mesh region
  coverage, not old-pose equality. No algorithm/asset edit. 12,800 samples, zero
  penetration, maximum player-local lift 10.308 mm, cap 12.691 mm.
- `qa.config.ts`: direct focused tests with no ecosystem prehook/server startup.
  `focused-tests.json`: all 11 asset/animation/ground/stride unit tests passed.
- `comparison.html`: isolated clear-ground exact-GLB comparison, 1× vs runtime
  calibrated playback, same .42 player travel, .1586387156 scale and PI facing.
  No camera occluders, no runtime feature. It deliberately translates the model
  and camera over a stationary grid to expose contact motion.
- `browser-qa.cjs` serves that fixture locally on 3333, reuses one browser for the
  comparison and native Tools flow on the opt-in dev server at 3000. Native keys
  exercise both axes, direction changes, blocked Idle, pause, repeat entry/exit,
  Return focus, FPS exclusion and reduced Idle. S/D/W samples retain a moving
  transition count; the earlier A reversal includes a legitimate collision stop.
  `native-sideways-walk.png` has foreground occlusion: not foot-slide evidence.
  `cadence-comparison.png` and recorded WebM are clear-view supporting evidence.
  SwiftShader recording is not real-hardware motion/performance acceptance.

Initial browser navigation timed out during first Next compilation. The isolated
comparison's grid contrast was improved and only the browser check retried, with
a longer DOM navigation timeout. The completed attempt passed with no page errors;
`browser-report.json` / `browser-progress.json` retain exact state metadata. No
successful unit/static check was repeated. Direct typecheck/lint and one production
build (walking=false) passed; source hashes and `git diff --check` were verified.

Gateway production edits are only the existing animation controller; regression
tests and milestone docs accompany it. No GLB/BLEND, movement, ground algorithm,
camera, canonical configuration or default flag changes. Server stopped. Nothing
committed, pushed or deployed. Licensing/attribution remains pre-publication work.
