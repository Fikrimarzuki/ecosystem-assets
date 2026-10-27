const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const app='D:/Code/porto-projects/app-gateway-fe',req=Module.createRequire(app+'/package.json'),ts=req('typescript');
require.extensions['.ts']=(m,f)=>m._compile(ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,f);
const {ThirdPersonCamera,THIRD_PERSON,cameraBoomFraction}=require(app+'/lib/third-person.ts'),{groundHeight}=require(app+'/lib/first-person.ts'),{PerspectiveCamera,Vector3}=req('three');
const r=JSON.parse(fs.readFileSync(path.join(__dirname,'report.json'))),out={hardware:r.hardware,runs:[],constraints:[],poseGroups:[]};
r.runs.push(...JSON.parse(fs.readFileSync(path.join(__dirname,'targeted-report.json'))).runs);
const stats=a=>{const s=[...a].sort((a,b)=>a-b);return{mean:s.reduce((a,b)=>a+b,0)/s.length,p95:s[Math.floor(s.length*.95)],max:s.at(-1)};};
const failed=f=>f.meshCrop>.5||f.mesh.behind>0||f.mesh.clippedDepth>0;
for(const run of r.runs){
 const f=run.frames,m=f.filter(f=>f.mesh),events=[];let event;
 for(let i=0;i<m.length;i++){const sample=m[i],cropped=failed(sample);
  if(cropped){if(!event)event={start:sample.t,end:sample.t,count:0,max:0,previousGood:m[i-1]?.t??sample.t};event.end=sample.t;event.count++;event.max=Math.max(event.max,sample.meshCrop);}
  if(event&&(!cropped||i===m.length-1)){event.sampleSpanMs=event.end-event.start;event.bracketMs=sample.t-event.previousGood;events.push(event);event=null;}
 }
 const cropped=m.filter(x=>x.meshCrop>.5),moving=m.filter(x=>x.speed>.0001),tail=m.slice(-10),bootBody=m.map(x=>x.body);
 out.runs.push({name:run.name,durationMs:f.at(-1).t-f[0].t,renderFrames:f.length,meshSamples:m.length,croppedSamples:cropped.length,croppedPercent:cropped.length/m.length*100,framingFailures:m.filter(failed).length,framingFailurePercent:m.filter(failed).length/m.length*100,movingSamples:moving.length,movingCroppedSamples:moving.filter(x=>x.meshCrop>.5).length,maxCroppingPx:Math.max(...m.map(x=>x.meshCrop)),maxCroppingAt75Px:Math.max(...m.map(x=>x.mesh75Crop)),events,tailMaxCroppingPx:Math.max(...tail.map(x=>x.meshCrop)),tailFailures:tail.filter(failed).length,shadowError:stats(f.map(x=>x.shadowError)),scanCostMs:stats(m.map(x=>x.diagnosticMs)),meshSampleIntervalsMs:stats(m.slice(1).map((x,i)=>x.t-m[i].t)),maxBody:{side:Math.max(...bootBody.flatMap(x=>[Math.abs(x.minX),Math.abs(x.maxX)])),depth:Math.max(...bootBody.flatMap(x=>[Math.abs(x.minZ),Math.abs(x.maxZ)])),height:Math.max(...bootBody.map(x=>x.maxY)),minHeight:Math.min(...bootBody.map(x=>x.minY))},envelopeDetectsAllCropped:cropped.every(x=>x.envelopeCrop>.5),blockedHeldFrames:f.filter(f=>f.keys?.length&&f.speed<.0001).length,blockedHeldIdleFrames:f.filter(f=>f.keys?.length&&f.speed<.0001&&f.animation.clip==='Idle').length,worst:run.worst.frame});
 if(!cropped.length)continue;
 const reference=run.matchedWorst??run.worst,w=reference.frame,p={position:{x:w.player.x,y:w.player.y,z:w.player.z},yaw:w.player.yaw,pitch:w.player.pitch},nav=run.navigation,vertices=reference.vertices;
 const projection=(position,target,fov=75)=>{const cam=new PerspectiveCamera(fov,1.6,.01/1.025,100);cam.position.set(position.x,position.y,position.z);cam.lookAt(target.x,target.y,target.z);cam.updateMatrixWorld();let minY=Infinity,maxY=-Infinity,minX=Infinity,maxX=-Infinity,behind=0,near=0,required=65;
  for(const v of vertices){const eye=new Vector3(...v).applyMatrix4(cam.matrixWorldInverse);if(eye.z>=0){behind++;continue;}required=Math.max(required,2*Math.atan(Math.max(Math.abs(eye.y),Math.abs(eye.x)/1.6)/(-eye.z*.92))*180/Math.PI);const q=new Vector3(...v).project(cam);if(q.z < -1||q.z>1){near++;continue;}minY=Math.min(minY,q.y);maxY=Math.max(maxY,q.y);minX=Math.min(minX,q.x);maxX=Math.max(maxX,q.x);}
  return{cropPx:Math.max(0,(-1-minY)*450,(maxY-1)*450,(-1-minX)*720,(maxX-1)*720),requiredFov:required,behind,near,boomClear:cameraBoomFraction(target,position,nav.obstacles),boomLength:Math.hypot(position.x-target.x,position.y-target.y,position.z-target.z)};
 };
 const current={x:w.cameraLocal[0],y:w.cameraLocal[1],z:w.cameraLocal[2]},pivot={...p.position,y:p.position.y+(nav.worldId==='latest'?.47:.35)};
 for(const b of nav.obstacles)if(b.min.y>=p.position.y+.30-.0001&&pivot.x>=b.min.x-.035&&pivot.x<=b.max.x+.035&&pivot.z>=b.min.z-.035&&pivot.z<=b.max.z+.035&&pivot.y>=b.min.y-.035)pivot.y=b.min.y-.035-.002;
 const freeze=new ThirdPersonCamera();freeze.update(p,nav,0,true,true,1.6);
 const follow=new ThirdPersonCamera();follow.position={...current};follow.target={...pivot};follow.initialized=true;follow.fov=w.fov;follow.visibilityView=w.visibilityView;for(let i=0;i<240;i++)follow.update(p,nav,1/60,false,true,1.6);
 const candidates=[{name:'actual-current',position:current,target:pivot},{name:'fresh-reduced-placement',position:freeze.position,target:freeze.target},{name:'frozen-player-follow-4s',position:follow.position,target:follow.target}];
 const views=[[0,-.16,.68],[-.25,0,.68],[.25,0,.68],[-.50,0,.68],[.50,0,.68],[0,-.32,.68],[0,-.16,.55],[-.50,-.16,.68],[.50,-.16,.68]];
 for(const [i,[yo,po,d]]of views.entries()){
  const yaw=p.yaw+yo,pitch=Math.max(THIRD_PERSON.pitchMin,p.pitch+po),raw={x:pivot.x+Math.sin(yaw)*Math.cos(pitch)*d,y:pivot.y-Math.sin(pitch)*d,z:pivot.z+Math.cos(yaw)*Math.cos(pitch)*d};
  raw.y=Math.max(raw.y,groundHeight(nav,raw.x,raw.z)+THIRD_PERSON.radius);if(Number.isFinite(w.trace.ceiling))raw.y=Math.min(raw.y,w.trace.ceiling);
  const t=cameraBoomFraction(pivot,raw,nav.obstacles),position={x:pivot.x+(raw.x-pivot.x)*t,y:pivot.y+(raw.y-pivot.y)*t,z:pivot.z+(raw.z-pivot.z)*t};
  candidates.push({name:'existing-view-'+i,position,target:pivot});
 }
 for(const c of candidates){c.projection=c.name==='actual-current'?{cropPx:w.mesh75Crop,requiredFov:w.mesh75.requiredFov,behind:w.mesh75.behind,near:w.mesh75.clippedDepth,boomClear:cameraBoomFraction(pivot,current,nav.obstacles),boomLength:Math.hypot(current.x-pivot.x,current.y-pivot.y,current.z-pivot.z),method:'Actual rendered-camera projection; do not reconstruct lookAt at zero boom'}:projection(c.position,c.target);c.visibility=[0,.08,.16,.25,.32].map(height=>cameraBoomFraction(c.position,{...p.position,y:p.position.y+height},nav.obstacles,0));
  let total=0,visible=0;for(const [i,[side,depth,height]]of [[-.065,-.05,.01],[.065,-.05,.01],[-.065,.05,.01],[.065,.05,.01],[0,0,.01],[0,0,.15],[0,0,.25]].entries()){
   const sin=Math.sin(p.yaw),cos=Math.cos(p.yaw),probe={x:p.position.x+cos*side+sin*depth,y:p.position.y+height,z:p.position.z-sin*side+cos*depth};
   if(cameraBoomFraction(probe,probe,nav.obstacles,0)===1){const weight=i<5?1:2;total+=weight;if(cameraBoomFraction(c.position,probe,nav.obstacles,0)===1)visible+=weight;}
  }c.visibilityScore={visible,total};
 }
 out.constraints.push({name:run.name,player:p,candidates});
}
const meshSamples=r.runs.flatMap(r=>r.frames.filter(f=>f.mesh));
for(const [name,predicate]of [['Idle',f=>f.animation.walkWeight===0],['Walk-full',f=>f.animation.walkWeight===1],['Crossfade',f=>f.animation.walkWeight>0&&f.animation.walkWeight<1],...Array.from({length:4},(_,i)=>['Walk-quarter-'+i,f=>f.animation.walkWeight===1&&Math.floor(f.animation.walkTime/1.0333333015441895*4)%4===i])]){
 const samples=meshSamples.filter(predicate);out.poseGroups.push({name,count:samples.length,maxSide:Math.max(...samples.flatMap(f=>[Math.abs(f.body.minX),Math.abs(f.body.maxX)])),maxDepth:Math.max(...samples.flatMap(f=>[Math.abs(f.body.minZ),Math.abs(f.body.maxZ)])),maxHeight:Math.max(...samples.map(f=>f.body.maxY)),cropped:samples.filter(f=>f.meshCrop>.5).length,meshOutsidePredictedProjection:samples.filter(f=>f.mesh.minX<f.envelope.minX||f.mesh.maxX>f.envelope.maxX||f.mesh.minY<f.envelope.minY||f.mesh.maxY>f.envelope.maxY).length});
}
fs.writeFileSync(path.join(__dirname,'analysis.json'),JSON.stringify(out,null,2));
console.log(JSON.stringify({runs:out.runs.map(({worst,...x})=>x),constraints:out.constraints.map(x=>({name:x.name,candidates:x.candidates.map(c=>({name:c.name,...c.projection,visibility:c.visibility}))}))},null,2));
