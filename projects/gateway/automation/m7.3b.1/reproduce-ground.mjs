import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
const app=path.resolve('app-gateway-fe');
const require=createRequire(path.join(app,'package.json'));
const ts=require('typescript'), sharp=require('sharp');
const threeURL=pathToFileURL(path.join(app,'node_modules/three/build/three.module.js')).href;
const {Vector3}=await import(threeURL);
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
const results=[];let minimum=Infinity;
function advance(playback,seconds,speed){while(seconds>1e-8){const step=Math.min(seconds,1/120);playback.update(step,speed,true,false);seconds-=step;}}
function sample(playback,context){
 asset.scene.updateMatrixWorld(true);mesh.skeleton.update();let lowest=Infinity;
 for(let i=0;i<mesh.geometry.attributes.position.count;i++){
  mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);lowest=Math.min(lowest,point.y);
 }
 minimum=Math.min(minimum,lowest);
 return {lowestMeters:lowest,...context,...playback.snapshot()};
}
for(const idlePhase of [0,2,5,8])for(const walkPhase of [.1,.5,.9]){
 const playback=new AstronautAnimation(asset);advance(playback,idlePhase,0);
 for(let i=0;i<24;i++){playback.update(1/120,.42,true,false);results.push(sample(playback,{transition:'Idle->Walk',idlePhase,walkPhase,frame:i}));}
 advance(playback,walkPhase,.42);
 for(let i=0;i<24;i++){playback.update(1/120,0,true,false);results.push(sample(playback,{transition:'Walk->Idle',idlePhase,walkPhase,frame:i}));}
 playback.dispose();
}
const report={sampleRateHz:120,samples:results.length,minimumMeters:minimum,minimumPlayerLocalMeters:minimum*.30/1.891089441470219,
 worst:results.reduce((a,b)=>a.lowestMeters<b.lowestMeters?a:b),samplesBelowGround:results.filter(r=>r.lowestMeters<0).length,
 scope:'Mixed poses only, all skinned vertices; no asset edits, world terrain not included',results};
await fs.writeFile('gateway-assets/automation/m7.3b.1/reproduced-ground-report.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({...report,results:undefined},null,2));
