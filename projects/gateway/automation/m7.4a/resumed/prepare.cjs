const fs=require('node:fs'),path=require('node:path');
let script=fs.readFileSync(path.join(__dirname,'../performance-template.cjs'),'utf8');
const replace=(from,to)=>{if(!script.includes(from))throw Error('Missing diagnostic marker: '+from.slice(0,70));script=script.replace(from,to);};
replace("const phase = process.argv[2], out = __dirname;", "const phase = 'continuation', out = __dirname;");
replace("report.hardware=await page.evaluate(()=>window.__qa.hardware);\n  if (/swiftshader|llvmpipe|software|basic render/i.test(report.hardware.renderer)) throw Error('Hardware GPU unavailable on Gateway Canvas');\n  report.gpu=(await (await browser.newBrowserCDPSession()).send('SystemInfo.getInfo')).gpu;", "// Renderer verification is performed once after native TPS entry below.");
replace("await page.waitForTimeout(5000);await measure(phase+'-overview');", "await page.waitForTimeout(5000); console.log('Warmed route; prior overview measurements reused.');");
replace("[['KeyS',650],['KeyW',650],['KeyA',350],['KeyD',350]]", "[['KeyS',450],['KeyW',450],['KeyA',250],['KeyD',250]]");
replace("report.samples.push(sample);save();console.log", "sample.movingFraction=sample.renders?sample.movingFrames/sample.renders:0;report.samples.push(sample);save();if(drive && sample.movingFraction<.8)throw Error('Diagnostic route did not sustain movement; retain sample as mixed/blocked, not active walking');console.log");
replace("await page.waitForTimeout(2000);};", `await page.waitForTimeout(2000);
   if(!report.hardware){report.hardware=await page.evaluate(()=>{const q=window.__qa,gl=q.state.gl.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {...q.hardware,renderer:gl.getParameter(ext.UNMASKED_RENDERER_WEBGL),activeTPS:q.controller.getSnapshot().explorationMode};});if(/swiftshader|llvmpipe|software|basic render/i.test(report.hardware.renderer))throw Error('Physical GPU absent in active TPS');report.gpu=(await(await browser.newBrowserCDPSession()).send('SystemInfo.getInfo')).gpu;save();console.log('Active TPS GPU: '+report.hardware.renderer);}
  };`);
replace("await arrive('Tools');await enter();await capture('tools-entry');", `await arrive('Tools');await enter();
  await page.evaluate(()=>{const q=window.__qa,prior=q.resources;q.resources=()=>{const base=prior(),roots=q.state.scene.getObjectsByProperty('name','exploration-astronaut');return {...base,astronautRoots:roots.length,mixerCount:new Set(roots.map(r=>r.userData.astronautAnimation?.mixer).filter(Boolean)).size};};});
  await capture('tools-entry');`);
replace("await key('KeyS',650);await capture('tools-bench-side');", `// Use native mouse look to align with the verified bench-side route, never reposition the player.
  await page.mouse.move(720,450);const heading=(await snap()).player.yaw;await page.mouse.move(720+heading/.0025,450);
  await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.58);await capture('tools-bench-side');}finally{await page.keyboard.up('KeyS');}`);
replace("await capture('tools-blocked-idle');report.checks.blockedIdle=true;", "await capture('tools-blocked-idle');expect((await snap()).player.x).toBeLessThan(.05701);report.checks.blockedIdle=true;");
replace("report.checks.fiveEntriesExitCleanup=report.cycles.every(c=>!c.after.activeAnimation && c.after.skinnedMeshes===0);", `report.checks.fiveEntriesExitCleanup=report.cycles.every(c=>!c.after.activeAnimation && c.after.skinnedMeshes===0 && c.after.mixerCount===0 && c.active.mixerCount===1 && c.active.skinnedMeshes===1);
  expect(report.checks.fiveEntriesExitCleanup).toBe(true);const signature=v=>[v.geometries,v.textures,v.programs].join('/');expect(new Set(report.cycles.map(c=>signature(c.after))).size).toBe(1);
  await page.waitForTimeout(500);await measure('settled-showcase-after-exit',2500);expect(report.samples.at(-1).renders).toBe(0);report.checks.settledNoRendering=true;`);
const throttleStart=script.indexOf('  // CPU-throttled native start/stop');
const throttleEnd=script.indexOf("  await leave('Latest Builds');report.checks",throttleStart);
if(throttleStart<0||throttleEnd<0)throw Error('Throttle block markers missing');
script=script.slice(0,throttleStart)+script.slice(throttleEnd);
replace("report.requests=requests;\n  save();expect(report.errors).toEqual([]);", `
  // FPS uses the same session owner but must have no mounted astronaut/mixer.
  await r.getByRole('button',{name:'Explore in First Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await page.waitForTimeout(250);expect((await snap()).astronaut.visible).toBe(false);expect((await snap()).astronaut.animation).toBeNull();expect((await page.evaluate(()=>window.__qa.resources())).mixerCount).toBe(0);
  const fpsBefore=(await snap()).player;await key('KeyS',200);const fpsAfter=(await snap()).player;expect(Math.hypot(fpsAfter.x-fpsBefore.x,fpsAfter.z-fpsBefore.z)).toBeGreaterThan(.01);await leave('Latest Builds');report.checks.fpsExclusion=true;
  await page.emulateMedia({reducedMotion:'reduce'});entryCamera=(await snap()).camera;await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).astronaut.animation?.idleTime).toBe(0);await page.waitForTimeout(500);await measure('reduced-static-tps',2500);expect(report.samples.at(-1).renders).toBe(0);const reduced=(await snap()).astronaut.animation,from=(await snap()).player;await key('KeyS',200);const to=(await snap()).player;expect(Math.hypot(to.x-from.x,to.z-from.z)).toBeGreaterThan(.01);expect((await snap()).astronaut.animation).toEqual(reduced);await leave('Latest Builds');report.checks.reducedStaticAndFunctionalMovement=true;
  await back();await page.getByRole('link',{name:'About & Experience',exact:true}).click();await expect.poll(async()=>(await snap()).state.visible).toBe(false);await page.waitForTimeout(500);await measure('portfolio-offscreen-after-tps',2500);expect(report.samples.at(-1).renders).toBe(0);expect((await page.evaluate(()=>window.__qa.resources())).mixerCount).toBe(0);report.checks.navigationOffscreenCleanup=true;
  const featured=page.getByRole('region',{name:'Selected builds'});await featured.getByRole('button',{name:'Playdeck: View Details'}).click();await expect(page.locator('#portfolio-project-details').getByRole('heading',{name:'Playdeck',exact:true})).toBeFocused();await page.keyboard.press('Escape');report.checks.independentPortfolioDetails=true;
  report.requests=requests;expect(requests).toHaveLength(1);save();expect(report.errors).toEqual([]);`);
const prior=fs.readFileSync(path.join(__dirname,'../../m7.3d/browser-qa.cjs'),'utf8');
const start=prior.indexOf("  await r.locator('canvas').evaluate(canvas=>{"),end=prior.indexOf('  report.hardware=',start);
if(start<0||end<0)throw Error('Prior probe markers missing');
replace('// INJECT_EXISTING_DIAGNOSTIC',prior.slice(start,end));
fs.writeFileSync(path.join(__dirname,'performance-qa.cjs'),script);
console.log('Prepared diagnostic continuation; overview windows omitted.');
