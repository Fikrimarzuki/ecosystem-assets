import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const app=path.resolve('app-gateway-fe');
const require=createRequire(path.join(app,'package.json'));
const ts=require('typescript'), sharp=require('sharp');
const threeURL=pathToFileURL(path.join(app,'node_modules/three/build/three.module.js')).href;
const {Vector3,Matrix4,Group,AnimationMixer,LoopRepeat}=await import(threeURL);
const groundJS=ts.transpileModule(await fs.readFile(path.join(app,'lib/astronaut-ground-contact.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText.replace('from "three"',`from "${threeURL}"`);
const groundURL='data:text/javascript;base64,'+Buffer.from(groundJS).toString('base64');
const code=ts.transpileModule(await fs.readFile(path.join(app,'lib/astronaut-animation.ts'),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}
}).outputText.replace('from "three"',`from "${threeURL}"`).replace('from "./astronaut-ground-contact"',`from "${groundURL}"`);
const runtimeCode=process.argv.includes('--smooth')?code.replace('const amount = this.elapsed / ASTRONAUT_FADE_SECONDS;', 'const fraction = this.elapsed / ASTRONAUT_FADE_SECONDS; const amount = fraction*fraction*(3-2*fraction);'):code;
const {AstronautAnimation}=await import('data:text/javascript;base64,'+Buffer.from(runtimeCode).toString('base64'));
globalThis.self=globalThis;
globalThis.ProgressEvent=class{};
globalThis.createImageBitmap=async blob=>{
 const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 return {data,width:info.width,height:info.height,close(){}};
};
const {GLTFLoader}=await import(pathToFileURL(path.join(app,'node_modules/three/examples/jsm/loaders/GLTFLoader.js')).href);
const bytes=await fs.readFile(path.join(app,'public/models/astronaut/astronaut-animated.glb'));
const asset=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
const mesh=asset.scene.getObjectsByProperty('isSkinnedMesh',true)[0], point=new Vector3();



const liftGroup=new Group();liftGroup.add(asset.scene);
const positions=mesh.geometry.attributes.position;
const masks={};
for(const side of ['Left','Right']){
 const id=mesh.skeleton.bones.findIndex(b=>b.name.endsWith(side+'Foot'));
 const foot=new Vector3().setFromMatrixPosition(new Matrix4().copy(mesh.skeleton.boneInverses[id]).invert());
 masks[side]=Array.from({length:positions.count},(_,i)=>i).filter(i=>positions.getY(i)<=foot.y+.12&&(side==='Left'?positions.getX(i)>0:positions.getX(i)<0));
}
const hip=mesh.skeleton.bones.find(b=>b.name==='mixamorigHips'), hipPoint=new Vector3(), previousHips=new WeakMap();
const summaries={};let allWorst={afterMeters:Infinity},maxLift=0,maxStep=0;const samples=[];
function step(c,dt,speed){liftGroup.updateMatrixWorld(true);previousHips.set(c,hip.getWorldPosition(hipPoint).y);c.update(dt,speed,true,false);liftGroup.position.y=c.visualLift;}
function advance(c,seconds,speed){while(seconds>1e-8){const dt=Math.min(seconds,1/120);step(c,dt,speed);seconds-=dt;}}
function sample(c,context,previousLift,full=false){
 liftGroup.updateMatrixWorld(true);mesh.skeleton.update();const feet={};let low=Infinity;
 for(const side of ['Left','Right']){
  let y=Infinity;for(const id of masks[side]){mesh.getVertexPosition(id,point).applyMatrix4(mesh.matrixWorld);y=Math.min(y,point.y);}
  feet[side]={beforeMeters:y-c.visualLift,afterMeters:y};low=Math.min(low,y);
 }
 if(full)for(let i=0;i<positions.count;i++){
  mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);
  if(point.y<low-1e-8)throw new Error('Boot region misses lowest posed vertex');
 }
 const hipStep=Math.abs(hip.getWorldPosition(hipPoint).y-previousHips.get(c));
 const r={...context,hipStepMeters:hipStep,afterMeters:low,beforeMeters:low-c.visualLift,liftMeters:c.visualLift,liftStepMeters:Math.abs(c.visualLift-previousLift),feet,...c.snapshot()};
 const group=summaries[context.scenario]??={samples:0,beforeMeters:Infinity,afterMeters:Infinity,maxLiftMeters:0,maxStepMeters:0,maxHipStepMeters:0,maximumOtherFootGapMeters:0};
 group.maxHipStepMeters=Math.max(group.maxHipStepMeters,hipStep);group.maximumOtherFootGapMeters=Math.max(group.maximumOtherFootGapMeters,feet.Left.afterMeters,feet.Right.afterMeters);
 group.samples++;group.beforeMeters=Math.min(group.beforeMeters,r.beforeMeters);group.afterMeters=Math.min(group.afterMeters,r.afterMeters);group.maxLiftMeters=Math.max(group.maxLiftMeters,r.liftMeters);group.maxStepMeters=Math.max(group.maxStepMeters,r.liftStepMeters);
 if(low<allWorst.afterMeters)allWorst=r;maxLift=Math.max(maxLift,c.visualLift);maxStep=Math.max(maxStep,r.liftStepMeters);
 samples.push(r);return r;
}
function runCase(idlePhase,walkPhase,scenario,full=false){
 const c=new AstronautAnimation(asset);liftGroup.position.y=0;advance(c,idlePhase,0);let prior=0;
 for(const [transition,speed] of [['Idle->Walk',.42],['Walk->Idle',0]]){
  if(!speed)advance(c,walkPhase,.42);
  for(let i=0;i<24;i++){step(c,1/120,speed);sample(c,{scenario,transition,idlePhase,walkPhase,frame:i},prior,full);prior=c.visualLift;}
 }
 c.dispose();liftGroup.position.y=0;
}
for(const idle of [0,2,5,8])for(const walk of [.1,.5,.9])runCase(idle,walk,'previous576',true);
for(const idle of [0,2,5,8])for(let phase=0;phase<24;phase++)runCase(idle,phase/24*31/30,'expanded-phases',phase%6===0);
for(const reversal of [.025,.075,.125,.175]){
 const c=new AstronautAnimation(asset);liftGroup.position.y=0;let prior=0;
 for(let cycle=0;cycle<4;cycle++)for(const speed of [.42,0,.42,0])for(let i=0;i<Math.ceil(reversal*120);i++){
  step(c,1/120,speed);sample(c,{scenario:'reversed-fades',reversal,cycle,speed,frame:i},prior,true);prior=c.visualLift;
 }
 for(let i=0;i<30;i++){step(c,1/120,0);sample(c,{scenario:'reversed-fades-settle',reversal,frame:i},prior,true);prior=c.visualLift;}
 if(c.visualLift!==0)throw new Error('Accumulated lift after settling');c.dispose();liftGroup.position.y=0;
}
for(const name of ['Idle','Walk']){
 const c=new AstronautAnimation(asset);liftGroup.position.y=0;if(name==='Walk')advance(c,.3,.42);
 const seconds=name==='Walk'?31/30*3:250/30;
 for(let i=0;i<=Math.ceil(seconds*120);i++){
  step(c,1/120,name==='Walk'?.42:0);sample(c,{scenario:'pure-'+name,frame:i},0,i%60===0);
  if(c.visualLift!==0)throw new Error('Permanent offset during '+name);
 }
 c.dispose();liftGroup.position.y=0;
}
// Frame-rate checks quantify discrete lift steps, rather than filtering clearance upward.
for(const fps of [30,60])for(let phase=0;phase<24;phase++){
 const c=new AstronautAnimation(asset);liftGroup.position.y=0;advance(c,.2+phase/24*31/30,.42);let prior=0;
 for(let i=0;i<Math.ceil(.25*fps);i++){step(c,1/fps,0);sample(c,{scenario:'steps-'+fps+'fps',phase,frame:i},prior,true);prior=c.visualLift;}
 c.dispose();liftGroup.position.y=0;
}
// New runtime times intentionally differ; do not compare old pose phases by wall time.
for(const speed of [.06,.12,.24,.42,.48])for(let phase=0;phase<8;phase++){
 const c=new AstronautAnimation(asset);liftGroup.position.y=0;advance(c,.2+phase/8*31/30,speed);let prior=0;
 for(const next of [speed*.5,speed,0,speed,0])for(let i=0;i<24;i++){
  step(c,1/120,next);sample(c,{scenario:'dynamic-rates',speed,next,phase,frame:i},prior,true);prior=c.visualLift;
 }
 c.dispose();liftGroup.position.y=0;
}
const maximumReproductionError=null;
const scale=.30/1.891089441470219;
const report={sampleRateHz:120,samples:samples.length,toleranceAssetMeters:.00001,correctionBoundAssetMeters:.08,
 maximumReproductionError,minimumAfterMeters:allWorst.afterMeters,maximumLiftAssetMeters:maxLift,maximumLiftPlayerMeters:maxLift*scale,
 summaries,worst:allWorst,unchangedGLB:true,scope:'Both posed boots; full-mesh checks on previous576, reversals, frame-rate sweeps and periodic expanded/pure samples. Navigation transforms unchanged.',results:samples};
await fs.writeFile('gateway-assets/automation/m7.3c.3/ground-compatibility.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({...report,results:undefined},null,2));
