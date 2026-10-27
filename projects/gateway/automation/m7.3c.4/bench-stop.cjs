// Targeted follow-up: earlier D traversal stopped at the outer boundary, not the bench.
const fs=require('node:fs'),path=require('node:path'),{chromium,expect}=require(path.resolve('app-gateway-fe/node_modules/@playwright/test'));
(async()=>{
 const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'}),r=page.getByRole('region',{name:'Project Universe'}),s=r.locator('[data-ready="true"]');
 const snap=()=>s.evaluate(e=>{const c=e.__universeController;return{...e.__universeRender(),speed:c.character.speed,state:c.getSnapshot(),player:{...c.player.position,yaw:c.player.yaw,pitch:c.player.pitch}};});
 await page.goto('http://127.0.0.1:3000',{waitUntil:'domcontentloaded',timeout:120000});await expect(s).toBeVisible({timeout:60000});await s.scrollIntoViewIfNeeded();await r.getByRole('button',{name:'Tools',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});
 await r.getByRole('button',{name:'Explore in Third Person'}).click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).state.firstPersonLocked).toBe(true);await expect.poll(async()=>(await snap()).astronaut.visual).toBe('model');
 await page.mouse.move(720,450);const initial=await snap();await page.mouse.move(720+initial.player.yaw/.0025,450);
 await expect.poll(async()=>(await snap()).player.yaw).toBeCloseTo(0,2); // Mouse motion is integer-pixel quantized.
 await page.keyboard.down('KeyS');try{await expect.poll(async()=>(await snap()).player.z,{timeout:15000}).toBeGreaterThan(.58);}finally{await page.keyboard.up('KeyS');}
 // At the aligned zero yaw, D approaches the bench west face.
 const before=await snap();expect(before.player.z).toBeGreaterThan(.55);expect(before.player.z).toBeLessThan(.81);
 await page.keyboard.down('KeyD');try{await expect.poll(async()=>(await snap()).player.x,{timeout:15000}).toBeGreaterThan(.045);await expect.poll(async()=>{const q=await snap();fs.writeFileSync(path.join(__dirname,'bench-stop-progress.json'),JSON.stringify(q,null,2));return q.speed<.001&&q.astronaut.animation.idleWeight===1;},{timeout:15000}).toBe(true);await page.waitForTimeout(250);}finally{await page.keyboard.up('KeyD');}
 const after=await snap();expect(after.player.x).toBeGreaterThan(.045);expect(after.player.x).toBeLessThan(.05701);expect(Math.abs(after.player.z-before.player.z)).toBeLessThan(.001);
 await page.screenshot({path:path.join(__dirname,'tools-confirmed-bench-stop.png')});
 await page.keyboard.press('Escape');await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect Tools'})).toBeFocused();
 // Reset only Tools so the project approach uses its normal entry orientation.
 await r.getByRole('button',{name:/Back to Universe/}).click();await expect(s).toHaveAttribute('data-state',/^overview/);
 await page.emulateMedia({reducedMotion:'reduce'});await r.getByRole('button',{name:'Tools',exact:true}).click();await expect(s).toHaveAttribute('data-state','inspecting');await page.emulateMedia({reducedMotion:'no-preference'});
 // Recheck the affected Tools entry/support height and normal project route.
 const restoredCamera=(await snap()).camera;
 await r.getByRole('button',{name:'Explore in Third Person'}).click();
 await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);await expect.poll(async()=>(await snap()).state.firstPersonLocked).toBe(true);
 await page.keyboard.down('KeyW');try{await expect.poll(async()=>{const q=await snap();fs.writeFileSync(path.join(__dirname,'tools-project-progress.json'),JSON.stringify(q,null,2));return r.getByRole('status').filter({hasText:'Press E or Click to explore'}).isVisible();},{timeout:15000}).toBe(true);}finally{await page.keyboard.up('KeyW');}
 await page.keyboard.press('KeyE');await expect(r.getByRole('article',{name:'CareerLens project details'})).toBeVisible();
 const frozen=(await snap()).camera;await page.waitForTimeout(150);expect((await snap()).camera).toEqual(frozen);
 await page.keyboard.press('Escape');if(await page.evaluate(()=>!!document.pointerLockElement))await page.keyboard.press('Escape');
 await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect Tools'})).toBeFocused();
 await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-restoredCamera[i])))).toBeLessThan(1e-6);
 fs.writeFileSync(path.join(__dirname,'bench-stop-report.json'),JSON.stringify({viewport:{width:1440,height:900},before,after,checks:{benchStop:true,heldKeyIdle:true,returnFocus:true,projectDetails:true,detailsCameraFrozen:true,cameraRestored:true}},null,2));console.log('Native west-face bench stop passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
