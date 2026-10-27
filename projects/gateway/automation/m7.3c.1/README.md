# M7.3c.1 read-only camera/visibility audit

Production code and asset bytes were not edited. Gateway's only audit edit is the
M7.3c.1 documentation record. These scripts use installed tools and write only their
own reports/captures in this directory. Run from `D:/Code/porto-projects`.

## Reproduction

Use the existing generated ecosystem payload. Do not invoke npm's predev sync hook.
Start the direct Next CLI from `app-gateway-fe` with a process-only walking opt-in:

```powershell
$env:NEXT_PUBLIC_GATEWAY_WALKING_EXPLORATION='true'
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1
```

After HTTP 200, from the workspace root:

```powershell
node gateway-assets/automation/m7.3c.1/browser-audit.cjs
node gateway-assets/automation/m7.3c.1/clear-walk.cjs
node gateway-assets/automation/m7.3c.1/measure-audit.cjs
```

The server was stopped after this audit. No flag file was changed.

## Evidence and limits

- `browser-report.json`: native 1440×900 Tools entry, pitch, backward walking,
  direction changes, E/details/pause/Resume/Return, Canvas identity and page errors.
  `tools-forward-after-resume` is not a settled collision capture: the original
  speed poll caught a transient zero. Do not use it as wall-stop proof.
- `clear-walk-report.json`: separate small Tools flow for clear lateral Walk and
  stable held-key collision stop. It waits for actual motion first, then speed=0
  and Idle weight=1. Later lateral captures reached the flywheel/road boundary;
  their names do not imply they are still walking or unobstructed. Inspect metadata.
- PNGs are native browser captures. Snapshots precede screenshots; they are not
  frame-atomic while keys remain held. SwiftShader cadence is insufficient for a
  real-hardware motion-quality/performance claim. No six-world browser matrix.
- `measure-report.json` replays saved action times/weights, player/facing transforms
  and camera poses against the exact imported GLB and current recipe geometry.
  Rays to 1,930 boot/cuff vertices identify foreground blockers. Counts are samples
  of mesh vertices, not percentage of rendered pixels. Mesh projections separate
  frustum cropping from obstruction. Solid intersection tests are restricted to
  actual unrotated box geometry; nearest-face depths are not swept collision tests.
- Six-world spawn calculations are offline only. They do not certify traversal.
  Distance probes are hypothetical sightlines, not changed camera settings or a
  complete collision-aware tuning trial.
- `walk-samples.json`: 249 Walk poses, 248 intervals (~240 Hz). Near-floor centroid
  windows are proxies, not stance classification. `soleVelocity` separately tracks
  the same sole vertices near the plane across endpoints and adds 0.42 full-speed
  root travel, demonstrating residual forward slide. Directional transitions,
  partial fades and collision-reduced speed are not included in that estimate.
- 24 stop phases per 15/20/30/60 FPS use the unchanged runtime animation controller.
  This is a discrete-step simulation, not GPU frame-time profiling or hardware QA.
- TypeScript is transpiled in memory with the installed compiler. No production build,
  dependency installation, camera/movement setting mutation or GLB rewrite occurs.

Gateway's milestone record contains priorities and the proposed camera-only
M7.3c.2 scope. Stride calibration, terrain clearance policy and real-device motion
acceptance remain separate decisions. The final GLB hashes still match M7.2.
