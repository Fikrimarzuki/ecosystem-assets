# M7.3d — Final Walking Exploration Validation

2026-10-13. Gateway checkpoint at start: `7a4c1d046d7873e75ac7ab4087f786f458347db7`.
Only the milestone document changes inside Gateway. Local diagnostics remain here.

## Outcome

Bounded Tools/Latest integration, default-off browsing, FPS separation, reduced
motion, repeated TPS reuse, Return focus/camera and mobile fallback are verified.
No production fix was justified. Public walking remains unapproved: real-GPU
performance, perceptual/assistive-technology/browser acceptance and asset-specific
licensing evidence are still required. No commit, push, deployment or next milestone.

`verification-summary.json` maps claims to evidence. Read the milestone record for
the measured CPU/pacing table and limitations; raw partial reports are not all passing.

## Evidence segments

- `focused-tests.json`: 20 unit checks passed together, 15.3 seconds. No full suite.
- `disabled-browser-report.json`: standard warmed Next CLI, no walking/model request,
  independent portfolio details heading focus, baseline scene pacing. Final control
  assertions resumed without repeating the successful measurements after correcting
  the initial portfolio accessible-name selector.
- `enabled-browser-report.json`: Tools movement, bench held-key Idle, pause/Resume,
  CareerLens details assertions completed before an incorrect camera assertion
  compared different Tools visits. Keep the failure in this partial report.
- `enabled-final-browser-report.json`: complete controller/camera/animation CPU
  sample and three reuse cycles. 32 geometries, 5 textures, 5 programs stay stable;
  mixers detach on exit. Its later FPS assertion incorrectly used TPS-only speed.
- `enabled-fallback-browser-report.json`: remaining FPS/reduced/Latest/Return/
  offscreen/mobile checks completed. FPS movement uses player displacement and
  waits for the camera/player lock initialization. False check fields denote
  flows skipped in that resumed segment, not newly failing product behavior.
- `transitions-browser-report.json`: 17-frame native start/stop profile, 5 blended
  frames. Boot scans mean/max 1.920/3.000 ms; animation update .824/3.900 ms. Mixer
  and ground costs are nested in animation totals, not additive. Sampled maximum
  visual lift is 1.925 mm, not an exhaustive maximum.
- `motion-profile-browser-report.json`: no screenshots during held keys; per-render
  speed/position validates 17/23 Tools and 22/29 Latest moving frames. Latest crosses
  between .1805 road support and .18 deck. Two earlier "moving" windows in partial
  reports had already reached the boundary during captures; use those as blocked
  Idle only. Initial replaced callback refs also undercounted some CPU callbacks;
  later complete samples refresh the timing wrappers.
- Requested native screenshots include entry, bench-side/stop, road traversal,
  Latest entry/crossbar, clear-view walking and transition. Image and snapshot times
  are not synchronized; screenshots alone do not certify gait or foot sliding.
- `default-gpu-capability.json`: unforced headless launch also reports SwiftShader.

## Reproduction

Use installed Gateway dependencies, direct CLIs (no ecosystem sync prehooks).
Start the standard dev server sequentially with flag false at port 3001, then
true at port 3000; do not change .env files. Wait for a successful `/` response
before browser assertions, and exclude initial compilation/loading from timings.

```powershell
# From app-gateway-fe; choose the flag/port for each sequential server.
$env:NEXT_PUBLIC_GATEWAY_WALKING_EXPLORATION='false'
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3001
# From the workspace, against the ready matching server:
node gateway-assets/automation/m7.3d/browser-qa.cjs disabled
# Enabled server: true, port 3000. Full harness or only a requested segment:
node gateway-assets/automation/m7.3d/browser-qa.cjs enabled
$env:QA_RESUME='motion'
node gateway-assets/automation/m7.3d/browser-qa.cjs motion-profile
```

The alternative custom-server configuration was abandoned after route compilation
timed out; usable measurements all use the standard Next CLI. The initial 5-second
cold model check in the final motion probe timed out; the affected check used a
30-second readiness timeout. All successful unit/static checks were retained.

Timing uses in-page references to existing R3F callbacks/mixer, plus a diagnostic
browser RAF that never schedules scene frames. Camera frame timing includes
visibility/projection/transforms, not isolated probe cost. Development, wrapping,
timer resolution, short windows and software rendering limit inference. Heap data
is noisy and not a leak certification. Physical-GPU/browser/AT acceptance remains
manual. All servers were stopped; production build used walking=false. Source GLB,
animated GLB and corrected BLEND retain their recorded hashes.
