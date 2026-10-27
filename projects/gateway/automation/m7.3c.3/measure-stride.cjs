// Offline read-only GLB analysis. Run from the workspace root.
const fs = require('node:fs'), path = require('node:path'), Module = require('node:module');
const app = path.resolve('app-gateway-fe'), req = Module.createRequire(path.join(app, 'package.json'));
const THREE = req('three'), sharp = req('sharp'), ts = req('typescript');
const resolve = Module._resolveFilename;
Module._resolveFilename = function(id, parent, ...rest) { return resolve.call(this, id.startsWith('@/') ? path.join(app, id.slice(2)) : id, parent, ...rest); };
require.extensions['.ts'] = (m, file) => m._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true}}).outputText, file);
const { ASTRONAUT_SCALE } = require(path.join(app, 'lib/astronaut-asset.ts'));
globalThis.self = globalThis; globalThis.ProgressEvent = class {};
globalThis.createImageBitmap = async blob => { const {data, info} = await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true}); return {data, width:info.width, height:info.height, close(){}}; };
(async () => {
 const {GLTFLoader} = await import(require('node:url').pathToFileURL(path.join(app, 'node_modules/three/examples/jsm/loaders/GLTFLoader.js')).href);
 const bytes = fs.readFileSync(path.join(app, 'public/models/astronaut/astronaut-animated.glb'));
 const asset = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
 const mesh = asset.scene.getObjectsByProperty('isSkinnedMesh', true)[0], p = mesh.geometry.attributes.position;
 const masks = {}, point = new THREE.Vector3(), mixer = new THREE.AnimationMixer(asset.scene), walk = asset.animations.find(c => c.name === 'Walk');
 for (const side of ['Left','Right']) {
  const index = mesh.skeleton.bones.findIndex(b => b.name.endsWith(side+'Foot'));
  const ankle = new THREE.Vector3().setFromMatrixPosition(new THREE.Matrix4().copy(mesh.skeleton.boneInverses[index]).invert());
  masks[side] = Array.from({length:p.count},(_,i)=>i).filter(i=>p.getY(i)<=ankle.y+.12 && p.getX(i)*(side==='Left'?1:-1)>0);
 }
 mixer.clipAction(walk).play();
 const n = 496, dt = walk.duration/n, frames=[];
 for (let i=0;i<=n;i++) {
  mixer.setTime(i*dt); asset.scene.updateMatrixWorld(true); mesh.skeleton.update();
  const feet={};
  for (const side of ['Left','Right']) feet[side]=masks[side].map(index=>mesh.getVertexPosition(index,point).applyMatrix4(mesh.matrixWorld).toArray());
  const ankles = Object.fromEntries(['Left','Right'].map(side=>[side, mesh.skeleton.bones.find(b=>b.name.endsWith(side+'Foot')).getWorldPosition(new THREE.Vector3()).toArray()]));
  frames.push({time:i*dt, feet, ankles});
 }
  const summaries=[];
 for (const threshold of [.001,.002,.005,.01]) {
  const pairs=[], phases={};
  for (const side of ['Left','Right']) {
   const windows=[]; let window=null;
   for(let f=0;f<n;f++) {
    const a=frames[f].feet[side],b=frames[f+1].feet[side]; let count=0;
    for(let v=0;v<a.length;v++) if(a[v][1]<=threshold && b[v][1]<=threshold) {
     pairs.push({side,time:f*dt,vx:(b[v][0]-a[v][0])/dt*ASTRONAUT_SCALE,vz:(b[v][2]-a[v][2])/dt*ASTRONAUT_SCALE,stance:frames[f+1].ankles[side][2]<frames[f].ankles[side][2]}); count++;
    }
    if(count) { if(!window) {window={start:f*dt,end:(f+1)*dt};windows.push(window);} else window.end=(f+1)*dt; } else window=null;
   }
   phases[side]=windows;
  }
  const mean=a=>a.reduce((s,x)=>s+x,0)/a.length, median=a=>a.sort((x,y)=>x-y)[Math.floor(a.length/2)];
  const impliedSpeed=-mean(pairs.map(p=>p.vz));
  const optimal=.42*-pairs.reduce((s,p)=>s+p.vz,0)/pairs.reduce((s,p)=>s+p.vz*p.vz+p.vx*p.vx,0);
  const rates=[1,1.5,1.65,1.75,1.8,1.9,2,optimal];
  summaries.push({thresholdAssetMeters:threshold,pairs:pairs.length,phases,impliedSpeed,impliedCycleDistance:impliedSpeed*walk.duration,optimalLeastSquaresRate:optimal,
   rates:rates.map(rate=>({rate,playerDistancePerCycle:.42*walk.duration/rate,meanAbsoluteForwardSpeed:mean(pairs.map(p=>Math.abs(.42+p.vz*rate))),medianAbsoluteForwardSpeed:median(pairs.map(p=>Math.abs(.42+p.vz*rate))),rmsHorizontalSpeed:Math.sqrt(mean(pairs.map(p=>(.42+p.vz*rate)**2+(p.vx*rate)**2))),meanForwardSpeed:mean(pairs.map(p=>.42+p.vz*rate))})),
   kinematicStance:{criterion:'Foot bone moving backward in asset-forward Z; additionally same sole vertex below threshold at both endpoints',pairs:pairs.filter(p=>p.stance).length,rates:rates.map(rate=>{const ps=pairs.filter(p=>p.stance);return {rate,meanAbsoluteForwardSpeed:mean(ps.map(p=>Math.abs(.42+p.vz*rate))),rmsHorizontalSpeed:Math.sqrt(mean(ps.map(p=>(.42+p.vz*rate)**2+(p.vx*rate)**2))),medianAbsoluteForwardSpeed:median(ps.map(p=>Math.abs(.42+p.vz*rate)))};})},
   sides:['Left','Right'].map(side=>{const ps=pairs.filter(p=>p.side===side);return {side,impliedSpeed:-mean(ps.map(p=>p.vz)),medianImpliedSpeed:median(ps.map(p=>-p.vz))};})});
 }
 const stanceDisplacement=[];
 for(const side of ['Left','Right']){
  let best={length:0};
  for(let v=0;v<masks[side].length;v++){
   let start=-1;
   for(let f=0;f<n;f++){
    const contact=frames[f].feet[side][v][1]<=.002 && frames[f+1].feet[side][v][1]<=.002 && frames[f+1].ankles[side][2]<frames[f].ankles[side][2];
    if(contact && start<0)start=f;
    if(start>=0 && (!contact || f===n-1)){
     const end=contact?f+1:f;
     if(end-start>best.length)best={length:end-start,start,end,v};
     start=-1;
    }
   }
  }
  const a=frames[best.start].feet[side][best.v],b=frames[best.end].feet[side][best.v],seconds=best.length*dt;
  stanceDisplacement.push({side,vertex:masks[side][best.v],start:best.start*dt,end:best.end*dt,criterion:'Longest continuous same-vertex Y <=2mm, foot bone moving backward',
   rates:[1,1.75].map(rate=>({rate,stanceRealSeconds:seconds/rate,forwardDisplacement:.42*seconds/rate+(b[2]-a[2])*ASTRONAUT_SCALE,lateralDisplacement:(b[0]-a[0])*ASTRONAUT_SCALE}))});
 }
 const report={scale:ASTRONAUT_SCALE,duration:walk.duration,playerSpeed:.42,currentCycleDistance:.42*walk.duration,sampleHz:1/dt,stanceDisplacement,
  convention:'Asset +Z-forward; runtime PI facing maps to player -Z. Residual along movement = player speed + scaled asset Z stance velocity. Same material vertex at both near-floor endpoints; no centroid substitution. Ground-corrected boot rolling means this is a contact proxy, not force/contact labeling.',summaries};
 fs.writeFileSync(path.join(__dirname,'stride-analysis.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(summaries.map(s=>({threshold:s.thresholdAssetMeters,sides:s.sides,rates:s.rates.filter(r=>[1,1.65,1.75,1.8].includes(r.rate)),stance:s.kinematicStance})),null,2));
 fs.writeFileSync(path.join(__dirname,'foot-phases.json'),JSON.stringify(frames.filter((_,i)=>i%16===0).map(f=>({time:f.time,ankles:f.ankles,minimum:Object.fromEntries(['Left','Right'].map(side=>[side,Math.min(...f.feet[side].map(p=>p[1]))]))})),null,2));
})();
