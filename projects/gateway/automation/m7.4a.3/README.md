# M7.4a.3 external diagnostics

These scripts, reports and screenshots are outside the Gateway repository.
They use the installed headed Chrome and a temporary walking-opt-in dev server.
No production instrumentation or source environment settings were changed.

## Authoritative comparisons

- Desktop before: `../m7.4a/final-acceptance/acceptance-report.json` and
  `../m7.4a/final-acceptance/latest-corrected-settled.png` (257 boot vertices
  inside the bottom-center instruction panel).
- Tablet before: `before-tablet-report.json` and
  `before-latest-settled-768.png` (642 boot vertices inside).
- After: `layout-measurements.json`, `test-report.json` and the four
  `hud-latest-*` / `hud-tools-*` screenshots under `test-results/`.
  All sampled TPS meshes have zero HUD-overlapping vertices.

The initial `before-report.json`/desktop capture is not an equivalent comparison:
automation's initial pointer-lock cursor warp changed the player's orientation.
The tablet-only baseline retry settled the intended route. Use the existing
verified desktop final-acceptance baseline instead of the initial new capture.

## Test results

Four distinct focused tests passed: the two pre-existing native pointer/keyboard
control tests in `test-report-initial.json`, and two HUD route tests in final
`test-report.json`. Intermediate reports retain failures from a wrong expected
overview state and selecting a world before fresh labels rendered. The final
HUD tests wait two rendered frames and normalize automation's initial pointer
warp through native mouse look using the existing spawn orientation, without
assigning any player/camera state.

Mesh projection scans actual animated vertices in test code only. Foot counts
use combined Foot/ToeBase weight > .5. They measure overlap, not visible surface
area. AABB checks also separate instructions from character and essential HUD
controls. Samples cover Latest entry/settled/movement, Tools entry/bench, and
reduced-motion FPS, with native Escape/Return and restored inspection focus.

## Separate camera observation

The forward-moving Latest sample records character bottoms beyond the viewport
(about 1754px desktop / 1160px tablet), although the HUD remains separate. This
single moving-frame result does not establish persistence; retain it for targeted
M7.4a camera/framing review. No camera change or full visual acceptance is claimed.
No performance measurements were repeated in this layout milestone.
