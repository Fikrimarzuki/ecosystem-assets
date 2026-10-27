const fs=require('node:fs'),path=require('node:path');
const {chromium,expect}=require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false});
 const report={browserVersion:browser.version(),captures:[],checks:{},errors:[]},save=()=>fs.writeFileSync(path.join(__dirname,'visual-report.json'),JSON.stringify(report,null,2));
 try {
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});page.on('pageerror',e=>report.errors.push(e.message));
  const r=page.getByRole('region',{name:'Project Universe'}),s=r.locator('[data-ready="true"]');await page.goto('http://127.0.0.1:3001');await expect(s).toBeVisible({timeout:60000});await s.scrollIntoViewIfNeeded();
  // INJECT_EXISTING_DIAGNOSTIC
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
  await enter('Latest Builds');await page.keyboard.down('KeyS');await page.waitForTimeout(1000);await capture('latest-crossbar-moving-repro');await page.keyboard.up('KeyS');await page.waitForTimeout(1500);const settled=await capture('latest-crossbar-settled-repro');
  if(settled.boots.minY < -1 || settled.boots.maxY > 1){report.confirmedDefect='Settled Latest crossbar route clips boot vertices outside the viewport';save();return;}
  await leave('Latest Builds');await enter('Latest Builds');await page.mouse.move(720,450);const heading=(await snap()).player.yaw;await page.mouse.move(720+heading/.0025,450);await page.keyboard.down('KeyS');await page.waitForTimeout(50);await page.keyboard.up('KeyS');await page.keyboard.down('KeyD');await page.waitForTimeout(1100);await page.keyboard.up('KeyD');await page.waitForTimeout(300);await capture('latest-roof-guard');report.checks.roofApproachRecorded=true;await leave('Latest Builds');
  await enter('Tools');await capture('tools-idle-visual');
  for(const [name,key] of [['forward','KeyW'],['backward','KeyS'],['left','KeyA'],['right','KeyD']]){
   await page.keyboard.down(key);await page.waitForTimeout(200);await capture('tools-'+name+'-visual');await page.keyboard.up(key);await page.waitForTimeout(350);
  }
  await page.keyboard.down('KeyS');await page.waitForTimeout(100);await page.keyboard.up('KeyS');await page.waitForTimeout(70);await capture('tools-stop-crossfade');await page.waitForTimeout(350);await capture('tools-stopped-idle');
  await leave('Tools');report.checks.directionsAndStartStopRecorded=true;report.checks.returnRestored=true;save();expect(report.errors).toEqual([]);
 }catch(error){report.failure=String(error);save();throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
