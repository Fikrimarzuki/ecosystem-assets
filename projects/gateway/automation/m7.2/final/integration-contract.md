# Expected Three.js integration contract — no integration implemented

**Asset:** `astronaut-animated.glb`, SHA-256
`cbe687ee68998b318a9faebcb1a9c93697f50419e9624ab6c1f6b5c278362544`.
Self-contained GLB 2.0: one SkinnedMesh/primitive, one PBR material, three embedded
1024px PNG images, one 41-joint humanoid skin, exactly two AnimationClips. No
Draco/KTX2/meshopt decoder or external texture paths are required. Local asset location
is not a public URL; no public placement is authorized by this preparation.

## Transforms and ownership

- Preserve the loader-created hierarchy, skin and inverse bind transforms. Asset
  uses **Y-up / +Z-forward / meters**, default standing height **1.891089 m**.
- Soles are already placed at Y=0 in default Idle. The **+9.607552 mm** placement
  offset is baked into the hierarchy. Do not add it again and do not apply the old
  unrigged centered-pivot **+0.951071 m** correction.
- A future player wrapper owns navigation translation, yaw and destination
  transforms. Do not reset internal Armature/bone transforms or zero animated hips.
  Hips contain natural sway but no accumulated horizontal root motion.
- Gateway's current procedural visor faces **−Z**. If retaining that convention,
  apply **one 180° Y facing adjustment** to an asset-only wrapper. Do not apply it
  twice or rotate the player/camera/navigation system as part of this contract.
- For a future 0.30 m player-local standing height, initial uniform asset scale is
  approximately **0.158639** (`0.30 / 1.891089`). Existing world scale and `1.025`
  wrapper factor are separate. Check limb envelope against the existing collider;
  changing collision dimensions is not authorized here.

## Clip contract

| Lookup name | Duration | Motion |
| --- | --- | --- |
| `Idle` | 8.333333015 s | Looped stationary idle with natural sway |
| `Walk` | 1.033333302 s | Corrected in-place walking, no accumulated horizontal drift |

Lookup clips by exact name, not index. Use one AnimationMixer per character instance
and LoopRepeat playback. Drive mixer delta from the existing R3F frame loop; no
additional render loop or navigation state. Dense stored keyframes do not require
240 Hz runtime rendering. Movement speed/playback-rate alignment and any crossfade
duration require a later integration review; no stride-speed claim is encoded here.

Retain current pause/details, default-disabled walking and reduced-motion behavior.
Stop advancing visual playback when the existing flow freezes it. Reduced motion
must remain governed by the existing controller/presentation policy; it does not
authorize altering navigation mechanics or enabling FPS/TPS.

For multiple independently animated copies, use a skeleton-aware clone (existing
Three SkeletonUtils); ordinary scene cloning may share bones. Keep cached geometry,
materials and textures ownership clear and do not dispose shared cached resources
when one character unmounts. Release per-instance mixer bindings on disposal.

## Validated boundary and outstanding checks

Installed Three r186 GLTFLoader and CPU AnimationMixer successfully load the asset,
decode maps, animate clips independently and repeat two cycles. The corrected Walk
has **+0.70267 mm minimum CPU-skinned clearance** at unit scale across 993 samples.
At scale 0.158639 that margin is about **0.1115 mm**; terrain alignment, interpolation
between mixed clips and shadows can expose issues not covered by isolated clips.

Later integration must verify actual GPU upload/lighting, live loop/transition quality,
movement synchronization, bounded loading/fallback/resource lifecycle, reduced motion
and real-device performance. Native Walk velocity seam remains a known source property.
No extra IK, root-motion extraction or ground-lift behavior is prescribed.

Public integration also requires documented asset/animation redistribution and
attribution rights. This document is a handoff specification, not permission to
publish, enable walking or modify Gateway runtime.
