const fs=require('node:fs'),path=require('node:path');
let code=fs.readFileSync(path.join(__dirname,'../m7.4a/resumed/camera-repro.cjs'),'utf8');
code=code.replace('camera-repro-report.json','after-report.json').replace("page.goto('http://127.0.0.1:3001')","page.goto('http://127.0.0.1:3001',{timeout:120000})");
code=code.replace("const feet=new Set", "const original=camera.clone();original.fov=65;original.updateProjectionMatrix();const baseline={minY:Infinity,maxY:-Infinity};const groups={helmet:{minY:Infinity,maxY:-Infinity},torso:{minY:Infinity,maxY:-Infinity},lower:{minY:Infinity,maxY:-Infinity}};const world=point.clone(); const feet=new Set");
code=code.replace("mesh.getVertexPosition(i,point).applyMatrix4(mesh.matrixWorld).project(camera);", "mesh.getVertexPosition(i,world).applyMatrix4(mesh.matrixWorld);point.copy(world).project(original);baseline.minY=Math.min(baseline.minY,point.y);baseline.maxY=Math.max(baseline.maxY,point.y);point.copy(world).project(camera);");
code=code.replace("let footWeight=0;", "for(const [group,pattern] of [['helmet',/head|neck/i],['torso',/spine/i],['lower',/leg/i]]){let weight=0;for(const getter of ['getX','getY','getZ','getW'])if(pattern.test(mesh.skeleton.bones[attrs.skinIndex[getter](i)]?.name??''))weight+=attrs.skinWeight[getter](i);if(weight>.5){groups[group].minY=Math.min(groups[group].minY,point.y);groups[group].maxY=Math.max(groups[group].maxY,point.y);}} let footWeight=0;");
code=code.replace("return{range,boots,renderer:","return{range,boots,groups,baseline,fov:camera.fov,renderer:");
const start=code.indexOf('  for(let visit=1;'),end=code.indexOf('save(); }catch(error)',start);
code=code.slice(0,start)+`
  await enter('Latest Builds');await capture('after-latest-entry');
  await page.keyboard.down('KeyS');await page.waitForTimeout(950);await page.keyboard.up('KeyS');await page.waitForTimeout(1500);
  const settled=await capture('after-latest-crossbar-settled');
  if(settled.range.minY < -1 || settled.range.maxY > 1)throw Error('Latest mesh remains vertically cropped');
  await page.evaluate(()=>{const q=window.__qa;q.values={};q.renders=[];q.motionFrames=[];q.active=true;q.refresh();});
  for(let i=0;i<6;i++)for(const key of ['KeyW','KeyS','KeyA','KeyD']){await page.keyboard.down(key);await page.waitForTimeout(400);await page.keyboard.up(key);await page.evaluate(()=>window.__qa.refresh());}
  report.cpu=await page.evaluate(()=>{const q=window.__qa;q.active=false;const summarize=a=>{const sorted=[...a].sort((a,b)=>a-b);return{count:a.length,mean:a.reduce((a,b)=>a+b,0)/a.length,p95:sorted[Math.floor(sorted.length*.95)],max:Math.max(...a)};};return{camera:summarize(q.values['frame-priority--3']),movingFraction:q.motionFrames.filter(x=>x.speed>.0001).length/q.motionFrames.length,renderer:q.hardware.renderer};});save();
  await page.waitForTimeout(1500);await capture('after-latest-direction-changes');await leave('Latest Builds');
  await enter('Tools');await capture('after-tools-entry');
  await page.keyboard.down('KeyD');await page.waitForTimeout(350);await page.keyboard.up('KeyD');await page.waitForTimeout(1500);await capture('after-tools-bench');
  await page.keyboard.down('KeyW');await page.waitForTimeout(200);await page.keyboard.up('KeyW');await page.waitForTimeout(1500);await capture('after-tools-forward');
  await leave('Tools');await enter('Tools');
  await page.keyboard.down('KeyW');await page.waitForTimeout(2200);await page.keyboard.up('KeyW');await page.waitForTimeout(1500);await capture('after-tools-project-approach');
  await page.keyboard.press('KeyE');await expect.poll(async()=>(await snap()).state.firstPersonProjectOpen).toBe(true);
  const frozen=await snap();await page.waitForTimeout(350);const later=await snap();expect(later.camera).toEqual(frozen.camera);report.checks.projectFocusFreeze=true;
  await page.keyboard.press('Escape');await expect.poll(async()=>(await snap()).state.firstPersonProjectOpen).toBe(false);
  await r.getByRole('button',{name:'Return to Planet',exact:true}).first().click();await expect(r.getByRole('group',{name:'Inspect Tools'})).toBeFocused();await expect.poll(async()=>Math.max(...(await snap()).camera.map((v,i)=>Math.abs(v-entryCamera[i])))).toBeLessThan(1e-6);
  report.checks.returnCameraAndFocus=true;report.checks.latestNativeSettledCoverage=true;report.checks.directionsAndBenchRecorded=true;
  `+code.slice(end);
fs.writeFileSync(path.join(__dirname,'after.cjs'),code);
