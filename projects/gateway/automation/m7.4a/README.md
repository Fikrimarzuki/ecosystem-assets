# M7.4a — Real-GPU diagnostic checkpoint

2026-10-13, Gateway commit `7f9f832474812914ccf36a8b94635effa39c7f35`.
No production change or automatic commit. Diagnostics stopped at a confirmed
pointer-entry regression, as required by the milestone.

## Results

- Physical GPU confirmed on Gateway Canvas: Chrome 155.0.8059.40, Windows 11 Pro
  10.0.26200, NVIDIA GeForce GTX 1660 SUPER, driver 32.0.15.9649, ANGLE D3D11.
  WebGL and GPU compositing enabled. No forced GPU flags or SwiftShader.
- `disabled-report.json`: warmed 30.005 s overview, 1,800 renders, 59.99 FPS,
  p95 17.0 ms, maximum 19.6 ms. No walking controls or astronaut request.
- `enabled-report.json`: warmed 30.009 s overview, 1,801 renders, 60.02 FPS,
  p95 16.9 ms, maximum 24.3 ms. Later native TPS click timed out because the
  inspection surface intercepted it. The failure is intentionally retained.
- Both overview windows have 28 geometries, 1 texture, 3 shader programs and no
  skinned mesh/mounted animation. This is baseline stability, not TPS cleanup.
- `entry-hit-test.json` and `entry-hit-{1440,768}.png`: both FPS/TPS centers hit
  the `Inspect Tools` rotation surface at both representative sizes. The row is
  static with z-index auto. Prior layout tests checked spacing/focus, not pointer
  hit ownership. Proposed fix: explicit row positioning/stacking above the surface,
  plus native entry-click regression checks. No fix implemented here.

## Evidence caveats

`gpu-capability.json` includes successful WebGL/CDP device results but failed
optional chrome://gpu / edge://gpu page reads. Browser capability is established
by the recorded Canvas renderer and CDP results, not those internal-page reads.
Fresh installed headed Edge also used NVIDIA/D3D11. Default bundled headless
Chromium 156.0.8078.4 still used Vulkan SwiftShader; its results are not real GPU.

Only overview A/B measurements completed. Tools/Latest walking, Idle TPS, repeated
entry/exit, animation/visibility CPU costs and throttled transitions remain pending.
Do not run the full prepared performance script before reviewing the entry fix.
No force-click, DOM invocation or keyboard substitution was used to bypass the bug.

The benchmark uses a temporary native Chrome profile, 1440×900, DPR 1 and no reduced
motion, with Next dev on port 3001 and diagnostic wrappers adapted from M7.3d.
Cold compile and 5 s warm-up are excluded. FPS counts scene renders, not just RAF.
No screenshots/video are captured inside the timed windows. Measurements describe
this desktop/development workload; no production or low-end-device guarantee.
The source is `performance-template.cjs`; `performance-qa.cjs` embeds the existing
M7.3d in-page probe without changing any Gateway source file. Both local servers
and all temporary browsers launched for this milestone were stopped.
