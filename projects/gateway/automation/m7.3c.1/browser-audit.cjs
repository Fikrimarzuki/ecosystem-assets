// Read-only desktop audit. Diagnostics/captures stay outside Gateway.
const fs=require('node:fs/promises'),path=require('node:path');
const app=path.resolve('app-gateway-fe'),out=__dirname;
const {chromium,expect}=require(path.join(app,'node_modules/@playwright/test'));
(async()=>{
 const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const region=page.getByRole('region',{name:'Project Universe'}),scene=region.locator('[data-ready="true"]');
 const samples=[];
 async function capture(name,screenshot=true){
  const data=await scene.evaluate(e=>{const c=e.__universeController;return {...e.__universeRender(),player:{position:{...c.player.position},yaw:c.player.yaw,pitch:c.player.pitch},character:{yaw:c.character.yaw,speed:c.character.speed},nav:c.player.navigation,state:c.getSnapshot(),canvas:{width:e.querySelector('canvas').clientWidth,height:e.querySelector('canvas').clientHeight}};});
  samples.push({name,...data});if(screenshot)await page.screenshot({path:path.join(out,name+'.png')});return data;
 }
 await page.goto('http://127.0.0.1:3000/');await expect(scene).toBeVisible();await scene.scrollIntoViewIfNeeded();
 await region.getByRole('button',{name:'Tools',exact:true}).click();await expect(scene).toHaveAttribute('data-state','inspecting');
 const canvas=await region.locator('canvas').elementHandle();
 await page.emulateMedia({reducedMotion:'no-preference'});
 const button=region.getByRole('button',{name:'Explore in Third Person'}),box=await button.boundingBox();
 const x=box.x+box.width/2,y=box.y+box.height/2;
 await button.click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);
 await expect.poll(async()=>scene.evaluate(e=>e.__universeRender().astronaut.visual)).toBe('model');
 await capture('tools-entry-stationary');
 await page.mouse.move(x,y+200,{steps:4});await page.waitForTimeout(350);
 await capture('tools-clear-angle-stationary');
 await page.keyboard.down('KeyS');try{await page.waitForTimeout(380);await capture('tools-clear-angle-walking');}finally{await page.keyboard.up('KeyS');}
 await page.keyboard.down('KeyD');try{await page.waitForTimeout(180);await capture('tools-turning');}finally{await page.keyboard.up('KeyD');}
 // Re-enter to restore native spawn/entry framing before close-space/interaction review.
 await page.keyboard.press('Escape');await region.getByRole('button',{name:'Return to Planet',exact:true}).first().click();
 await button.click();await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);
 await capture('tools-reentry',false);
 await page.keyboard.down('KeyW');try{
  await expect(region.getByRole('status').filter({hasText:'Press E or Click to explore'})).toBeVisible({timeout:15000});
 }finally{await page.keyboard.up('KeyW');}
 await capture('tools-near-project');
 await page.keyboard.press('KeyE');await expect(region.getByRole('article',{name:'CareerLens project details'})).toBeVisible();
 const paused=await capture('tools-project-details',false);await page.waitForTimeout(150);
 const frozen=await capture('tools-details-frozen',false);
 await page.keyboard.press('Escape');await region.getByRole('button',{name:'Resume exploration'}).click();
 await expect.poll(()=>page.evaluate(()=>!!document.pointerLockElement)).toBe(true);
 await page.keyboard.down('KeyW');try{await expect.poll(async()=>scene.evaluate(e=>e.__universeController.character.speed),{timeout:15000}).toBe(0);await capture('tools-forward-after-resume');}finally{await page.keyboard.up('KeyW');}
 await page.keyboard.press('Escape');await region.getByRole('button',{name:'Return to Planet',exact:true}).first().click();
 await expect(region.getByRole('group',{name:'Inspect Tools'})).toBeFocused();
 const results={viewport:{width:1440,height:900},renderer:'Chromium SwiftShader; not real-device performance',errors,detailsFrozen:JSON.stringify(paused.astronaut.animation)===JSON.stringify(frozen.astronaut.animation),returnFocus:true,canvasPersistent:await region.locator('canvas').evaluate((n,old)=>n===old,canvas),samples};
 await fs.writeFile(path.join(out,'browser-report.json'),JSON.stringify(results,null,2));
 await browser.close();console.log(JSON.stringify({...results,samples:samples.map(s=>({name:s.name,player:s.player,speed:s.character.speed,clip:s.astronaut.animation?.clip}))},null,2));
})().catch(e=>{console.error(e);process.exit(1)});
