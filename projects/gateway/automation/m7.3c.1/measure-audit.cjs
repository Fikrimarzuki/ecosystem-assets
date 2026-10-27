// Read existing TS modules/GLB; no runtime/source mutations or asset writes.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const app=path.resolve('app-gateway-fe'),out=__dirname,req=Module.createRequire(path.join(app,'package.json'));
const ts=req('typescript'),THREE=req('three'),sharp=req('sharp');
const original=Module._resolveFilename;
Module._resolveFilename=function(id,parent,...rest){return original.call(this,id.startsWith('@/')?path.join(app,id.slice(2)):id,parent,...rest);};
for(const ext of ['.ts','.tsx'])require.extensions[ext]=(m,file)=>m._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,file);
const {AstronautAnimation}=require(path.join(app,'lib/astronaut-animation.ts'));
const {ThirdPersonCamera,thirdPersonSpawnPitch,thirdPersonSpawnYaw,THIRD_PERSON}=require(path.join(app,'lib/third-person.ts'));
const {PLAYER,groundHeight}=require(path.join(app,'lib/first-person.ts'));
const {worldRecipe}=require(path.join(app,'components/universe/world-recipes.ts'));
const {worldNavigation}=require(path.join(app,'components/universe/world-navigation.ts'));
const {bakeDiorama}=require(path.join(app,'components/universe/diorama-primitives.tsx'));
const {universePlanets}=require(path.join(app,'lib/universe-config.ts'));
const {Vector3,Matrix4,AnimationMixer,Raycaster,Mesh,MeshBasicMaterial,PerspectiveCamera,Quaternion}=THREE;
const scale=.3/1.891089441470219;
globalThis.self=globalThis;globalThis.ProgressEvent=class{};
globalThis.createImageBitmap=async blob=>{const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});return{data,width:info.width,height:info.height,close(){}};};
(async()=>{
 const {GLTFLoader}=await import(require('node:url').pathToFileURL(path.join(app,'node_modules/three/examples/jsm/loaders/GLTFLoader.js')).href);
 const bytes=fs.readFileSync(path.join(app,'public/models/astronaut/astronaut-animated.glb'));
 const asset=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 const mesh=asset.scene.getObjectsByProperty('isSkinnedMesh',true)[0],point=new Vector3(),bones=mesh.skeleton.bones;
 const masks={};
 for(const side of ['Left','Right']){const b=bones.findIndex(b=>b.name.endsWith(side+'Foot')),foot=new Vector3().setFromMatrixPosition(new Matrix4().copy(mesh.skeleton.boneInverses[b]).invert()),p=mesh.geometry.attributes.position;masks[side]=Array.from({length:p.count},(_,i)=>i).filter(i=>p.getY(i)<=foot.y+.12&&(side==='Left'?p.getX(i)>0:p.getX(i)<0));}
 function sampleBoots(){asset.scene.updateMatrixWorld(true);mesh.skeleton.update();const result={};for(const side of ['Left','Right']){let low=Infinity,index=0;const center=new Vector3();for(const i of masks[side]){mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);center.add(point);if(point.y<low){low=point.y;index=i;}}center.divideScalar(masks[side].length);mesh.getVertexPosition(index,point).applyMatrix4(mesh.matrixWorld);result[side]={min:low,lowest:point.toArray(),centroid:center.toArray(),bone:bones.find(b=>b.name.endsWith(side+'Foot')).getWorldPosition(new Vector3()).toArray()};}return result;}
 // Contact-speed evidence: finite difference of the boot centroid/ankle during low-clearance samples.
 const mixer=new AnimationMixer(asset.scene),walk=asset.animations.find(c=>c.name==='Walk'),action=mixer.clipAction(walk).play(),walkSamples=[];
 for(let i=0;i<=248;i++){const t=i*walk.duration/248;mixer.setTime(t);walkSamples.push({time:t,feet:sampleBoots()});}
 const stride={};
 for(const side of ['Left','Right']){const spans=[];let current=[];for(let i=0;i<248;i++){const a=walkSamples[i],b=walkSamples[i+1],f=a.feet[side],g=b.feet[side],dt=b.time-a.time;
  // <=10mm asset (1.586mm player) defines a diagnostic near-floor window, not asserted physical stance.
  const velocity=(g.centroid[2]-f.centroid[2])/dt*scale;
  if(f.min<=.01&&g.min<=.01){current.push({t:a.time,velocity,worldSpeed:PLAYER.speed+velocity});}else if(current.length){spans.push(current);current=[];}}
 if(current.length)spans.push(current);
 stride[side]=spans.filter(s=>s.length>=3).map(s=>({start:s[0].t,end:s.at(-1).t+walk.duration/248,samples:s.length,meanBackwardSpeed:-s.reduce((a,b)=>a+b.velocity,0)/s.length,minBackwardSpeed:Math.min(...s.map(v=>-v.velocity)),maxBackwardSpeed:Math.max(...s.map(v=>-v.velocity)),meanResidualForwardSpeed:s.reduce((a,b)=>a+b.worldSpeed,0)/s.length}));}
 // Track the SAME near-floor sole vertices across adjacent frames; distinguishes sliding from boot rolling/centroid motion.
 const soleVelocity={},previous={};for(const side of ['Left','Right'])soleVelocity[side]={values:[],intervals:0};
 for(let frame=0;frame<=248;frame++){mixer.setTime(frame*walk.duration/248);asset.scene.updateMatrixWorld(true);mesh.skeleton.update();for(const side of ['Left','Right']){const now=masks[side].map(i=>{mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);return point.toArray();});let contacts=0;
 if(previous[side])for(let j=0;j<now.length;j++){const a=previous[side][j],b=now[j];if(a[1]<=.002&&b[1]<=.002){soleVelocity[side].values.push(PLAYER.speed+(b[2]-a[2])/(walk.duration/248)*scale);contacts++;}}
 if(contacts)soleVelocity[side].intervals++;previous[side]=now;}}
 for(const side of ['Left','Right']){const s=soleVelocity[side],v=s.values.sort((a,b)=>a-b);soleVelocity[side]={criterion:'Same vertex Y <=2mm asset (0.317mm player) at both interval endpoints, all directions; hypothetical straight full-speed travel',intervalsWithContact:s.intervals,vertexPairs:v.length,meanForwardWorldSpeed:v.reduce((a,b)=>a+b,0)/v.length,medianForwardWorldSpeed:v[Math.floor(v.length/2)],minForwardWorldSpeed:v[0],maxForwardWorldSpeed:v.at(-1),fractionForward:v.filter(x=>x>.01).length/v.length};}
 mixer.stopAllAction();mixer.uncacheRoot(asset.scene);
 const fpsResults={};
 for(const fps of [15,20,30,60]){let maxStep=0,maxLift=0,errors=0;for(let phase=0;phase<24;phase++){const c=new AstronautAnimation(asset);const duration=.2+phase/24*walk.duration;let elapsed=0;while(elapsed<duration-1e-8){const dt=Math.min(1/120,duration-elapsed);c.update(dt,.42,true,false);elapsed+=dt;}let prior=0;for(let i=0;i<Math.ceil(.3*fps);i++){try{c.update(1/fps,0,true,false);maxStep=Math.max(maxStep,Math.abs(c.visualLift-prior)*scale);maxLift=Math.max(maxLift,c.visualLift*scale);prior=c.visualLift;}catch{errors++;break;}}c.dispose();}fpsResults[fps]={stopPhases:24,maxStepPlayerMeters:maxStep,maxLiftPlayerMeters:maxLift,errors};}
 // Native recipe/nav spawn rays at six worlds: mathematical inspection, not six browser flows.
 const spawnFindings=[];
 for(const planet of universePlanets){const nav=worldNavigation(planet),camera=new ThirdPersonCamera(),pitch=thirdPersonSpawnPitch(nav),yaw=thirdPersonSpawnYaw(nav);camera.update({position:nav.spawn,yaw,pitch},nav,0,true);
  spawnFindings.push({world:planet.id,groundY:nav.groundY,spawn:nav.spawn,pitch,yaw,camera:camera.position,target:camera.target,fov:camera.fov,distance:new Vector3(camera.position.x,camera.position.y,camera.position.z).distanceTo(new Vector3(camera.target.x,camera.target.y,camera.target.z)),pathHeightAboveDeck:nav.spawn.y-nav.groundY});}
 const backwardNearFloor={};
 for(const side of ['Left','Right']){const values=[];for(let i=0;i<248;i++){const a=walkSamples[i],b=walkSamples[i+1],f=a.feet[side],g=b.feet[side],dt=b.time-a.time,centroidSpeed=-(g.centroid[2]-f.centroid[2])/dt*scale,boneSpeed=-(g.bone[2]-f.bone[2])/dt*scale;
 if(f.min<=.01&&g.min<=.01&&centroidSpeed>.05)values.push({time:a.time,centroidSpeed,boneSpeed});}
 backwardNearFloor[side]={samples:values.length,criterion:'Near-floor at both endpoints and backward centroid speed >0.05 player units/s; excludes forward swing, not a full contact detector',meanBackwardSpeed:values.reduce((s,v)=>s+v.centroidSpeed,0)/values.length,maxBackwardSpeed:Math.max(...values.map(v=>v.centroidSpeed)),meanBoneBackwardSpeed:values.reduce((s,v)=>s+v.boneSpeed,0)/values.length,meanResidualForwardSpeed:PLAYER.speed-values.reduce((s,v)=>s+v.centroidSpeed,0)/values.length};}
 const cameraEvidence=[];
 const browserFile=path.join(out,'browser-report.json');
 const browser=fs.existsSync(browserFile)?JSON.parse(fs.readFileSync(browserFile)):null;
 const scenarios=browser?browser.samples.filter(s=>s.nav&&s.astronaut.animation):[];
 const clearFile=path.join(out,'clear-walk-report.json');if(fs.existsSync(clearFile))scenarios.push(...JSON.parse(fs.readFileSync(clearFile)).shots);
 for(const spawn of spawnFindings){const p=universePlanets.find(p=>p.id===spawn.world),nav=worldNavigation(p);scenarios.push({name:'simulated-spawn-'+p.id,nav,player:{position:nav.spawn,yaw:spawn.yaw,pitch:spawn.pitch},character:{yaw:spawn.yaw},localCamera:spawn.camera,localTarget:spawn.target,cameraFov:spawn.fov,canvas:{width:1440,height:900},astronaut:{animation:{idleTime:0,walkTime:0,idleWeight:1,walkWeight:0},model:{position:[0,0,0]}}});}
 for(const s of scenarios){const planet=universePlanets.find(p=>p.id===s.nav.worldId),parts=worldRecipe(planet),geometries=parts.map(p=>{const m=new Mesh(bakeDiorama([p]),new MeshBasicMaterial());m.updateMatrixWorld(true);return m;});
 const pose=s.astronaut.animation,mix=new AnimationMixer(asset.scene),ia=mix.clipAction(asset.animations.find(c=>c.name==='Idle')),wa=mix.clipAction(walk);ia.play().setEffectiveWeight(pose.idleWeight);wa.play().setEffectiveWeight(pose.walkWeight);ia.time=pose.idleTime;wa.time=pose.walkTime;mix.update(0);
 const transform=new Matrix4().makeRotationY(s.character.yaw+Math.PI).scale(new Vector3(scale,scale,scale));transform.setPosition(s.player.position.x,s.player.position.y+s.astronaut.model.position[1],s.player.position.z);
 const camera=new PerspectiveCamera(s.cameraFov,s.canvas.width/s.canvas.height,.01/1.025,100);
 if(s.localCamera){camera.position.set(s.localCamera.x,s.localCamera.y,s.localCamera.z);camera.lookAt(s.localTarget.x,s.localTarget.y,s.localTarget.z);}else{const world=new Matrix4().fromArray(s.astronaut.matrix),inv=world.clone().invert(),worldRotation=new Quaternion().setFromRotationMatrix(new Matrix4().extractRotation(world));camera.position.fromArray(s.camera).applyMatrix4(inv);camera.quaternion.copy(worldRotation.invert().multiply(new Quaternion().fromArray(s.cameraQuaternion)));}
 camera.updateMatrixWorld(true);const ray=new Raycaster(),blocked={},bootTotal=masks.Left.length+masks.Right.length;let frustumBoot=0,intersections=0,maxBoxPenetration=0,maxRadius=0,minY=Infinity,maxY=-Infinity;const projected={minX:Infinity,maxX:-Infinity,minY:Infinity,maxY:-Infinity};
 const p=new Vector3(),screen=new Vector3(),direction=new Vector3();asset.scene.updateMatrixWorld(true);mesh.skeleton.update();
 for(let i=0;i<mesh.geometry.attributes.position.count;i++){mesh.getVertexPosition(i,p).applyMatrix4(mesh.matrixWorld).applyMatrix4(transform);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);maxRadius=Math.max(maxRadius,Math.hypot(p.x-s.player.position.x,p.z-s.player.position.z));screen.copy(p).project(camera);projected.minX=Math.min(projected.minX,screen.x);projected.maxX=Math.max(projected.maxX,screen.x);projected.minY=Math.min(projected.minY,screen.y);projected.maxY=Math.max(projected.maxY,screen.y);}
 for(const id of [...masks.Left,...masks.Right]){mesh.getVertexPosition(id,p).applyMatrix4(mesh.matrixWorld).applyMatrix4(transform);screen.copy(p).project(camera);if(Math.abs(screen.x)>1||Math.abs(screen.y)>1||Math.abs(screen.z)>1)frustumBoot++;
 direction.copy(p).sub(camera.position);const distance=direction.length();ray.set(camera.position,direction.normalize());const hits=ray.intersectObjects(geometries,false);if(hits[0]&&hits[0].distance<distance-1e-5){const index=geometries.indexOf(hits[0].object),key=String(index);blocked[key]=(blocked[key]??0)+1;}
 // AABB test only for the confirmed unrotated box bench; exact solid, no empty-corner false positives.
 for(let j=0;j<parts.length;j++){const part=parts[j];if(part.shape!=='box'||part.rotation?.some(v=>v!==0))continue;geometries[j].geometry.computeBoundingBox();const box=geometries[j].geometry.boundingBox;if(box.containsPoint(p)&&p.y>box.min.y+1e-5&&p.y<box.max.y-1e-5){intersections++;maxBoxPenetration=Math.max(maxBoxPenetration,Math.min(p.x-box.min.x,box.max.x-p.x,p.y-box.min.y,box.max.y-p.y,p.z-box.min.z,box.max.z-p.z));break;}}
 }
 const bench=parts.findIndex(p=>p.shape==='box'&&p.position[0]===.48&&p.position[1]===.34);const benches=bench<0?null:geometries[bench].geometry.boundingBox;
 const pivotHeight=s.player.position.y+(s.nav.worldId==='latest'?.47:s.nav.worldId==='platforms'?.435:.35),pivot=new Vector3(s.player.position.x,pivotHeight,s.player.position.z);
 const distanceProbe=[];if(s.name==='simulated-spawn-tools')for(const distance of [.45,.55,.68,.85]){const probe=camera.position.clone().sub(pivot).normalize().multiplyScalar(distance).add(pivot);let count=0;for(const id of [...masks.Left,...masks.Right]){mesh.getVertexPosition(id,p).applyMatrix4(mesh.matrixWorld).applyMatrix4(transform);direction.copy(p).sub(probe);const len=direction.length();ray.set(probe,direction.normalize());const hit=ray.intersectObjects(geometries,false)[0];if(hit&&hit.distance<len-1e-5)count++;}distanceProbe.push({distance,blockedBootVertices:count,cameraInsideBench:benches?.containsPoint(probe)??false});}
 const cameraInsideObstacle=s.nav.obstacles.some(b=>['x','y','z'].every(k=>camera.position[k]>=b.min[k]&&camera.position[k]<=b.max[k])&&(!b.planes||b.planes.every(p=>p.x*camera.position.x+p.y*camera.position.y+p.z*camera.position.z+p.constant<=1e-8)));
 cameraEvidence.push({name:s.name,world:s.nav.worldId,localCamera:camera.position.toArray(),pitch:s.player.pitch,distanceToPivot:camera.position.distanceTo(pivot),cameraInsideObstacle,cameraInsideBench:benches?.containsPoint(camera.position)??false,groundClearance:camera.position.y-groundHeight(s.nav,camera.position.x,camera.position.z),modelGroundClearance:minY-s.player.position.y,modelHeight:maxY-minY,maxVisualRadius:maxRadius,projectedBoundsNDC:projected,bootTotal,bootOutsideFrustum:frustumBoot,bootVerticesInsideUnrotatedBoxes:intersections,maxBoxPenetration,distanceProbe,blockers:Object.entries(blocked).map(([id,count])=>({partIndex:+id,part:parts[+id],blockedBootVertices:count}))});
 mix.stopAllAction();mix.uncacheRoot(asset.scene);geometries.forEach(m=>{m.geometry.dispose();m.material.dispose();});}
 const report={scale,playerSpeed:PLAYER.speed,walkDuration:walk.duration,travelPerCycle:PLAYER.speed*walk.duration,contactWindow:'Boot min <=0.01m asset, interval endpoints both near floor; centroid finite difference; no physical contact classifier',stride,backwardNearFloor,soleVelocity,fpsResults,spawnFindings,cameraEvidence};
 fs.writeFileSync(path.join(out,'measure-report.json'),JSON.stringify(report,null,2));
 fs.writeFileSync(path.join(out,'walk-samples.json'),JSON.stringify(walkSamples,null,2));
 console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
