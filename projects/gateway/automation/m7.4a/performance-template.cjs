const fs = require('node:fs'), path = require('node:path');
const { chromium, expect } = require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
const phase = process.argv[2], out = __dirname;
const stats = values => { const sorted = [...values].sort((a,b)=>a-b); return { count: values.length, mean: values.length ? values.reduce((a,b)=>a+b,0)/values.length : null, p50: sorted[Math.floor(sorted.length*.5)] ?? null, p95: sorted[Math.floor(sorted.length*.95)] ?? null, p99: sorted[Math.floor(sorted.length*.99)] ?? null, max: sorted.at(-1) ?? null, over33ms: values.filter(v=>v>33.34).length, over50ms: values.filter(v=>v>50).length, over100ms: values.filter(v=>v>100).length }; };
(async()=>{
 const browser = await chromium.launch({ channel: 'chrome', headless: false });
 const report = { phase, timestamp: new Date().toISOString(), browserVersion: browser.version(), mode: 'Next development, real GPU, diagnostic wrappers enabled', samples: [], checks: {}, captures: [], errors: [] };
 const save=()=>fs.writeFileSync(path.join(out,phase+'-report.json'),JSON.stringify(report,null,2));
 try {
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'no-preference'});
  page.on('pageerror',e=>report.errors.push(e.message));
  const requests=[]; page.on('request',r=>{if(r.url().includes('/models/astronaut/')) requests.push(r.url());});
  const r=page.getByRole('region',{name:'Project Universe'}), s=r.locator('[data-ready="true"]');
  await page.goto('http://127.0.0.1:3001',{waitUntil:'domcontentloaded',timeout:120000});
  await expect(s).toBeVisible({timeout:60000}); await s.scrollIntoViewIfNeeded(); await page.bringToFront();
  // INJECT_EXISTING_DIAGNOSTIC
  report.hardware=await page.evaluate(()=>window.__qa.hardware);
  if (/swiftshader|llvmpipe|software|basic render/i.test(report.hardware.renderer)) throw Error('Hardware GPU unavailable on Gateway Canvas');
  report.gpu=(await (await browser.newBrowserCDPSession()).send('SystemInfo.getInfo')).gpu;
  const snap=(ground=false)=>s.evaluate((e,g)=>({ ...e.__universeRender(g), state:e.__universeController.getSnapshot(), speed:e.__universeController.character.speed, player:{...e.__universeController.player.position,yaw:e.__universeController.player.yaw,pitch:e.__universeController.player.pitch} }),ground);
  const measure=async(name,duration=30000,drive=false)=>{
    const run=page.evaluate(async duration=>{const q=window.__qa;q.values={};q.renders=[];q.raf=[];q.cameraPositions=[];q.animationFrames=[];q.motionFrames=[];q.refresh();const before=q.resources();let id,prev;const tick=t=>{q.refresh();if(prev!==undefined)q.raf.push(t-prev);prev=t;id=requestAnimationFrame(tick);};id=requestAnimationFrame(tick);const start=performance.now();q.active=true;await new Promise(r=>setTimeout(r,duration));q.active=false;cancelAnimationFrame(id);return {elapsedMs:performance.now()-start,renderTimes:q.renders,raf:q.raf,values:q.values,cameraPositions:q.cameraPositions,motionFrames:q.motionFrames,animationFrames:q.animationFrames,before,after:q.resources()};},duration);
    if (drive) {
      const deadline=Date.now()+duration-600;
      // Short, balanced native key segments keep a bounded route; per-frame speed verifies movement.
      while(Date.now()<deadline) for(const [key,ms] of [['KeyS',650],['KeyW',650],['KeyA',350],['KeyD',350]]) {
        if(Date.now()>=deadline) break;
        await page.keyboard.down(key);await page.waitForTimeout(Math.min(ms,Math.max(0,deadline-Date.now())));await page.keyboard.up(key);
      }
    }
    const raw=await run, intervals=raw.renderTimes.slice(1).map((t,i)=>t-raw.renderTimes[i]);
    const costs=Object.fromEntries(Object.entries(raw.values).map(([label,v])=>[label,stats(v)]));
    const sample={name,elapsedMs:raw.elapsedMs,renders:raw.renderTimes.length,averageFPS:raw.renderTimes.length*1000/raw.elapsedMs,sceneFrameMs:stats(intervals),browserRAFMs:stats(raw.raf),callbackMs:costs,before:raw.before,after:raw.after,movingFrames:raw.motionFrames.filter(f=>f.speed>.001).length,rootPositions:raw.motionFrames.map(f=>f.player),animationFrames:raw.animationFrames,maxCameraStep:raw.cameraPositions.slice(1).reduce((max,p,i)=>Math.max(max,Math.hypot(...p.map((v,j)=>v-raw.cameraPositions[i][j]))),0),final:await snap()};
    report.samples.push(sample);save();console.log(JSON.stringify({name,fps:sample.averageFPS,frame:sample.sceneFrameMs,movingFrames:sample.movingFrames,renders:sample.renders,costs}));
  };
  await page.waitForTimeout(5000);await measure(phase+'-overview');
  const capture=async name=>{report.captures.push({name,snapshot:await snap(true)});await page.screenshot({path:path.join(out,name+'.png')});save();};
  const arrive=async name=>{await page.emulateMedia({reducedMotion:'reduce'});await r.getByRole('button',{name,exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});};
  if(phase==='disabled') {
    await arrive('Tools');await expect(r.getByRole('button',{name:/Explore in (First|Third) Person/})).toHaveCount(0);
    report.checks.noWalkingControls=true;report.checks.noAssetRequest=requests.length===0;report.requests=requests;save();return;
  }
  const canvas=await r.locator('canvas').elementHandle();let entryCamera;
  const enter=async()=>{entryCamera=(await snap()).camera;await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement),{timeout:15000}).toBe(true);await expect.poll(async()=>(await snap()).astronaut.visual,{timeout:30000}).toBe('model');await expect.poll(async()=>(await snap()).astronaut.animation.time).toBeGreaterThan(.1);await page.waitForTimeout(2000);};
  const leave=async world=>{if(await page.evaluate(()=>!!document.pointerLockElement))await page.keyboard.press('Escape');await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect '+world})).toBeFocused();expect((await snap()).astronaut.animation).toBeNull();await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-entryCamera[i])))).toBeLessThan(1e-6);};
  const back=async()=>{await r.getByRole('button',{name:/Back to Universe/}).click();await expect(s).toHaveAttribute('data-state',/^overview/);};
  const key=async(code,ms)=>{await page.keyboard.down(code);try{await page.waitForTimeout(ms);}finally{await page.keyboard.up(code);}};
  await arrive('Tools');await enter();await capture('tools-entry');await measure('tools-idle-tps');await measure('tools-active-tps-walking',30000,true);
  await leave('Tools');await back();await arrive('Tools');await enter();
  await key('KeyS',650);await capture('tools-bench-side');
  await page.keyboard.down('KeyD');try { await expect.poll(async()=>{const p=await snap();return p.speed<.001&&p.astronaut.animation.idleWeight===1;},{timeout:5000}).toBe(true);await capture('tools-blocked-idle');report.checks.blockedIdle=true; } finally {await page.keyboard.up('KeyD');}
  await leave('Tools');await back();await arrive('Tools');await enter();
  await page.keyboard.down('KeyW');try{await expect(r.getByRole('status').filter({hasText:'Press E or Click to explore'})).toBeVisible({timeout:8000});}finally{await page.keyboard.up('KeyW');}
  await page.keyboard.press('KeyE');await expect(r.getByRole('article',{name:'CareerLens project details'})).toBeVisible();const detail=await snap();await page.waitForTimeout(300);expect((await snap()).camera).toEqual(detail.camera);expect((await snap()).astronaut.animation).toEqual(detail.astronaut.animation);await page.keyboard.press('Escape');report.checks.projectFocusFreeze=true;await leave('Tools');
  report.cycles=[];
  for(let i=0;i<5;i++){await enter();await key('KeyS',150);const active=await page.evaluate(()=>window.__qa.resources());await leave('Tools');await page.waitForTimeout(500);report.cycles.push({active,after:await page.evaluate(()=>window.__qa.resources())});save();}
  report.checks.fiveEntriesExitCleanup=report.cycles.every(c=>!c.after.activeAnimation && c.after.skinnedMeshes===0);
  await back();await arrive('Latest Builds');await enter();await capture('latest-entry');await measure('latest-active-tps-walking',30000,true);await leave('Latest Builds');await back();await arrive('Latest Builds');await enter();
  await key('KeyS',1000);await capture('latest-crossbar');await key('KeyD',250);await capture('latest-road');
  // CPU-throttled native start/stop is diagnostic only, not a low-end physical-device benchmark.
  const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:6});
  try {await measure('latest-cpu-throttled-transitions',10000,true);await capture('latest-throttled-transition');} finally {await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});}
  await leave('Latest Builds');report.checks.returnCameraAndFocus=true;report.checks.persistentCanvas=await r.locator('canvas').evaluate((node,old)=>node===old,canvas);report.requests=requests;
  save();expect(report.errors).toEqual([]);
 }catch(error){report.failure=String(error);save();throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
