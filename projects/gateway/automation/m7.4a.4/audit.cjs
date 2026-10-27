const fs=require('node:fs'),path=require('node:path');
const app='D:/Code/porto-projects/app-gateway-fe', ts=require(app+'/node_modules/typescript');
const {chromium,expect}=require(app+'/node_modules/@playwright/test');
const modules={};
for(const name of ['first-person-interaction','first-person','third-person']){
 let source=fs.readFileSync(app+'/lib/'+name+'.ts','utf8');
 if(name==='third-person') source=source.replace('this.position = next;', 'this.trace = { previous: {...this.position}, pivot, rear, desired, ceiling, rearLength, blend, next }; this.position = next;').replace('const fovStep =', 'this.trace.desiredFov = desiredFov; const fovStep =');
 modules['./'+name]=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
}
const probes=[[-.075,-.075,0],[.075,-.075,0],[-.075,.075,0],[.075,.075,0],[0,0,.08],[0,0,.16],[-.075,-.075,.32],[.075,-.075,.32],[-.075,.075,.32],[.075,.075,.32]];
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false});
 const report={browser:browser.version(),runs:[],errors:[],method:'Native movement; exact-source shadow camera; every-render envelope and every-fourth-render full animated mesh, no production edits'};
 const targeted=process.argv.includes('--targeted');
 const save=()=>fs.writeFileSync(path.join(__dirname,targeted?'targeted-report.json':'report.json'),JSON.stringify(report,null,2));
 try{
 const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>report.errors.push(e.message));
 await page.goto('http://127.0.0.1:3001',{timeout:120000});
 const region=page.getByRole('region',{name:'Project Universe'}), scene=region.locator('[data-ready="true"]');await expect(scene).toBeVisible({timeout:60000});await scene.scrollIntoViewIfNeeded();
 await region.locator('canvas').evaluate((canvas,{modules,probes})=>{
  let state;
  for(let f=canvas[Object.keys(canvas).find(k=>k.startsWith('__reactFiber'))];f&&!state;f=f.return)for(let h=f.memoizedState;h;h=h.next){if(h.memoizedState?.current?.gl&&h.memoizedState.current.scene){state=h.memoizedState.current;break;}}
  if(!state)throw Error('Missing R3F state');
  const cache={},load=name=>{if(cache[name])return cache[name].exports;const m=cache[name]={exports:{}};new Function('require','module','exports',modules[name])(load,m,m.exports);return m.exports;};
  const lib=load('./third-person'),q=window.__audit={state,lib,probes,controller:canvas.closest('[data-ready]').__universeController,frames:[],index:0,active:false,shadow:null,wrappers:new WeakSet(),worst:null};
  const gl=state.gl.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');q.hardware={renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):null,webgl:gl.getParameter(gl.VERSION),userAgent:navigator.userAgent};
  q.refresh=()=>{for(const sub of state.internal.subscribers)if(sub.priority===-3&&!q.wrappers.has(sub.ref.current)){
   const original=sub.ref.current;const wrapped=function(...args){const s=q.controller.getSnapshot(),p=q.controller.player;
    if(s.explorationMode!=='third-person')q.shadow=null;
    else if(p.navigation&&(s.firstPersonLocked||!q.shadow)){
     if(q.shadow){const root=state.scene.getObjectByName('exploration-astronaut');root.updateWorldMatrix(true,false);const previous=state.camera.position.clone().applyMatrix4(root.matrixWorld.clone().invert());q.shadow.position={x:previous.x,y:previous.y,z:previous.z};q.shadow.fov=state.camera.fov;}
     q.shadow??=new lib.ThirdPersonCamera();q.delta=args[1];q.shadow.update(p,p.navigation,args[1],s.reduced,true,1.6);
    }
    return original.apply(this,args);
   };q.wrappers.add(wrapped);sub.ref.current=wrapped;
  }};
  q.refresh();
  const originalRender=state.gl.render;
  state.gl.render=function(...args){const result=originalRender.apply(this,args);q.refresh();if(q.active&&q.shadow){
   const start=performance.now(),camera=state.camera,p=q.controller.player,root=state.scene.getObjectByName('exploration-astronaut'),mesh=state.scene.getObjectByName('astronaut-model-placement')?.getObjectsByProperty('isSkinnedMesh',true)[0];
   if(!mesh)return result;
   state.scene.updateMatrixWorld(true);mesh.skeleton.update();camera.updateMatrixWorld();
   const local=root.matrixWorld.clone().invert(),world=camera.position.clone(),point=world.clone(),eye=world.clone(),cameraLocal=camera.position.clone().applyMatrix4(local),shadow=q.shadow;
   const predicted=world.clone().set(shadow.position.x,shadow.position.y,shadow.position.z).applyMatrix4(root.matrixWorld);
   const target=world.clone().set(shadow.target.x,shadow.target.y,shadow.target.z).applyMatrix4(root.matrixWorld);
   const rect=canvas.getBoundingClientRect();
   const makeRange=()=>({minX:Infinity,maxX:-Infinity,minY:Infinity,maxY:-Infinity,behind:0,clippedDepth:0,requiredFov:65});
   const range=makeRange(), at75=makeRange(),envelope=makeRange(),body=makeRange();const limit=camera.clone();limit.fov=75;limit.updateProjectionMatrix();
   const extend=(out,v,cam)=>{eye.copy(v).applyMatrix4(cam.matrixWorldInverse);if(eye.z>=0){out.behind++;return;}
    out.requiredFov=Math.max(out.requiredFov,2*Math.atan(Math.max(Math.abs(eye.y),Math.abs(eye.x)/cam.aspect)/(-eye.z*.92))*180/Math.PI);
    point.copy(v).project(cam);if(point.z < -1 || point.z > 1){out.clippedDepth++;return;}out.minX=Math.min(out.minX,point.x);out.maxX=Math.max(out.maxX,point.x);out.minY=Math.min(out.minY,point.y);out.maxY=Math.max(out.maxY,point.y);
   };
   const c=Math.cos(p.yaw),s=Math.sin(p.yaw);
   for(const [side,depth,height]of probes){world.set(p.position.x+c*side+s*depth,p.position.y+height,p.position.z-s*side+c*depth).applyMatrix4(root.matrixWorld);extend(envelope,world,camera);}
   const scan=q.index++%4===0,vertices=[];
   if(scan)for(let i=0;i<mesh.geometry.attributes.position.count;i++){
    mesh.getVertexPosition(i,world).applyMatrix4(mesh.matrixWorld);extend(range,world,camera);extend(at75,world,limit);
    point.copy(world).applyMatrix4(local);vertices.push(point.toArray());const dx=point.x-p.position.x,dz=point.z-p.position.z;
    const side=c*dx-s*dz,depth=s*dx+c*dz,height=point.y-p.position.y;
    body.minX=Math.min(body.minX,side);body.maxX=Math.max(body.maxX,side);body.minY=Math.min(body.minY,height);body.maxY=Math.max(body.maxY,height);body.minZ=Math.min(body.minZ??Infinity,depth);body.maxZ=Math.max(body.maxZ??-Infinity,depth);
   }
   const crop=r=>Math.max(0,(-1-r.minY)*rect.height/2,(r.maxY-1)*rect.height/2,(-1-r.minX)*rect.width/2,(r.maxX-1)*rect.width/2);
   const snap=root.userData.astronautAnimation?.snapshot();
   const frame={t:performance.now(),delta:q.delta,phase:q.phase,keys:q.keys??[],player:{...p.position,yaw:p.yaw,pitch:p.pitch},speed:q.controller.character.speed,facing:q.controller.character.yaw,animation:snap,camera:camera.position.toArray(),cameraLocal:cameraLocal.toArray(),target:target.toArray(),fov:camera.fov,shadowFov:shadow.fov,shadowError:predicted.distanceTo(camera.position),trace:shadow.trace,settled:shadow.settled,visibilityView:shadow.visibilityView,clearSeconds:shadow.clearSeconds,envelope,envelopeCrop:crop(envelope),mesh:scan?range:null,mesh75:scan?at75:null,body:scan?body:null,meshCrop:scan?crop(range):null,mesh75Crop:scan?crop(at75):null};
   frame.boomClear=lib.cameraBoomFraction(shadow.target,shadow.position,p.navigation.obstacles);frame.boomLength=Math.hypot(shadow.position.x-shadow.target.x,shadow.position.y-shadow.target.y,shadow.position.z-shadow.target.z);
   if(scan&&(!q.worst||frame.meshCrop>q.worst.frame.meshCrop)){q.worst={frame,vertices,png:canvas.toDataURL('image/png')};}
   if(scan&&frame.shadowError<1e-8&&(!q.matchedWorst||frame.meshCrop>q.matchedWorst.frame.meshCrop)){q.matchedWorst={frame,vertices,png:canvas.toDataURL('image/png')};}
   frame.diagnosticMs=performance.now()-start;q.frames.push(frame);
  }return result;};
 },{modules,probes});
 report.hardware=await page.evaluate(()=>window.__audit.hardware);if(/swiftshader|software|llvmpipe/i.test(report.hardware.renderer))throw Error('Physical GPU unavailable');save();
 const look=async(yaw,pitch)=>{await page.mouse.move(720,450);const p=await scene.evaluate(e=>({yaw:e.__universeController.player.yaw,pitch:e.__universeController.player.pitch}));const diff=Math.atan2(Math.sin(p.yaw-yaw),Math.cos(p.yaw-yaw));await page.mouse.move(720+diff/.0025,450+(p.pitch-pitch)/.0025);};
 const enter=async(name)=>{
  await region.getByRole('button',{name,exact:true}).click();await expect(scene).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});await page.waitForTimeout(100);
  await region.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(()=>scene.evaluate(e=>e.__universeRender().astronaut?.visual),{timeout:30000}).toBe('model');
  const angles=await page.evaluate(()=>{const q=window.__audit,n=q.controller.player.navigation;return[q.lib.thirdPersonSpawnYaw(n),q.lib.thirdPersonSpawnPitch(n)];});await look(...angles);await page.waitForTimeout(1800);
 };
 const leave=async()=>{await page.keyboard.press('Escape');await region.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await page.emulateMedia({reducedMotion:'reduce'});await region.getByRole('button',{name:/Back to Universe/}).click();await expect(scene).toHaveAttribute('data-state','overview-paused');await page.waitForTimeout(100);};
 const move=async(key,ms)=>{await page.evaluate(key=>window.__audit.keys=[key],key);await page.keyboard.down(key);await page.waitForTimeout(ms);await page.keyboard.up(key);await page.evaluate(()=>window.__audit.keys=[]);};
 const segment=async(name,action)=>{await page.evaluate(name=>{const q=window.__audit;q.active=true;q.frames=[];q.index=0;q.worst=null;q.matchedWorst=null;q.phase=name;},name);await action();
  const raw=await page.evaluate(()=>{const q=window.__audit;q.active=false;return{frames:q.frames,worst:q.worst,matchedWorst:q.matchedWorst,navigation:q.controller.player.navigation};});
  if(raw.worst){fs.writeFileSync(path.join(__dirname,name+'-worst.png'),Buffer.from(raw.worst.png.split(',')[1],'base64'));delete raw.worst.png;}
  if(raw.matchedWorst){fs.writeFileSync(path.join(__dirname,name+'-matched-worst.png'),Buffer.from(raw.matchedWorst.png.split(',')[1],'base64'));delete raw.matchedWorst.png;}
  report.runs.push({name,...raw});save();console.log(name,raw.frames.length,'frames, max crop',Math.max(...raw.frames.map(f=>f.meshCrop??0)).toFixed(2));
 };
 if(targeted){
  await enter('Latest Builds');
  await segment('latest-crossbar-turns',async()=>{await move('KeyS',950);await page.waitForTimeout(1500);for(const key of ['KeyA','KeyD','KeyD','KeyA','KeyW','KeyS']){await move(key,220);await page.waitForTimeout(150);}await page.waitForTimeout(1800);});
  await leave();await enter('Latest Builds');await move('KeyS',950);await page.waitForTimeout(1500);
  await segment('latest-blocked-and-exit',async()=>{await move('KeyS',3000);await page.waitForTimeout(1500);await move('KeyW',2000);await page.waitForTimeout(2200);});
  await leave();report.completed=true;save();return;
 }
 await enter('Latest Builds');
 await segment('latest-normal',async()=>{await page.waitForTimeout(600);for(const key of ['KeyW','KeyS','KeyA','KeyD']){await move(key,250);await page.waitForTimeout(500);}});
 await leave();await enter('Latest Builds');
 await segment('latest-crossbar',async()=>{await move('KeyS',950);await page.waitForTimeout(1500);await move('KeyW',1000);await page.waitForTimeout(2500);});
 await page.screenshot({path:path.join(__dirname,'latest-crossbar-after-stop.png')});
 await segment('latest-directions',async()=>{for(const key of ['KeyS','KeyA','KeyD','KeyW']){await move(key,350);await page.waitForTimeout(600);}await page.waitForTimeout(1500);});
 await leave();await enter('Latest Builds');await move('KeyS',950);await page.waitForTimeout(1500);
 await segment('latest-collision-hold',async()=>{await move('KeyW',3000);await page.waitForTimeout(3500);});
 await leave();await enter('Tools');
 await segment('tools-entry-normal',async()=>{await page.waitForTimeout(600);for(const key of ['KeyW','KeyS','KeyA','KeyD']){await move(key,300);await page.waitForTimeout(400);}});
 await leave();await enter('Tools');await look(0,-.52);
 await segment('tools-bench',async()=>{await move('KeyS',1600);await page.waitForTimeout(1500);for(const key of ['KeyA','KeyD','KeyW','KeyS']){await move(key,300);await page.waitForTimeout(300);}await page.waitForTimeout(1500);});
 await leave();report.completed=true;save();
 }catch(e){report.failure=String(e);save();throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
