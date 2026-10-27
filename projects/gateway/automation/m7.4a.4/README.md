# M7.4a.4 — Dynamic TPS Framing Audit

Diagnostic only. Gateway production files were not changed. All scripts, reports
and screenshots here are external to the Gateway repository. No dependencies,
asset edits, commits, publication or deployment.

## Reproduce

Use installed headed Chrome at 1440x900 with a temporary walking-opt-in development
server at 127.0.0.1:3001. Enter Latest Builds, native-click TPS, obtain pointer
lock, normalize initial automation cursor warp through native mouse look to
existing spawn yaw .1355277193 and pitch -.52. Hold S ~950ms, stop ~1.5s, then
hold W through the crossbar. A/D reversals and W/S start/stop near the beam also
reproduce cropping. See `audit.cjs` for exact bounded routes and key timings.

The active Canvas confirms Chrome 155.0.8059.40 and GTX 1660 SUPER through
ANGLE/D3D11. SwiftShader is inactive. These are geometric diagnostics, not new
FPS/performance acceptance measurements.

## Authoritative evidence

- `report.json`: six bounded native routes, actual rendered-camera projection.
- `targeted-report.json`: crossbar turns/reversals and held-key blocked movement;
  includes explicit key records and matched internal-trace captures.
- `analysis.json`: eight-route summary, event brackets, animation pose groups,
  offline existing-camera alternatives at frozen animated poses.
- `analysis-console.txt`: readable summary from `analyze.cjs`.
- `*-worst.png`: same-render Canvas snapshots for route projection maxima.
- `*-matched-worst.png`: same-render snapshots whose copied internal camera trace
  matches the actual rendered position; available for targeted routes.
- `latest-crossbar-after-stop.png`: page screenshot including DOM HUD and recovered
  astronaut framing. Canvas-only captures deliberately omit DOM controls.

`initial-report.json` / `initial-audit.cjs` retain the first diagnostic attempt.
It let its source-copy camera drift from the real smoothed pose and included
near-plane projection extremes without depth filtering. Do not use its internal
trace or maximum pixels as the final result. `dense-audit.cjs` preserves the
subsequent six-route script version; `audit.cjs --targeted` runs only the two
additional crossbar scenarios. `analyze.cjs` reads both authoritative reports.

## Method and precision

The page wraps the existing camera callback for an external source-copy trace
and wraps render completion for sampling. The camera copy is synchronized to
the previous real camera pose. It never writes the real camera/player/animation.
Code is transpiled with Gateway's installed TypeScript; source-copy trace fields
are added in memory only. Installed Three.js is used for offline alternatives.

The fixed envelope is projected every rendered frame; full animated mesh scanning
is every fourth render (~67ms). Actual projections use the real Three.js mesh,
skeleton and camera. Every sampled vertex is classified by camera depth; behind
and near-clipped geometry is separate from screen-coordinate overshoot. 714 mesh
samples are captured; 43 fail framing. Sample fractions are scenario-specific,
not visitor statistics. Event spans are first-to-last failed samples; surrounding
good samples provide conservative duration brackets. Onset/offset can be missed
between samples. Zero overshoot with all geometry behind the camera is a failure.

2813/2845 source-copy position comparisons agree within 1e-8 world units. React
callback replacement temporarily loses the wrapper on 32 frames; reject those
internal traces for causal claims. Actual camera/mesh projections remain valid.
Offline candidate evaluation reconstructs the pivot from the captured player and
navigation. It uses the actual saved projection for the current camera, since
look-at reconstruction at a zero-length boom has an undefined orientation.

Full scan frames average ~10.7–13.1ms including diagnostics; allocation and PNG
readback can affect pacing. Do not claim these are uninstrumented performance or
exact worst-case frame/duration measurements. No production mesh scan was added.

## Findings

- Maximum recorded below-viewport overshoot is 24,631.83px in a near-lens pose.
  This is projected vertex extent, not visible pixel area; the character can
  disappear entirely. At the same pose an immediate 75-degree lens still records
  24,299.68px overshoot. A fully in-front frame also fails at 75 degrees by
  1,511.58px, independently of near-plane numerical extremes.
- Failure sequences span up to 532ms of failed samples, bracketed within 649ms.
  All route tails recover. Tools entry/bench and ordinary Latest movement have
  no sampled failures. Crossbar geometry is the confirmed trigger, but the
  transition algorithm is shared: other narrow passages remain untested.
- The copied trace exactly matching a real frame shows a .73530-unit camera jump
  against a nominal .03360-unit smoothing step, ending at its pivot/target with
  zero boom. The collision-projected interpolation and its inward fallback
  collapse before settling toward the clear underside endpoint.
- The envelope flags every recorded framing failure. Walk/turn horizontal bounds
  exceed its +/- .075 by up to ~.022 side / .016 depth; measured height < .306
  fits below .32. All four walk-cycle quarters, 375 Idle samples and 146 crossfade
  samples are represented. Eleven mesh projections exceed envelope bounds, but
  no recorded failure escapes envelope detection.
- Source frame order advances player before camera, then character/animation.
  Matched rendered poses confirm failure without a stale player. Faster FOV or
  reordered animation alone cannot solve the near/zero boom; full Walk, crossfade
  and Idle samples all participate.
- Frozen-pose existing side view 3 gives .5902 boom, clear collision, 9/9 existing
  weighted visibility, full framing at 75 degrees and ~74.13 degrees for the .92
  NDC margin. This establishes safe endpoints, not a continuously safe path.

## Proposed correction and risks

Recommend a framing-aware version of the existing passage transition: anticipate
the ceiling/pivot change before hard collision projection, using the existing
fixed envelope to avoid a transition through the body while following a clear
existing endpoint. Preserve the sole camera writer, exact collision safety,
visibility scoring, cached bounds, smoothing and 65–75-degree limits. Do not
accept a lens/envelope-only fix, remove collision checks, jump to an endpoint,
or add runtime skinned-mesh scans.

Implementation is justified for review; exact bounded-path feasibility remains
unproved and needs a prototype. Main risks are camera safety under roofs,
near-body occlusion, target/interaction ray changes, hysteresis/oscillation,
unbounded jumps, reduced motion and frame-rate sensitivity. Future focused
regressions should sample both crossing directions, reversals and blocked
Idle frame-by-frame, compare Tools, and check collision, framing and travel
bounds together. Nothing was implemented in this audit.
