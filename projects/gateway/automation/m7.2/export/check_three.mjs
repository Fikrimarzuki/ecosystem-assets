// Offline CPU parsing/animation check using Gateway's installed Three and Sharp.
// ImageBitmap stand-in decodes PNG bytes; this is not a GPU/browser render test.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const here = path.dirname(fileURLToPath(import.meta.url));
const app = path.resolve(here, '../../../../app-gateway-fe');
const localRequire = createRequire(path.join(app, 'package.json'));
const sharp = localRequire('sharp');
const THREE = await import(pathToFileURL(path.join(app, 'node_modules/three/build/three.module.js')));
const { GLTFLoader } = await import(pathToFileURL(path.join(app, 'node_modules/three/examples/jsm/loaders/GLTFLoader.js')));
globalThis.self = globalThis;
globalThis.ProgressEvent = class ProgressEvent { constructor(type, detail) { this.type = type; Object.assign(this, detail); } };
globalThis.createImageBitmap = async blob => {
  const { data, info } = await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  return { width: info.width, height: info.height, data, close() {} };
};

const audit = JSON.parse(fs.readFileSync(path.join(here, 'export-validation.json')));
const reference = JSON.parse(fs.readFileSync(path.join(here, 'engine-reference.json')));
const bytes = fs.readFileSync(audit.output);
const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
const meshes = [];
gltf.scene.traverse(object => { if (object.isMesh) meshes.push(object); });
assert.equal(meshes.length, 1);
const mesh = meshes[0];
assert(mesh.isSkinnedMesh);
assert.equal(mesh.skeleton.bones.length, 41);
assert.equal(mesh.geometry.index.count / 3, 10357);
assert.deepEqual(gltf.animations.map(a => a.name).sort(), ['Idle', 'Walk']);
assert.equal(mesh.geometry.attributes.skinWeight.itemSize, 4);
assert.equal(mesh.geometry.attributes.skinIndex.itemSize, 4);
for (const slot of ['map', 'normalMap', 'metalnessMap', 'roughnessMap']) {
  assert(mesh.material[slot]);
  assert.equal(mesh.material[slot].image.width, 1024);
  assert.equal(mesh.material[slot].image.height, 1024);
}
gltf.scene.updateMatrixWorld(true);
mesh.skeleton.update();
const defaultBounds = new THREE.Box3().setFromObject(gltf.scene, true);
const result = { threeRevision: THREE.REVISION, scope: 'Offline GLTFLoader + CPU AnimationMixer, Sharp ImageBitmap stand-in, no GPU or Gateway integration',
  meshCount: meshes.length, boneCount: mesh.skeleton.bones.length, triangleCount: mesh.geometry.index.count / 3,
  vertexCount: mesh.geometry.attributes.position.count, defaultBounds: { min: defaultBounds.min.toArray(), max: defaultBounds.max.toArray() }, clips: {} };
assert(Math.abs(defaultBounds.min.y) < 1e-5, 'Default scene must be grounded in Y-up');
for (const name of ['Idle', 'Walk']) {
  const clip = gltf.animations.find(a => a.name === name);
  const expectedDuration = name === 'Idle' ? 250 / 30 : 31 / 30;
  assert(Math.abs(clip.duration - expectedDuration) < 1e-5);
  const mixer = new THREE.AnimationMixer(gltf.scene);
  const action = mixer.clipAction(clip);
  action.setLoop(THREE.LoopOnce, 1);
  action.clampWhenFinished = true;
  action.play();
  const errors = [];
  const roots = [];
  for (const sample of reference.clips[name]) {
    mixer.setTime(sample.time);
    gltf.scene.updateMatrixWorld(true);
    mesh.skeleton.update();
    const expectedByImportedName = Object.fromEntries(Object.entries(sample.boneHeads).map(([name, co]) => [THREE.PropertyBinding.sanitizeNodeName(name), co]));
    for (const bone of mesh.skeleton.bones) {
      const actual = bone.getWorldPosition(new THREE.Vector3());
      const expected = new THREE.Vector3(...expectedByImportedName[bone.name]);
      errors.push(actual.distanceTo(expected));
    }
    roots.push(mesh.skeleton.bones.find(b => b.name === THREE.PropertyBinding.sanitizeNodeName('mixamorig:Hips')).getWorldPosition(new THREE.Vector3()));
  }
  const maximum = Math.max(...errors);
  const drift = new THREE.Vector2(roots.at(-1).x - roots[0].x, roots.at(-1).z - roots[0].z).length();
  assert(maximum < .0001, `${name} joint discrepancy ${maximum}`);
  assert(drift < .0001, `${name} root drift ${drift}`);
  result.clips[name] = { duration: clip.duration, sampledTimes: reference.clips[name].map(f => f.time), boneComparisons: errors.length,
    maxJointPositionError: maximum, meanJointPositionError: errors.reduce((a,b) => a+b,0) / errors.length, horizontalRootEndpointDrift: drift };
  mixer.stopAllAction();
  mixer.uncacheRoot(gltf.scene);
}
result.passed = true;
fs.writeFileSync(path.join(here, 'three-validation.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
