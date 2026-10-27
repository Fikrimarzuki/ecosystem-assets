// Offline exact-box environmental penetration; source assets are read-only.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const app=path.resolve('app-gateway-fe'),req=Module.createRequire(path.join(app,'package.json')),ts=req('typescript'),T=req('three'),sharp=req('sharp');
const resolve=Module._resolveFilename;
Module._resolveFilename=function(id,parent,...rest){return resolve.call(this,id.startsWith('@/')?path.join(app,id.slice(2)):id,parent,...rest);};
for(const ext of ['.ts','.tsx'])require.extensions[ext]=(m,file)=>{
 const baseline=process.argv[2]==='baseline' && ['world-recipes.ts','world-navigation.ts'].includes(path.basename(file));
 const source=baseline?path.join(__dirname,path.basename(file)==='world-recipes.ts'?'baseline-recipes.ts':'baseline-navigation.ts'):file;
 m._compile(ts.transpileModule(fs.readFileSync(source,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,file);
};
const {worldRecipe}=require(path.join(app,'components/universe/world-recipes.ts')), {worldNavigation}=require(path.join(app,'components/universe/world-navigation.ts'));
const {universePlanets}=require(path.join(app,'lib/universe-config.ts')), {safePosition,groundHeight,FirstPersonPlayer}=require(path.join(app,'lib/first-person.ts'));
const {AstronautAnimation}=require(path.join(app,'lib/astronaut-animation.ts')), {ASTRONAUT_SCALE}=require(path.join(app,'lib/astronaut-asset.ts'));
globalThis.self=globalThis;globalThis.ProgressEvent=class{};
globalThis.createImageBitmap=async blob=>{const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});return {data,width:info.width,height:info.height,close(){}};};
(async()=>{
 const {GLTFLoader}=await import(require('node:url').pathToFileURL(path.join(app,'node_modules/three/examples/jsm/loaders/GLTFLoader.js')).href);
 const bytes=fs.readFileSync(path.join(app,'public/models/astronaut/astronaut-animated.glb')),asset=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
 const mesh=asset.scene.getObjectsByProperty('isSkinnedMesh',true)[0],p=mesh.geometry.attributes.position,point=new T.Vector3(),boots=[];
 for(const side of ['Left','Right']){const id=mesh.skeleton.bones.findIndex(b=>b.name.endsWith(side+'Foot')),ankle=new T.Vector3().setFromMatrixPosition(new T.Matrix4().copy(mesh.skeleton.boneInverses[id]).invert());for(let i=0;i<p.count;i++)if(p.getY(i)<=ankle.y+.12 && p.getX(i)*(side==='Left'?1:-1)>0)boots.push(i);}
 const poses=[],playback=new AstronautAnimation(asset);let maximumAvatarHeight=0;
 // Sample actual calibrated runtime, including the incoming fade and >2 cycles.
 for(let frame=0;frame<180;frame++){
  playback.update(1/120,.42,true,false);asset.scene.updateMatrixWorld(true);mesh.skeleton.update();
  for(let i=0;i<p.count;i++){mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);maximumAvatarHeight=Math.max(maximumAvatarHeight,(point.y+playback.visualLift)*ASTRONAUT_SCALE);}
  poses.push({frame,...playback.snapshot(),points:boots.map(i=>{mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);point.multiplyScalar(ASTRONAUT_SCALE);point.y+=playback.visualLift*ASTRONAUT_SCALE;return point.toArray();})});
 }
 playback.dispose();
 const report={stridePreserved:true,poses:poses.length,bootVertices:boots.length,maximumBootRadius:poses.reduce((r,p)=>p.points.reduce((r,v)=>Math.max(r,Math.hypot(v[0],v[2])),r),0),cases:[],navigation:{}};
 for(const id of ['tools','latest']){
  const planet=universePlanets.find(w=>w.id===id),nav=worldNavigation(planet),parts=worldRecipe(planet);
  const solids=id==='tools'?[parts.find(p=>p.shape==='box'&&p.position[0]===.48&&p.position[1]===.34)]:parts.filter(p=>p.navigationRole==='path');
  const approach=new FirstPersonPlayer();approach.enter(nav);approach.setActive(true);approach.yaw=-Math.PI/2;approach.position={x:0,y:groundHeight(nav,0,.64),z:.64};approach.key('KeyW',true);for(let i=0;i<180;i++)approach.advance(1/120);
  const locations=id==='tools'?[{name:'audited-bench',x:.0977947554244788,z:.5782330583555203,yaw:3.1537622749235497},
   {name:'bench-wall-stop',x:approach.position.x,z:approach.position.z,yaw:-Math.PI/2},
   {name:'tools-road-edge',x:-.3170893728,z:.5496432599,yaw:1.83965392077,kind:'path'}]:[{name:'horizontal-road-edge',x:0,z:.55,yaw:0},{name:'cross-road-edge',x:.4,z:.1,yaw:Math.PI/2}];
  for(const location of locations){
   const caseSolids=location.kind==='path'?parts.filter(p=>p.navigationRole==='path'):solids;
   const y=groundHeight(nav,location.x,location.z),sin=Math.sin(location.yaw+Math.PI),cos=Math.cos(location.yaw+Math.PI);
   let maximumDepth=0,maximumVerticalDepth=0,totalVertices=0,intersectingPoses=0;const frames=[];
   for(const pose of poses){let count=0,depth=0;
    for(const [x,py,z] of pose.points){const q={x:location.x+cos*x+sin*z,y:y+py,z:location.z-sin*x+cos*z};
     for(const solid of caseSolids){const min=solid.position.map((v,i)=>v-solid.size[i]/2),max=solid.position.map((v,i)=>v+solid.size[i]/2);
      if(q.x>min[0]+1e-7&&q.x<max[0]-1e-7&&q.y>min[1]+1e-7&&q.y<max[1]-1e-7&&q.z>min[2]+1e-7&&q.z<max[2]-1e-7){count++;maximumVerticalDepth=Math.max(maximumVerticalDepth,max[1]-q.y);depth=Math.max(depth,Math.min(q.x-min[0],max[0]-q.x,q.y-min[1],max[1]-q.y,q.z-min[2],max[2]-q.z));break;}}
    }
    maximumDepth=Math.max(maximumDepth,depth);totalVertices+=count;if(count)intersectingPoses++;frames.push({frame:pose.frame,walkTime:pose.walkTime,walkRate:pose.walkRate,weight:pose.walkWeight,count,depth});
   }
   report.cases.push({world:id,...location,y,valid:safePosition(nav,location.x,location.z),maximumDepth,maximumVerticalDepth,totalVertexSamples:totalVertices,intersectingPoses,frames});
  }
  const player=new FirstPersonPlayer();player.enter(nav);player.setActive(true);
  player.yaw=id==='tools'?-Math.PI/2:Math.PI; // Tools approaches west bench face; Latest crosses front road edge.
  if(id==='tools')player.position={x:0,y:groundHeight(nav,0,.64),z:.64};
  player.key('KeyW',true);const trajectory=[];
  for(let i=0;i<180;i++){player.advance(1/120);trajectory.push({...player.position});}
  const allowed=[];
  for(let ix=-65;ix<=65;ix++)for(let iz=-60;iz<=60;iz++)if(safePosition(nav,ix*.02,iz*.02))allowed.push(ix+':'+iz);
  report.navigation[id]={spawn:nav.spawn,solids,stop:player.position,trajectory,allowedGrid:allowed,obstacles:nav.obstacles};
 }
 // Attribute the old mixed-box count before treating it as bench-only evidence.
 const historical=JSON.parse(fs.readFileSync('gateway-assets/automation/m7.3c.1/browser-report.json','utf8')).samples.find(s=>s.name==='tools-clear-angle-walking');
 const mix=new T.AnimationMixer(asset.scene),history=historical.astronaut.animation;
 for(const clip of asset.animations){const action=mix.clipAction(clip).play();action.time=clip.name==='Idle'?history.idleTime:history.walkTime;action.setEffectiveWeight(clip.name==='Idle'?history.idleWeight:history.walkWeight);}
 mix.update(0);asset.scene.updateMatrixWorld(true);mesh.skeleton.update();
 const transform=new T.Matrix4().makeRotationY(historical.character.yaw+Math.PI).scale(new T.Vector3(ASTRONAUT_SCALE,ASTRONAUT_SCALE,ASTRONAUT_SCALE));
 transform.setPosition(historical.player.position.x,historical.player.position.y+historical.astronaut.model.position[1],historical.player.position.z);
 report.historicalPartAttribution=[];
 for(const part of worldRecipe(universePlanets.find(w=>w.id==='tools'))){if(part.shape!=='box'||part.rotation?.some(v=>v!==0))continue;let count=0,depth=0;
  for(const i of boots){mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld).applyMatrix4(transform);const d=Math.min(...part.position.flatMap((v,i)=>[point.getComponent(i)-v+part.size[i]/2,v+part.size[i]/2-point.getComponent(i)]));if(d>1e-5){count++;depth=Math.max(depth,d);}}
  if(count)report.historicalPartAttribution.push({part,count,depth});
 }
 mix.stopAllAction();mix.uncacheRoot(asset.scene);
 // Lowered Latest support permits under-roof fringe points. Check posed height
 // across Idle and stop fades rather than assuming the visual equals PLAYER.height.
 if(process.argv[2]!=='baseline') {
  for(const idlePhase of [0,2,5,8])for(const stopPhase of [0,.25,.5,.75]){
   const c=new AstronautAnimation(asset);c.mixer.setTime(idlePhase);c.update(0,0,true,false);
   for(const [steps,speed] of [[Math.ceil((.25+stopPhase)*120),.42],[24,0]]) for(let step=0;step<steps;step++){
    c.update(1/120,speed,true,false);asset.scene.updateMatrixWorld(true);mesh.skeleton.update();
    for(let i=0;i<p.count;i++){mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld);maximumAvatarHeight=Math.max(maximumAvatarHeight,(point.y+c.visualLift)*ASTRONAUT_SCALE);}
   }
   c.dispose();
  }
 }
 report.maximumAvatarHeight=maximumAvatarHeight;
 const name=process.argv[2]||'baseline';fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({name,cases:report.cases.map(({frames,...c})=>c),historicalPartAttribution:report.historicalPartAttribution},null,2));
})();
