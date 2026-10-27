# M7.3c.2 — TPS visibility correction

Gateway changes are confined to its camera adapter, focused visibility tests and
milestone record. No GLB, movement, collision, animation, ground correction,
targeting, world geometry or canonical data was edited.

## Evidence

- `baseline-third-person.ts`: original camera source, retained for offline comparison.
- `options.cjs` / `options-report.json`: original adapter with isolated in-memory
  distance/pitch/yaw trials. Original source/geometry remains intact. Camera pitch
  and distance alone do not clear the audited bench-side walking case. A bounded
  side angle reveals most boots/body while preserving solid occlusion.
- `compare.cjs` / `comparison-report.json`: exact real-GLB Idle/Walk boot rays against
  current recipe meshes. Entry Tools 506→0 blocked vertices; entry Latest 94→0;
  audited bench-side Walk 1,930→253. Counts are boot/cuff vertex sightlines, not
  pixel percentages. This comparison uses identical poses/geometry before/after.
- `before-tools.png`, `before-latest.png`, `after-tools-*.png`, `after-latest-*.png`:
  native Chromium SwiftShader desktop 1440×900. Tools entry, backward near bench,
  direction change and wall stop; Latest entry and movement past crossbar. Sparse
  captures are not real-hardware smoothness acceptance or frame-atomic pose data.
- `after-browser-report.json`: final targeted Latest continuation and metadata.
  The original Tools invocation passed E/details/frozen camera and mixer,
  Escape/Resume, stable collision stop (speed=0, Idle weight=1), paused camera,
  Return focus and saved camera, FPS exclusion and reduced-motion Idle assertions.
  It then stopped on an incorrect diagnostic expectation of `overview` instead of
  the valid reduced-motion `overview-paused`. Only Latest was subsequently rerun;
  this was not a production failure. Tools captures remain from that first flow.
- `focused-tests.json` retains the **last affected smoothing-test rerun**. The initial
  focused selection passed eight unique tests: three real-asset visibility/stability
  tests plus existing safe entry, FPS pitch isolation, camera smoothing/close-space,
  Tools supported-ground camera clearance and targeting/occlusion tests. After
  retaining equally good adjusted views at edges, only stability and existing frame-independent smoothing were rerun and passed.
- Static typecheck, full lint and one production build (walking=false) passed.
  Generated ecosystem payload was reused; npm's sync prehooks were not invoked.

## Reproduction

From `app-gateway-fe`, start the direct Next CLI with process-only walking opt-in:

```powershell
$env:NEXT_PUBLIC_GATEWAY_WALKING_EXPLORATION='true'
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1
```

Then from the workspace root:

```powershell
node gateway-assets/automation/m7.3c.2/after-browser.cjs
node gateway-assets/automation/m7.3c.2/compare.cjs
```

Set `GATEWAY_QA_WORLD=latest` for only the targeted Latest continuation. The browser
script now checkpoints snapshots and accepts both overview states. From the app:

```powershell
$env:NEXT_PUBLIC_GATEWAY_WALKING_EXPLORATION='true'
node node_modules/@playwright/test/cli.js test --config ../gateway-assets/automation/m7.3c.2/qa.config.ts universe-third-person-visibility.spec.ts universe-third-person.spec.ts --grep 'visibility:|initial boom|camera smooths|Tools camera keeps clearance|TPS range|TPS pitch limits'
```

## Bounds and limits

Seven cached envelope probes, at most nine candidate views; existing navigation
solids, no posed mesh scan or full-scene raycast at runtime. Prefer current clear
view, retain equally good corrections, and require 300 ms of clear preferred view
before releasing through existing smoothing. Candidate side angles are ≤0.5 rad;
downward pitch is clamped to −0.65; candidate distance is 0.68 or 0.55 and collision
projects it. Corrective candidates shorter than 0.48 are rejected. Existing safe
overhead fallback remains possible when no useful non-overhead correction fits.

The local CPU benchmark averages 1,000 warmed stationary updates per case:
baseline ~0.016–0.017 ms, corrected ~0.073–0.248 ms. This is not GPU profiling or
real-device performance acceptance. World geometry/materials and player input
yaw/pitch are unchanged; temporary camera side angles can change crosshair aim,
so existing target/range validation remains authoritative.

Remaining boot/prop and road intersections, foot sliding, low-FPS lift perception,
target-label overlap and public-release licensing checks remain separately scoped.
Both animated GLB copies retain their M7.2 SHA-256. The QA server was stopped;
walking remains default-off. No commit, push or deployment.
