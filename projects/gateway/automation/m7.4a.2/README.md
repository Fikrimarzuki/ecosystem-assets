# M7.4a.2 — focused character-framing evidence

All temporary diagnostics are outside Gateway. No assets were modified. Walking
was enabled only for the isolated dev-server process; its source default is false.

- `baseline-third-person.ts`: unchanged source-camera snapshot before this fix.
- `before-latest-crossbar-reference.png`: original M7.4a settled defect screenshot,
  copied without alteration from the preceding diagnostic. Two fresh `before.cjs`
  attempts failed during server startup/cold compilation; `before-report.json`
  retains that diagnostic failure, not a successful new baseline browser run.
- `prepare-browser.cjs` / `after.cjs` / `after-report.json`: actual native Chrome
  entry, movement, grouped real-mesh projection, camera-cost probe, project focus
  and Return. The first attempt lost pointer lock while another headed browser
  owned focus; the successful report is the isolated rerun after it closed.
- `prepare-clearance.cjs` / `clearance.cjs` / `clearance-report.json`: original
  Tools bench-side route and blocked contact, plus Latest crossbar traversal.
- `compare-poses.cjs` / `pose-comparison-report.json`: eleven captured route poses,
  120 updates each, compare unchanged source camera against the corrected camera.
  Position and aim differences are exactly zero; collision booms remain clear.
- `focused.config.cjs`: only focused tests using installed headed Chrome. Test
  outputs remain here rather than in the Gateway repository.

Chrome 155.0.8059.40 at 1440×900 used NVIDIA GTX 1660 SUPER / ANGLE D3D11 on the
actual TPS Canvas. No SwiftShader. Warm native S input for 950 ms, then release and
settle 1.5 s, reproduces the affected Latest region. Each after capture also projects
the same real posed mesh through a **cloned 65° lens** for a position/pose-matched
counterfactual. No runtime camera mutation is used for that comparison.

At `after-latest-crossbar-settled.png`, boots move from −1.09857 to −.91208 NDC Y:
944.36 px to 860.44 px, or 44.36 px outside to 39.56 px inside the viewport.
The final lens is approximately 75°, its existing maximum. Helmet, torso, lower
body and complete mesh fit; after directional changes the minimum is −.94926.
Actual entry views keep 65°, and beyond-crossbar framing recovers to 65°.
Screenshot reference and native after visits have small input-timing position
differences; use the cloned-lens projections or unit reproduction for exact matching.

The approximately 10-second Latest native movement probe has 515 timed camera
callbacks: mean .241 ms, p95 .500 ms, max 3.700 ms; 99.17% of recorded renders have
actual movement. Callback refs can be replaced, so timings do not cover every
render. Totals include all camera work and diagnostic overhead. An unrelated
focused CPU-only test ran briefly during this diagnostic; this is not a controlled
microbenchmark or proof of improvement over the previous .247/.500 ms totals.
No prior 30-second overview/TPS acceptance samples were repeated.

Production uses ten constant body-envelope probes and arithmetic, not these full
mesh scans. Positions/aim/visibility choices, collision, player/animation/world
behavior and the central interaction ray remain unchanged. The existing 65–75°
limit and easing remain; impossible coverage retains the collision-safe fallback.
The viewport margin does not reserve the bottom instruction HUD. Subjective lens
comfort, other routes/devices, low-FPS visual acceptance and asset-rights approval
remain pending. See the milestone document for authoritative verification status.
