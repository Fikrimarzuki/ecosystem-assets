// Read-only headless load test: Babylon NullEngine + glTF loader from the game repo's node_modules.
import { readFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
const nm = 'file:///D:/Code/porto-projects/code-fps/node_modules/'
const t0 = Date.now()
console.error('importing core')
const core = await import(nm + '@babylonjs/core/index.js')
console.error('core imported', (Date.now() - t0) / 1000, 's')
await import(nm + '@babylonjs/loaders/glTF/index.js')
const { NullEngine, Scene, LoadAssetContainerAsync, FreeCamera, Vector3 } = core
const glb = readFileSync(process.argv[2])
const engine = new NullEngine()
const scene = new Scene(engine)
console.error('loading', glb.length, 'bytes')
const c = await LoadAssetContainerAsync(new Uint8Array(glb), scene, { pluginExtension: '.glb', pluginOptions: { gltf: { skipMaterials: true } } })
const skel = c.skeletons[0]
const out = {
  meshes: c.meshes.map((m) => ({ name: m.name, verts: m.getTotalVertices?.() ?? 0, skinned: !!m.skeleton })),
  skeletons: c.skeletons.length, bones: skel?.bones.length,
  animationGroups: c.animationGroups.map((g) => ({ name: g.name, from: g.from, to: g.to, targeted: g.targetedAnimations.length,
    seconds: +( (g.to - g.from) / (g.targetedAnimations[0]?.animation.framePerSecond || 60)).toFixed(4) })),
  materials: c.materials.map((m) => m.name), textures: c.textures.length,
}
console.log('BJS_LOAD ' + JSON.stringify(out))
c.addAllToScene()
new FreeCamera('cam', new Vector3(0, 1, -4), scene)
const bone = (n) => skel.bones.find((b) => b.name === n)
const probe = ['thigh.L', 'forearm.R', 'hips']
const motion = {}
for (const g of c.animationGroups) {
  g.start(true)
  const samples = []
  for (const t of [0, 0.25, 0.5, 0.75]) {
    g.goToFrame(g.from + (g.to - g.from) * t)
    scene.render()
    samples.push(probe.map((n) => bone(n).getTransformNode()?.rotationQuaternion?.asArray().map((x) => +x.toFixed(4)) ?? bone(n).getRotationQuaternion().asArray().map((x) => +x.toFixed(4))))
  }
  g.stop()
  const changed = probe.map((_, i) => samples.some((s) => JSON.stringify(s[i]) !== JSON.stringify(samples[0][i])))
  motion[g.name] = Object.fromEntries(probe.map((n, i) => [n, changed[i]]))
}
console.log('BJS_MOTION ' + JSON.stringify(motion))
engine.dispose()
