# M8.1 compatibility stop

The 5.2x4.4 Tools candidate was not accepted. `candidate/` archives the attempted
runtime and test files for review; Gateway versions were restored to starting Git
content. Do not copy this candidate into production as a validated expansion.

`measure.cjs` / `measurements.json`: existing local geometry/navigation functions,
same .01/.005 raster method as M8.0. Tools candidate measured 16.81066 gross / 13.80228
spawn-connected area, 898 triangles, two diorama batches, 24 obstacles, unchanged
spawn/buildings/player units. The script now reads restored Gateway if rerun, so
its archived JSON, not a new invocation, represents the candidate.

`tools-overview-probe.cjs` / JSON: hypothetical enlargement of Tools base only, fixed
authored transforms and 5-second orbit samples. No clipping, ~1.20% maximum projected
box overlap; excludes station, labels and flight. This limited probe missed the
stronger compatibility failures and is not full acceptance evidence.

Existing unit tests reproduced:
- Tools/Gateway conservative bounds intersection at phase 180s.
- Learning rocket OBB / expanded Tools cone bounds at phase 350s, sample 41/512.

Candidate selection had 14 passing / two failing units. Browser desktop timed out;
tablet reached native selection/inspection and captured overview/inspection bounds,
but execution stopped at the compatibility gate. No complete native walking
acceptance or update-cost benchmark. Concurrent failure-diagnosis execution shared
the initial output directory; some first-run artifacts were replaced. Retained
traces/screenshots are partial, not a complete test report.

`restored-test-results/` records the two affected tests passing after source restore.
Static typecheck/lint/default-off build passed on restored Gateway; remote sync
prehooks required network-enabled retries after sandbox EACCES. No runtime code,
assets, pnpm files or deployment behavior remain changed by M8.1.
