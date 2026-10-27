const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const app=path.resolve('app-gateway-fe'),{chromium,expect}=require(path.join(app,'node_modules/@playwright/test'));
const server=http.createServer((req,res)=>{try{let file,type='text/javascript';if(req.url==='/'){file=path.join(__dirname,'clearance-comparison.html');type='text/html';}else if(['/baseline.json','/corrected.json'].includes(req.url)){file=path.join(__dirname,req.url.slice(1));type='application/json';}else if(req.url==='/astronaut.glb'){file=path.join(app,'public/models/astronaut/astronaut-animated.glb');type='model/gltf-binary';}else if(req.url.startsWith('/three/')){file=path.resolve(app,'node_modules/three',req.url.slice(7));if(!file.startsWith(path.join(app,'node_modules/three')+path.sep))throw Error('Outside fixture');}else{res.writeHead(404);res.end();return;}res.setHeader('Content-Type',type);res.end(fs.readFileSync(file));}catch(e){res.writeHead(500);res.end(String(e));}});
(async()=>{
 await new Promise(resolve=>server.listen(3333,'127.0.0.1',resolve));const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'}),errors=[],samples=[];
 page.on('pageerror',e=>errors.push(e.message));
 if(!process.env.GATEWAY_NATIVE_ONLY){await page.goto('http://127.0.0.1:3333');await expect.poll(()=>page.evaluate(()=>!!window.ready)).toBe(true);await page.screenshot({path:path.join(__dirname,'environment-before-after.png')});}
 const r=page.getByRole('region',{name:'Project Universe'}),s=r.locator('[data-ready="true"]');
 const snap=()=>s.evaluate(e=>{const c=e.__universeController;return{...e.__universeRender(),speed:c.character.speed,position:{...c.player.position},characterYaw:c.character.yaw,state:c.getSnapshot()};});
 const capture=async name=>{samples.push({name,...await snap()});fs.writeFileSync(path.join(__dirname,'browser-progress.json'),JSON.stringify(samples,null,2));await page.screenshot({path:path.join(__dirname,name+'.png')});};
 await page.goto('http://127.0.0.1:3000',{waitUntil:'domcontentloaded',timeout:120000});await expect(s).toBeVisible({timeout:60000});await s.scrollIntoViewIfNeeded();const canvas=await r.locator('canvas').elementHandle();
 const enter=async()=>{await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).astronaut.visual).toBe('model');};
 const leave=async name=>{if(await page.evaluate(()=>!!document.pointerLockElement))await page.keyboard.press('Escape');await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect '+name})).toBeFocused();};
 const start=async(name)=>{await r.getByRole('button',{name,exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');const camera=(await snap()).camera;await page.emulateMedia({reducedMotion:'no-preference'});await enter();return camera;};
 const toolsCamera=await start('Tools');await capture('tools-entry');
 await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).position.z).toBeGreaterThan(.63);await expect.poll(async()=>(await snap()).astronaut.animation.walkWeight).toBe(1);}finally{await page.keyboard.up('KeyS');}
 await page.waitForTimeout(200);await capture('tools-bench-side');
 await page.keyboard.down('KeyD');try{await expect.poll(async()=>(await snap()).speed).toBeGreaterThan(0);await expect.poll(async()=>{const q=await snap();return q.speed===0&&q.astronaut.animation.idleWeight===1;},{timeout:15000}).toBe(true);}finally{await page.keyboard.up('KeyD');}
 await capture('tools-bench-stop');await leave('Tools');await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-toolsCamera[i])))).toBeLessThan(1e-6);
 // Separate reset isolates project approach from the bench trajectory.
 await enter();await page.keyboard.down('KeyW');try{await expect(r.getByRole('status').filter({hasText:'Press E or Click to explore'})).toBeVisible({timeout:15000});}finally{await page.keyboard.up('KeyW');}
 await page.keyboard.press('KeyE');await expect(r.getByRole('article',{name:'CareerLens project details'})).toBeVisible();const frozen=(await snap()).camera;await page.waitForTimeout(150);expect((await snap()).camera).toEqual(frozen);await page.keyboard.press('Escape');await leave('Tools');
 await r.getByRole('button',{name:/Back to Universe/}).click();await expect(s).toHaveAttribute('data-state',/^overview/);await page.emulateMedia({reducedMotion:'reduce'});
 const latestCamera=await start('Latest Builds');await capture('latest-entry');
 await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).position.z).toBeGreaterThan(.6);await capture('latest-road-edge-walk');await expect.poll(async()=>(await snap()).position.z).toBeGreaterThan(.72);}finally{await page.keyboard.up('KeyS');}
 await page.waitForTimeout(200);await capture('latest-crossbar');
 await page.keyboard.down('KeyD');try{await page.waitForTimeout(120);}finally{await page.keyboard.up('KeyD');}await expect.poll(async()=>(await snap()).astronaut.animation.idleWeight).toBe(1);
 await leave('Latest Builds');await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-latestCamera[i])))).toBeLessThan(1e-6);
 expect(await r.locator('canvas').evaluate((n,old)=>n===old,canvas)).toBe(true);expect(errors).toEqual([]);
 fs.writeFileSync(path.join(__dirname,'browser-report.json'),JSON.stringify({viewport:{width:1440,height:900},renderer:'SwiftShader',samples,errors,checks:{toolsBenchApproach:true,backwards:true,blockedIdle:true,latestRoadEdge:true,crossbar:true,projectDetails:true,returnFocus:true,cameraRestored:true,canvasPersistent:true}},null,2));console.log('Tools/Latest native smoke passed');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exit(1);});
