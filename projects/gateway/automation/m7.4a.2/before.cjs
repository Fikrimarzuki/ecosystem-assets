const fs=require('node:fs'),path=require('node:path');
const {chromium,expect}=require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false});
 const report={browserVersion:browser.version(),captures:[],checks:{},errors:[]},save=()=>fs.writeFileSync(path.join(__dirname,'before-report.json'),JSON.stringify(report,null,2));
 try {
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>report.errors.push(e.message));
  const r=page.getByRole('region',{name:'Project Universe'}),s=r.locator('[data-ready="true"]');await page.goto('http://127.0.0.1:3001');await expect(s).toBeVisible({timeout:60000});await s.scrollIntoViewIfNeeded();
    await r.locator('canvas').evaluate(canvas=>{
   let fiber=canvas[Object.keys(canvas).find(k=>k.startsWith('__reactFiber'))],state;
   for(let f=fiber;f&&!state;f=f.return)for(let h=f.memoizedState;h;h=h.next){const v=h.memoizedState?.current;if(v?.gl&&v?.scene&&v?.internal?.subscribers){state=v;break;}}
   if(!state)throw Error('R3F state inspection unavailable');
   const q=window.__qa={state,controller:canvas.closest('[data-ready]').__universeController,active:false,values:{},renders:[],raf:[],stamps:[],cameraPositions:[],wrappers:new WeakMap()};
   const timed=(object,key,label)=>{if(!object?.[key]||q.wrappers.get(object)?.get(key)===object[key])return;const orig=object[key];let set=q.wrappers.get(object);if(!set)q.wrappers.set(object,set=new Map());object[key]=function(...args){const t=performance.now();try{return orig.apply(this,args);}finally{if(q.active)(q.values[label]??=[]).push(performance.now()-t);}};set.set(key,object[key]);};
   q.refresh=()=>{
    for(const sub of state.internal.subscribers)timed(sub.ref,'current','frame-priority-'+sub.priority);
    const rig=state.scene.getObjectByName('exploration-astronaut'),a=rig?.userData.astronautAnimation;
    timed(a,'update','animation-update');timed(a?.mixer,'update','mixer-update');timed(a?.ground,'lift','ground-lift');
   };
   const render=state.gl.render;state.gl.render=function(...args){if(q.active){q.renders.push(performance.now());q.cameraPositions.push(state.camera.position.toArray());const a=state.scene.getObjectByName('exploration-astronaut')?.userData.astronautAnimation;if(a&&q.animationFrames)q.animationFrames.push(a.snapshot());if(q.motionFrames)q.motionFrames.push({speed:q.controller.character.speed,player:{...q.controller.player.position},clip:a?.snapshot().clip,weight:a?.snapshot().walkWeight});}return render.apply(this,args);};
   q.resources=()=>({geometries:state.gl.info.memory.geometries,textures:state.gl.info.memory.textures,programs:state.gl.info.programs?.length,
     subscribers:state.internal.subscribers.length,activeAnimation:!!state.scene.getObjectByName('exploration-astronaut')?.userData.astronautAnimation,
     skinnedMeshes:state.scene.getObjectsByProperty('isSkinnedMesh',true).length,frameloop:state.get().frameloop,heap:performance.memory?.usedJSHeapSize});
   q.hardware=(()=>{const gl=state.gl.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return{userAgent:navigator.userAgent,cores:navigator.hardwareConcurrency,deviceMemoryGB:navigator.deviceMemory,devicePixelRatio:devicePixelRatio,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),vendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):gl.getParameter(gl.VENDOR),webgl:gl.getParameter(gl.VERSION)};})();
  });

  const snap=()=>s.evaluate(e=>({...e.__universeRender(true),state:e.__universeController.getSnapshot(),player:{...e.__universeController.player.position,yaw:e.__universeController.player.yaw,pitch:e.__universeController.player.pitch},navigation:e.__universeController.player.navigation}));
  let entryCamera;
  const enter=async name=>{await r.getByRole('button',{name,exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});entryCamera=(await snap()).camera;await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).astronaut.visual,{timeout:30000}).toBe('model');await page.waitForTimeout(1500);};
  const leave=async name=>{await page.keyboard.press('Escape');await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect '+name})).toBeFocused();await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-entryCamera[i])))).toBeLessThan(1e-6);await r.getByRole('button',{name:/Back to Universe/}).click();await page.emulateMedia({reducedMotion:'reduce'});};
  const capture=async name=>{
   const projection=await page.evaluate(()=>{
    const q=window.__qa,mesh=q.state.scene.getObjectByName('astronaut-model-placement').getObjectsByProperty('isSkinnedMesh',true)[0],camera=q.state.camera;
    q.state.scene.updateMatrixWorld(true);mesh.skeleton.update();camera.updateMatrixWorld(true);const point=camera.position.clone(),range={minX:Infinity,maxX:-Infinity,minY:Infinity,maxY:-Infinity},boots={minY:Infinity,maxY:-Infinity,count:0};
    const feet=new Set(mesh.skeleton.bones.map((bone,i)=>/foot|toebase/i.test(bone.name)?i:-1).filter(i=>i>=0));
    const attrs=mesh.geometry.attributes;
    for(let i=0;i<attrs.position.count;i++){
     mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld).project(camera);
     range.minX=Math.min(range.minX,point.x);range.maxX=Math.max(range.maxX,point.x);range.minY=Math.min(range.minY,point.y);range.maxY=Math.max(range.maxY,point.y);
     let footWeight=0;for(const getter of ['getX','getY','getZ','getW'])if(feet.has(attrs.skinIndex[getter](i)))footWeight+=attrs.skinWeight[getter](i);
     if(footWeight>.5){boots.count++;boots.minY=Math.min(boots.minY,point.y);boots.maxY=Math.max(boots.maxY,point.y);}
    }
    const gl=q.state.gl.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return{range,boots,renderer:gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)};
   });
   report.captures.push({name,projection,snapshot:await snap()});save();await page.screenshot({path:path.join(__dirname,name+'.png')});return projection;
  };
  for(let visit=1;visit<=2;visit++){
   await enter('Latest Builds');
   await page.keyboard.down('KeyS');await page.waitForTimeout(950);await page.keyboard.up('KeyS');await page.waitForTimeout(50);
   await capture('before-latest-same-position-'+visit+'-initial');
   await page.waitForTimeout(1500);await capture('before-latest-same-position-'+visit+'-settled');
   await leave('Latest Builds');
  }
  report.checks.samePositionTwoVisits=true;save(); }catch(error){report.failure=String(error);save();throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});



