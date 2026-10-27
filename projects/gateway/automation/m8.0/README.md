# M8.0 read-only measurements

Gateway source snapshot: e4e6f34 with the existing M7 HUD CSS/tests/documentation
changes preserved. These scripts read current recipes and generated ecosystem;
they do not modify Gateway or synchronize canonical configuration.

- `measure.cjs`: uses installed TypeScript and Three.js to execute existing recipe,
  navigation, collision, ground support, interaction and camera entry functions.
  `measurements.json` contains local units and raw counts. Safe area rasterized at
  .01 and .005; eight-direction Dijkstra with midpoint collision checks gives
  spawn-connected area and estimated approach/traversal distances. Distances are
  divided by existing .42 speed; not native movement timing. Camera data is fresh
  direct placement at 1440/900, not continuous camera-path acceptance. This is a
  navigation graph estimate, not an exact geometric union or navmesh proof.
- `overview.cjs`: hypothetical enlargement of three island base parts in memory,
  keeping structures and planet transforms unchanged. Proposed dimensions 5.2x4.4
  and Platforms 6.4x5.2. Samples 600-second orbit every 5 seconds at two viewports;
  `overview-probe.json` reports projected AABB overlap/clipping. Fixed rotation;
  excludes bob/yaw, station/labels, future placements and rendered occlusion.

Run each with `node` using the absolute script path. No server, GPU session,
new dependencies, production instrumentation or asset changes. These diagnostics
are planning evidence and cannot establish release, subjective or legal acceptance.
