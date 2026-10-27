# M7.4a.5 — rejected transition prototypes

No production camera correction was accepted. The user's critical-failure rule
requires preserving existing collision safety if a continuous safe path cannot
be established. Only milestone documentation changed in Gateway; earlier HUD
CSS/tests remain untouched and uncommitted.

## Files and commands

- `prototype.cjs`: copies/transpiles current ThirdPersonCamera externally, adding
  early low-ceiling underside preparation. Uses installed TypeScript and Three.js.
- `prototype-third-person.ts`: generated candidate, **not production code**.
- `prototype-results.json`: old/new class replay metrics, rejected candidate.
- `path-check.cjs`: late-repair plane bound and bounded candidate-path checks.
- `path-results.json`: proof inputs, sampled ball and path results.

Run with Node from `app-gateway-fe` using their absolute paths. No installation,
GLB modification, runtime instrumentation, browser or build is required.

## Safety invariants

Existing .035-radius camera boom must be clear, eye must remain above supported
ground, eye sphere sweep must be clear, normal camera steps must remain within
2 units/s (delta clamped to .1), no zero boom when a feasible path is available,
and framing stays within 65–75 degrees. Preserve weighted body visibility,
candidate stability/hold, focus pause/freeze, Return restoration and reduced
motion. A candidate that clears geometry but hides the character is rejected.

## Confirmed local impossibility

Use the exact matched zero-boom frame from the M7.4a.4 targeted report. Previous
camera (.163411,.987878,1.402834), newly lowered pivot
(.078453,.563000,.808758), allowed step .0336. Expand the authored beam by the
existing .035 camera radius. Its lower plane is y=.565000, just .002 above pivot.

For every endpoint in the cube containing the allowed movement ball, the ray
hits that plane at x .078678–.079059 and z .811203–.811966, strictly inside the
beam's expanded footprint. Coordinate extrema occur at cube corners because the
plane-intersection ratio is monotone over these positive denominators. Therefore
all endpoints within the permitted step fail the clear-boom condition. An
independent 515-point ball sample also finds zero clear endpoints. Descending
the old camera below the expanded beam needs at least .422878 vertical units.

This proves a late repair cannot preserve collision and the current step bound
at this state. It does not prove that an earlier multi-stage trajectory is
impossible. No unsafe position clamp or teleport was implemented.

## Evaluated paths

Spawn-to-crossbar player positions over .95s; pivot height transitions smoothly.
Test at 30/60/120Hz (200 combined samples per strategy). Direct interpolation
between safe endpoints fails boom collision 108 times. Piecewise early routes
through the existing +/- .25/.50 yaw offsets and the straight rear waypoint fail
boom clearance 74–78 times each. Their eye sweeps and step bounds are valid.
This demonstrates why eye-only clearance and endpoint selection are insufficient.
These are bounded path proposals, not exhaustive search or accepted animations.

## Rejected underside preparation

The prototype anticipates low ceilings across the boom reach plus the existing
.36-unit preparation region. It lowers pivot and camera ceiling without changing
the real source, collision projection, visibility scoring or FOV limits.

On the same recorded spawn-based crossbar player trace, old/new minimum boom is
.001946/.558582 and maximum camera step .631068/.012131. The frame-wise sphere
and boom checks are clear, but fixed-envelope framing still has 60/359 failures
(maximum overshoot ~19.4px). More seriously, ordinary Latest movement gains
49/220 envelope failures, ~1770.6px overshoot and .22774 minimum boom. Therefore
the change fails presentation safety and is rejected even though it removes
the primary near-zero collapse. Tools replays remain unchanged.

Replay models are warmed at spawn before feeding saved player frames; classes
use the same inputs/deltas. The primary spawn-based routes are comparable offline
old/new evaluations. Continuation fragments begin elsewhere without reproducing
the original browser history; do not describe them as equivalent native captures.
Fixed-envelope failures are conservative geometric indicators, not newly rendered
animated-mesh pixel measurements. No native after result or runtime cost exists.

## Stop and next decision

No tested minimal strategy provides collision clearance, continuous motion and
framing together. A staged lateral/front-side trajectory or a more selective
early preparation policy needs its own path proof and nearby-facade/turning
checks before implementation. Keep the existing camera and walking default-off.
M7.4a remains blocked by dynamic framing; no defect-resolved claim, commit,
deployment or subsequent milestone.
