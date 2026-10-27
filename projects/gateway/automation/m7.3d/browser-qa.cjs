const fs = require('node:fs'), path = require('node:path');
const {chromium,expect} = require(path.resolve('app-gateway-fe/node_modules/@playwright/test'));
const phase = process.argv[2] || 'disabled', out = __dirname;const resume=!!process.env.QA_RESUME;const fallbackOnly=process.env.QA_RESUME==='fallback';
const summarize = values => {
  const sorted = values.slice().sort((a,b)=>a-b), n=sorted.length;
  return {count:n,mean:n?values.reduce((a,b)=>a+b,0)/n:null,p50:n?sorted[Math.floor((n-1)*.5)]:null,p95:n?sorted[Math.floor((n-1)*.95)]:null,max:n?sorted[n-1]:null};
};
(async()=>{
 const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const checksOnly=process.env.QA_CHECKS_ONLY==='true';
 const report=checksOnly?JSON.parse(fs.readFileSync(path.join(out,phase+'-browser-report.json'),'utf8')):{phase,samples:[],captures:[],checks:{},errors:[]};delete report.failure;
 const save=()=>fs.writeFileSync(path.join(out,phase+'-browser-report.json'),JSON.stringify(report,null,2));
 try{
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'no-preference'});
  page.on('pageerror',e=>{report.errors.push(e.message);save();});
  const requests=[];page.on('request',r=>{if(r.url().includes('/models/astronaut/'))requests.push(r.url());});
  const r=page.getByRole('region',{name:'Project Universe'}),s=r.locator('[data-ready="true"]');
  await page.goto('http://127.0.0.1:'+(phase==='disabled'?3001:3000),{waitUntil:'domcontentloaded',timeout:180000});
  await expect(s).toBeVisible({timeout:60000});await s.scrollIntoViewIfNeeded();
  const canvas=await r.locator('canvas').elementHandle();
  const snap=(ground=false)=>s.evaluate((e,g)=>{const c=e.__universeController;return{...e.__universeRender(g),state:c.getSnapshot(),playerActive:c.player.active,speed:c.character.speed,yaw:c.character.yaw,player:{...c.player.position,yaw:c.player.yaw,pitch:c.player.pitch}};},ground);
  // Inspect the installed R3F Canvas hook ref in this browser only. No app files
  // or frame ordering change. Wrap existing callbacks; never add scene frames.
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
  report.hardware=await page.evaluate(()=>window.__qa.hardware);save();
  const measure=async(name,duration=2500)=>{
   const raw=await page.evaluate(async({duration})=>{const q=window.__qa;q.refresh();q.values={};q.renders=[];q.raf=[];q.cameraPositions=[];q.animationFrames=[];q.motionFrames=[];const start=performance.now(),before=q.resources();let prev;let id;function tick(t){q.refresh();if(prev!==undefined)q.raf.push(t-prev);prev=t;id=requestAnimationFrame(tick);}id=requestAnimationFrame(tick);q.active=true;await new Promise(r=>setTimeout(r,duration));q.active=false;cancelAnimationFrame(id);return{elapsed:performance.now()-start,before,after:q.resources(),values:q.values,renderTimes:q.renders,raf:q.raf,cameraPositions:q.cameraPositions,animationFrames:q.animationFrames,motionFrames:q.motionFrames};},{duration});
   const intervals=raw.renderTimes.slice(1).map((v,i)=>v-raw.renderTimes[i]);
   const cost={};for(const [label,values]of Object.entries(raw.values))cost[label]=summarize(values);
   let maxCameraStep=0;for(let i=1;i<raw.cameraPositions.length;i++)maxCameraStep=Math.max(maxCameraStep,Math.hypot(...raw.cameraPositions[i].map((v,a)=>v-raw.cameraPositions[i-1][a])));
   const sample={name,elapsedMs:raw.elapsed,renders:raw.renderTimes.length,renderIntervalsMs:summarize(intervals),browserRAFIntervalsMs:summarize(raw.raf),callbacksMs:cost,maxCameraStepWorldUnits:maxCameraStep,animationFrames:raw.animationFrames,motionFrames:raw.motionFrames,before:raw.before,after:raw.after,snapshot:await snap()};
   report.samples.push(sample);save();console.log('Measured '+name+' renders='+sample.renders);
  };
  const capture=async(name)=>{const at=await snap(true);report.captures.push({name,...at});save();await page.screenshot({path:path.join(out,name+'.png')});};
  if(!checksOnly&&!resume)await measure(phase+'-overview');
  if(phase==='disabled'){
   await page.emulateMedia({reducedMotion:'reduce'});await r.getByRole('button',{name:'Tools',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');
   await expect(r.getByRole('button',{name:'Explore in Third Person'})).toHaveCount(0);await expect(r.getByRole('button',{name:'Explore in First Person'})).toHaveCount(0);
   expect(requests).toHaveLength(0);expect((await snap()).astronaut.animation).toBeNull();
   if(!checksOnly)await measure('disabled-showcase-reduced');
   const featured=page.getByRole('region',{name:'Selected builds'});await featured.getByRole('button',{name:'Playdeck: View Details'}).click();await expect(page.locator('#portfolio-project-details')).toBeVisible();await expect(page.locator('#portfolio-project-details').getByRole('heading',{name:'Playdeck',exact:true})).toBeFocused();await page.keyboard.press('Escape');
   report.checks={defaultNoWalking:true,noModelRequests:true,noBackgroundMixer:true,independentPortfolioDetails:true};report.requests=requests;save();return;
  }
  await page.emulateMedia({reducedMotion:'reduce'});await r.getByRole('button',{name:'Tools',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});
  if(!resume)await measure('enabled-inactive-showcase');expect(requests).toHaveLength(0);
  let entryCamera;const enter=async(mode='Third')=>{await page.waitForTimeout(200);entryCamera=(await snap()).camera;await r.getByRole('button',{name:'Explore in '+mode+' Person'}).click();await expect.poll(async()=>(await snap()).state.firstPersonLocked).toBe(true);await expect.poll(()=>page.evaluate(()=>document.activeElement===document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).playerActive).toBe(true);if(mode==='Third'){await expect.poll(async()=>(await snap()).astronaut.visual,{timeout:30000}).toBe('model');await expect.poll(async()=>(await snap()).astronaut.animation.time).toBeGreaterThan(.05);}};
  const leave=async(world)=>{if(await page.evaluate(()=>!!document.pointerLockElement))await page.keyboard.press('Escape');await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect '+world})).toBeFocused();expect((await snap()).astronaut.animation).toBeNull();await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-entryCamera[i]))),{timeout:15000}).toBeLessThan(1e-6);};
  const back=async()=>{await r.getByRole('button',{name:/Back to Universe/}).click();await expect(s).toHaveAttribute('data-state',/^overview/);};
  const resetTools=async()=>{await leave('Tools');await back();await page.emulateMedia({reducedMotion:'reduce'});await r.getByRole('button',{name:'Tools',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});};
  if(phase==='motion-profile'){
   const drive=async schedule=>{for(const [key,ms] of schedule){await page.keyboard.down(key);await page.waitForTimeout(ms);await page.keyboard.up(key);}};
   await enter();let perf=measure('tools-verified-moving',2300);await drive([['KeyS',450],['KeyW',450],['KeyD',300],['KeyA',300]]);await perf;await leave('Tools');await back();
   await page.emulateMedia({reducedMotion:'reduce'});await r.getByRole('button',{name:'Latest Builds',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});await enter();
   perf=measure('latest-verified-road-moving',2300);await drive([['KeyS',700],['KeyW',700]]);await perf;await leave('Latest Builds');
   report.checks={nativeVerifiedMovingSamples:true,returnCameraFocus:true};report.requests=requests;save();return;
  }
  if(phase==='transitions'){
   await enter();const perf=measure('start-stop-blended-cpu',2000);
   await page.keyboard.down('KeyS');await page.waitForTimeout(300);await page.keyboard.up('KeyS');await page.waitForTimeout(300);
   await page.keyboard.down('KeyD');await page.waitForTimeout(300);await page.keyboard.up('KeyD');await perf;
   await expect.poll(async()=>(await snap()).astronaut.animation.idleWeight).toBe(1);await capture('transition-final-idle');await leave('Tools');
   report.checks={twoDirectionStartStopFades:true,returnCameraFocus:true};report.requests=requests;save();return;
  }
  if(!resume){
  const toolsCamera=(await snap()).camera;await enter();await capture('tools-entry');await measure('active-tps-idle');
  // S follows the normal clear route; sample while actually moving, then stop.
  await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).astronaut.animation.walkWeight).toBe(1);await capture('clear-view-walking');await measure('active-tps-moving',650);await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.58);await capture('tools-bench-side-walking');}finally{await page.keyboard.up('KeyS');}
  await capture('idle-walk-transition');await expect.poll(async()=>(await snap()).astronaut.animation.idleWeight).toBe(1);
  await resetTools();await enter();await page.mouse.move(720,450);const angle=await snap();await page.mouse.move(720+angle.player.yaw/.0025,450);await expect.poll(async()=>(await snap()).player.yaw).toBeCloseTo(0,2);
  await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.58);}finally{await page.keyboard.up('KeyS');}
  await page.keyboard.down('KeyD');try{await expect.poll(async()=>(await snap()).player.x).toBeGreaterThan(.045);await expect.poll(async()=>{const q=await snap();return q.speed<.001&&q.astronaut.animation.idleWeight===1;}).toBe(true);await capture('tools-bench-stop');await measure('tools-obstacle-held-idle');}finally{await page.keyboard.up('KeyD');}
  expect((await snap()).player.x).toBeLessThan(.05701);
  // Pause/Resume and partial fade freeze use existing controls and native focus.
  await page.keyboard.press('Escape');await expect(r.getByRole('button',{name:'Resume exploration'})).toBeFocused();const paused=await snap();await measure('paused-tps');expect((await snap()).astronaut.animation).toEqual(paused.astronaut.animation);expect((await snap()).camera).toEqual(paused.camera);
  await r.getByRole('button',{name:'Resume exploration'}).click();await expect.poll(async()=>(await snap()).state.firstPersonLocked).toBe(true);await resetTools();
  await enter();await page.keyboard.down('KeyW');try{await expect(r.getByRole('status').filter({hasText:'Press E or Click to explore'})).toBeVisible();}finally{await page.keyboard.up('KeyW');}
  await capture('tools-road-traversal');await page.keyboard.press('KeyE');await expect(r.getByRole('article',{name:'CareerLens project details'})).toBeVisible();const details=await snap();await page.waitForTimeout(200);expect((await snap()).camera).toEqual(details.camera);expect((await snap()).astronaut.animation).toEqual(details.astronaut.animation);await page.keyboard.press('Escape');await leave('Tools');
  } else if(!fallbackOnly){await enter();await measure('tools-active-cpu-check',1800);await leave('Tools');}
  if(!fallbackOnly){
  const settledResource=await page.evaluate(()=>window.__qa.resources());
  const cycles=[];for(let i=0;i<3;i++){await enter();cycles.push(await page.evaluate(()=>window.__qa.resources()));await leave('Tools');cycles.push(await page.evaluate(()=>window.__qa.resources()));}
  report.resources={settledResource,cycles};expect(requests).toHaveLength(1);expect(cycles.filter((_,i)=>i%2===1).every(v=>!v.activeAnimation)).toBe(true);
  }
  await enter('First');expect((await snap()).astronaut.visible).toBe(false);expect((await snap()).astronaut.animation).toBeNull();const fpsPosition=(await snap()).player;await page.keyboard.down('KeyS');try{await expect.poll(async()=>{const p=(await snap()).player;return Math.hypot(p.x-fpsPosition.x,p.z-fpsPosition.z);}).toBeGreaterThan(.015);}finally{await page.keyboard.up('KeyS');}await leave('Tools');
  await page.emulateMedia({reducedMotion:'reduce'});entryCamera=(await snap()).camera;await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(async()=>(await snap()).state.firstPersonLocked).toBe(true);await expect.poll(async()=>(await snap()).playerActive).toBe(true);await expect.poll(async()=>(await snap()).astronaut.animation?.idleTime).toBe(0);await measure('reduced-tps-static');const reduced=(await snap()).astronaut.animation;await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.4);}finally{await page.keyboard.up('KeyS');}expect((await snap()).astronaut.animation).toEqual(reduced);await leave('Tools');
  await back();await r.getByRole('button',{name:'Latest Builds',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');const latestCamera=(await snap()).camera;await page.emulateMedia({reducedMotion:'no-preference'});await enter();await capture('latest-entry');
  await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.55);await capture('latest-road-edge');await measure('latest-road-moving',500);await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.72);await capture('latest-crossbar-traversal');}finally{await page.keyboard.up('KeyS');}
  await page.keyboard.down('KeyD');try{await page.waitForTimeout(150);}finally{await page.keyboard.up('KeyD');}await expect.poll(async()=>(await snap()).astronaut.animation.idleWeight).toBe(1);await measure('latest-obstacle-near-idle');await leave('Latest Builds');
  await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-latestCamera[i])))).toBeLessThan(1e-6);await back();
  expect(await r.locator('canvas').evaluate((n,old)=>n===old,canvas)).toBe(true);
  await page.getByRole('link',{name:'About & Experience',exact:true}).click();await expect.poll(async()=>(await snap()).state.visible).toBe(false);await measure('portfolio-offscreen-after-tps');
  expect((await snap()).astronaut.animation).toBeNull();
  await page.setViewportSize({width:390,height:700});await page.getByRole('link',{name:'Explore Universe',exact:true}).click();await expect(r.getByRole('button',{name:'Explore in Third Person'})).toHaveCount(0);await expect(r.locator('canvas')).toHaveCount(0);await page.screenshot({path:path.join(out,'mobile-fallback.png')});
  report.checks={integration:true,benchStop:!resume,projectDetails:!resume,pauseResumeFocus:!resume,returnCameraFocus:true,threeReentries:!fallbackOnly,fpsExclusion:true,reducedStatic:true,reducedFunctionalMovement:true,latestTraversal:true,persistentCanvas:true,offscreenNoMixer:true,mobileFallback:true};report.requests=requests;expect(report.errors).toEqual([]);save();
 }catch(e){report.failure=String(e);save();throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
