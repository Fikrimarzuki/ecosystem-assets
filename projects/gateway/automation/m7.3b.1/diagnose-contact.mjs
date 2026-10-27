import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const app=path.resolve('app-gateway-fe');
const require=createRequire(path.join(app,'package.json'));
const ts=require('typescript'), sharp=require('sharp');
const threeURL=pathToFileURL(path.join(app,'node_modules/three/build/three.module.js')).href;
const {Vector3,Matrix4,AnimationMixer,LoopRepeat}=await import(threeURL);
const code=ts.transpileModule(await fs.readFile(path.resolve('gateway-assets/automation/m7.3b.1/baseline-animation.ts'),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}
}).outputText.replace('from "three"',`from "${threeURL}"`);
const {AstronautAnimation}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
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


const baselineCode=await fs.readFile('gateway-assets/automation/m7.3b.1/baseline-animation.ts','utf8');
async function controllerFor(fade=.18,phase=0){
 const modified=baselineCode.replace('ASTRONAUT_FADE_SECONDS = .18',`ASTRONAUT_FADE_SECONDS = ${fade}`).replace('incoming.reset().play();',`{incoming.reset().play();if(next==='Walk') incoming.time=${phase};}`);
 const js=ts.transpileModule(modified,{compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText.replace('from "three"',`from "${threeURL}"`);
 return (await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'))).AstronautAnimation;
}
const masks={};const p=mesh.geometry.attributes.position;
for(const side of ['Left','Right']){
 const index=mesh.skeleton.bones.findIndex(b=>b.name.endsWith(side+'Foot'));
 const rest=new Vector3().setFromMatrixPosition(new Matrix4().copy(mesh.skeleton.boneInverses[index]).invert());
 masks[side]=Array.from({length:p.count},(_,i)=>i).filter(i=>p.getY(i)<=rest.y+.12&&(side==='Left'?p.getX(i)>0:p.getX(i)<0));
}
let absolute=0;const details=[];
function advance(c,seconds,speed){while(seconds>1e-8){const step=Math.min(seconds,1/120);c.update(step,speed,true,false);seconds-=step;}}
function measure(c,context={},full=false){
 asset.scene.updateMatrixWorld(true);mesh.skeleton.update();
 const feet={};let lowest=Infinity,vertex=-1;
 for(const side of ['Left','Right']){
  let y=Infinity,v=-1;
  for(const id of masks[side]){mesh.getVertexPosition(id,point).applyMatrix4(mesh.matrixWorld);if(point.y<y){y=point.y;v=id;}}
  feet[side]={y,vertex:v};if(y<lowest){lowest=y;vertex=v;}
 }
 if(full){
  const covered=new Set(Object.values(masks).flat());
  for(let i=0;i<p.count;i++){mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);if(point.y<-.000001&&!covered.has(i)) throw new Error('Missed penetrating vertex '+i);}
 }
 return {lowestMeters:lowest,vertex,feet,...context,...c.snapshot()};
}
async function sweep(fade,phase=0,full=false){
 const C=await controllerFor(fade,phase);let worst={lowestMeters:Infinity};const minima={'Idle->Walk':Infinity,'Walk->Idle':Infinity};
 for(const idlePhase of [0,2,5,8])for(const walkPhase of [.1,.5,.9]){
  const c=new C(asset);advance(c,idlePhase,0);
  for(const [transition,speed] of [['Idle->Walk',.42],['Walk->Idle',0]]){
   if(!speed)advance(c,walkPhase,.42);
   for(let i=0;i<Math.ceil(fade*120)+2;i++){
    c.update(1/120,speed,true,false);const r=measure(c,{transition,idlePhase,walkPhase,frame:i},full);
    if(fade===.18&&phase===0)details.push(r);
    if(r.lowestMeters<worst.lowestMeters)worst=r;
    minima[transition]=Math.min(minima[transition],r.lowestMeters);
   }
  }
  c.dispose();
 }
 return {fade,initialWalkPhase:phase,minima,worst};
}
const timing=[];for(const fade of [.04,.08,.12,.18,.25])timing.push(await sweep(fade,0,fade===.18));
const phase=[];for(const start of [31/120,31/60,31/40])phase.push(await sweep(.18,start));
const pure={};
for(const name of ['Idle','Walk']){
 const mixer=new AnimationMixer(asset.scene),clip=asset.animations.find(c=>c.name===name);
 const action=mixer.clipAction(clip).setLoop(LoopRepeat,Infinity).play();let worst={lowestMeters:Infinity};
 for(let i=0;i<=Math.ceil(clip.duration*120);i++){
  mixer.setTime(Math.min(clip.duration,i/120));
  const r=measure({snapshot:()=>({clip:name,time:action.time})});if(r.lowestMeters<worst.lowestMeters)worst=r;
 }
 pure[name]=worst;mixer.stopAllAction();mixer.uncacheRoot(asset.scene);
}
// Compare the same lowest vertex at the known worst blend and its clip endpoints.
const c=new AstronautAnimation(asset);advance(c,8,0);advance(c,.2,.42);advance(c,.1,.42);advance(c,11/120,0);
const worst=measure(c);const blended=new Vector3();mesh.getVertexPosition(worst.vertex,blended).applyMatrix4(mesh.matrixWorld);
const bonePositions=()=>Object.fromEntries(mesh.skeleton.bones.filter(b=>/Hips|Left(Foot|UpLeg|Leg)|Right(Foot|UpLeg|Leg)$/.test(b.name)).map(b=>[b.name,b.getWorldPosition(new Vector3()).toArray()]));
const blendedBones=bonePositions();c.dispose();
const endpoints={};
for(const name of ['Idle','Walk']){
 const mixer=new AnimationMixer(asset.scene),clip=asset.animations.find(c=>c.name===name);
 mixer.clipAction(clip).play();mixer.setTime(name==='Idle'?worst.idleTime:worst.walkTime);
 asset.scene.updateMatrixWorld(true);mesh.skeleton.update();
 mesh.getVertexPosition(worst.vertex,point).applyMatrix4(mesh.matrixWorld);
 endpoints[name]={vertex:point.toArray(),bones:bonePositions()};mixer.stopAllAction();mixer.uncacheRoot(asset.scene);
}
const linearEndpointY=endpoints.Idle.vertex[1]*worst.idleWeight+endpoints.Walk.vertex[1]*worst.walkWeight;
const report={sampleRateHz:120,bootMask:'Raw bind/rest geometry below corresponding Foot inverse-bind Y + 0.12m, split by rest X; all penetrating vertices covered in 180ms sweep',bootVertices:Object.fromEntries(Object.entries(masks).map(([k,v])=>[k,v.length])),pure,timing,phase,
 nonlinearComparison:{worst,blendedVertex:blended.toArray(),linearEndpointY,extraDownwardDeviation:blended.y-linearEndpointY,blendedBones,endpoints},details};
await fs.writeFile('gateway-assets/automation/m7.3b.1/diagnosis.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({...report,details:undefined,nonlinearComparison:{worst,linearEndpointY,actualY:blended.y,extraDownwardDeviation:blended.y-linearEndpointY}},null,2));
