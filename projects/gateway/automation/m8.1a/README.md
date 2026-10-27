# M8.1a — read-only clearance feasibility

Gateway HEAD e4e6f34, restored M8.1 recipes. All hypothetical changes exist only in
these external scripts/data. No production geometry, orbit, routes or cameras changed.

- `survey.cjs` / `clearance.json`: 600 one-second phases, conservative whole-world
  bounds (yaw extrema, selected1.025, .025 margin), station, all15 pairs, overview
  projection at1150x740/688x570/592x570 Canvas sizes. Tools7 envelopes; orbit factors;
  provisional all-world full and compact targets. Ground-only .01 raster connected
  areas with original navigation obstacles. Deck triangle-fan center is excluded
  from boundary, matching production. Fine Tools4x3.4=7.22295;3.6x3.04=5.35090.
- `geometry.cjs`: actual closed rendered part triangles, triangle SAT plus ray
  parity containment, including torus holes. `geometry-minima.cjs`: full600-phase
  nearest surface distances for all world/station and world/world pairs. Data in
  `geometry-*.json`. Sanity checks passed for disjoint/overlapping boxes, known unit
  surface gap, torus-hole exclusion. Known Learning350s/41 cone failure has no
  triangle contact and1.95720 surface gap. Sampled contact ≠ continuous proof.
- `routes.cjs` / route JSONs: all6 destinations,5s phases,513 equal-arc-distance
  samples. Conservative rocket primitive OBB vs world/station primitive boxes,
  with actual triangle contact checks where boxes overlap. Entire flight incl
  launch/arrival/parking checked, station too. Records are sample/part hits, not
  unique collisions. Signed SAT gap is a conservative separating-axis gap, NOT
  geometric penetration depth or exact nearest distance. Whole rocket radius1.12
  is broad phase only; the engine flame is excluded. Expanded parking keeps west
  edge offset: X=-1.8-(width-2.72)/2. Optional +globalZ lift shift retains initial
  pad tangent, curve joins and end tangent; no camera/flight acceptance implied.
- `global-balanced-refined-routes.json`, `tools-3.6-refined-routes.json`: full cycle
  refined to1s, each1,846,800 path poses. No sampled conservative contact.
- `clearance-extra.json`: balanced world-specific capacity plan and hypothetical
  1.10 overview view-span multiplier, plus full targets at1.35 orbit radii.
  Zoom is mathematical projection only, not a changed camera or UI.
- `global-balanced-fit1.13.json`: fitting with13% view-span allowance; narrow
  horizontal bounds margin~8.9px rather than~1px with10% fit.
- `tools-4-pilot.json`: next-step Tools-only4x3.4 with1.10 XY orbit/view spans,
  original remaining worlds. Full600-phase bounds,5s all-destination routes.
- `inspection.cjs` / `inspection-parking.json`: reduced-motion holding attitude,
  600one-second phases; phase-zero inspection projections at12 yaw/pitch pairs,
  existing65%/58% Canvas split. Compares unchanged `scale*2` with half-diagonal
  extent; includes mesh and parked rocket. Parking contact checks are global, but
  the positive distance minimum is only among near aggregate bounds (gap<=.2),
  not a certified global/continuous minimum. No HUD/browser/readability acceptance.

Methods preserve period600s, phase relationships, depth trajectories, local units,
player/astronaut/buildings/roads and selection state. They do NOT prove continuous
clearance across every combination of ambient bob/yaw, future structures, manually
rotated worlds, labels/fonts or native browser pointer behavior. Future acceptance
must refine critical intervals and include allowed transform extrema.

Recommended: world-specific compact capacities +10% XY orbit spacing and bounded
overview fitting, no new launch-path bend. First implement only Tools4x3.4 after
review; permit at most13% overview span for useful edge margin. Full5.2/6.4 targets
need about35% orbit and47% narrow-tablet view increase,
so they are physically plausible but not an accepted readability trade-off.
