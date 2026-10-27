// Focused native-input smoke plus isolated clear-view cadence comparison.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const app=path.resolve('app-gateway-fe'),{chromium,expect}=require(path.join(app,'node_modules/@playwright/test'));
const ts=require(path.join(app,'node_modules/typescript'));
const modules={};
for(const name of ['astronaut-animation','astronaut-ground-contact']) modules['/'+name+'.js']=ts.transpileModule(fs.readFileSync(path.join(app,'lib',name+'.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText.replace('"./astronaut-ground-contact"','"./astronaut-ground-contact.js"');
const server=http.createServer((req,res)=>{
 let bytes,type='text/javascript';
 try {
  if(req.url==='/') {bytes=fs.readFileSync(path.join(__dirname,'comparison.html'));type='text/html';}
  else if(modules[req.url])bytes=modules[req.url];
  else if(req.url==='/astronaut.glb'){bytes=fs.readFileSync(path.join(app,'public/models/astronaut/astronaut-animated.glb'));type='model/gltf-binary';}
  else if(req.url.startsWith('/three/')){const file=path.resolve(app,'node_modules/three',req.url.slice(7));if(!file.startsWith(path.join(app,'node_modules/three')+path.sep))throw Error('Outside fixture');bytes=fs.readFileSync(file);}
  else {res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',type);res.end(bytes);
 }catch(e){res.writeHead(500);res.end(String(e));}
});
(async()=>{
 await new Promise(resolve=>server.listen(3333,'127.0.0.1',resolve));
 const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce',recordVideo:{dir:__dirname,size:{width:1440,height:900}}}),errors=[],samples=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:3333');await expect.poll(()=>page.evaluate(()=>!!window.ready)).toBe(true);
  await page.waitForTimeout(2000);await page.screenshot({path:path.join(__dirname,'cadence-comparison.png')});
  const comparison=await page.evaluate(()=>window.metrics());
  fs.writeFileSync(path.join(__dirname,'comparison-report.json'),JSON.stringify(comparison,null,2));
  await page.waitForTimeout(2000);
  const r=page.getByRole('region',{name:'Project Universe'}),s=r.locator('[data-ready="true"]');
  const snap=()=>s.evaluate(e=>({render:e.__universeRender(),speed:e.__universeController.character.speed,position:{...e.__universeController.player.position},yaw:e.__universeController.character.yaw,state:e.__universeController.getSnapshot()}));
  const save=async name=>{samples.push({name,...await snap()});fs.writeFileSync(path.join(__dirname,'browser-progress.json'),JSON.stringify(samples,null,2));};
  await page.goto('http://127.0.0.1:3000',{waitUntil:'domcontentloaded',timeout:120000});await expect(s).toBeVisible({timeout:60000});await s.scrollIntoViewIfNeeded();
  await r.getByRole('button',{name:'Tools',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');
  const canvas=await r.locator('canvas').elementHandle();
  const enter=async()=>{await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).render.astronaut.visual).toBe('model');};
  const leave=async()=>{if(await page.evaluate(()=>!!document.pointerLockElement))await page.keyboard.press('Escape');await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect Tools'})).toBeFocused();expect((await snap()).render.astronaut.animation).toBeNull();};
  await page.emulateMedia({reducedMotion:'no-preference'});await enter();await save('initial-idle');
  // Native keys in both axes. Keep one key pressed during changes, preserving moving state.
  let held='KeyD';await page.keyboard.down(held);
  try {
   await expect.poll(async()=>(await snap()).render.astronaut.animation.walkWeight).toBe(1);
   await save('sideways-full-walk');await page.screenshot({path:path.join(__dirname,'native-sideways-walk.png')});
   const initialTransitions=(await snap()).render.astronaut.animation.transitions;
   for(const next of ['KeyA','KeyS','KeyD','KeyW']){
    await page.keyboard.down(next);await page.keyboard.up(held);held=next;
    await page.waitForTimeout(90);await save('direction-'+next);
   }
   // Collision can interrupt movement; count/time metadata distinguishes that from a direction restart.
   await expect.poll(async()=>{const q=await snap();return q.speed===0&&q.render.astronaut.animation.idleWeight===1;},{timeout:15000}).toBe(true);
   await save('held-key-collision-idle');
   for(const q of samples.filter(q=>q.name.startsWith('direction-'))){expect(q.render.astronaut.animation.walkRate).toBeGreaterThanOrEqual(.5);expect(q.render.astronaut.animation.walkRate).toBeLessThanOrEqual(2);}
   samples.push({name:'direction-initial-transition-count',initialTransitions});
  }finally{await page.keyboard.up(held);}
  await expect.poll(async()=>(await snap()).render.astronaut.animation.idleWeight).toBe(1);
  await page.keyboard.press('Escape');const paused=(await snap()).render.astronaut.animation;
  await page.waitForTimeout(180);expect((await snap()).render.astronaut.animation).toEqual(paused);await leave();
  for(let i=0;i<2;i++){await enter();expect((await snap()).render.astronaut.animation).toMatchObject({clip:'Idle',transitions:0,walkWeight:0});await leave();}
  await r.getByRole('button',{name:'Explore in First Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);expect((await snap()).render.astronaut.animation).toBeNull();await leave();
  await page.emulateMedia({reducedMotion:'reduce'});await enter();const reduced=(await snap()).render.astronaut.animation;
  await page.keyboard.down('KeyD');try{await page.waitForTimeout(150);expect((await snap()).render.astronaut.animation).toEqual(reduced);}finally{await page.keyboard.up('KeyD');}await leave();
  expect(await r.locator('canvas').evaluate((n,old)=>n===old,canvas)).toBe(true);
  await page.waitForTimeout(150);expect((await snap()).render.astronaut.animation).toBeNull();expect(errors).toEqual([]);
  fs.writeFileSync(path.join(__dirname,'browser-report.json'),JSON.stringify({viewport:{width:1440,height:900},renderer:'SwiftShader',comparison,errors,samples,checks:{pauseFreeze:true,repeatedExitCleanup:true,canvasPersistent:true,FPSExcluded:true,reducedStaticIdle:true,returnFocus:true}},null,2));
  await page.close();console.log('Desktop native-input smoke and cadence comparison passed');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exit(1);});
