const fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../../m7.4a.2/after.cjs'),'utf8');
let code=source.slice(0,source.indexOf("  await enter('Latest Builds');await capture"));
code=code.replace('after-report.json','acceptance-report.json');
code=code.replace('report={browserVersion:',"report={phase:'final-bounded-acceptance',browserVersion:");
code=code.replace('const attrs=mesh.geometry.attributes;',`const canvas=q.state.gl.domElement.getBoundingClientRect(),hint=[...document.querySelectorAll('p')].find(e=>e.textContent.includes('W/A/S/D · Mouse to look'));
    const rect=hint?.getBoundingClientRect();const overlay=rect?{x:rect.x,y:rect.y,width:rect.width,height:rect.height,background:getComputedStyle(hint).backgroundColor,opacity:getComputedStyle(hint).opacity,bootVerticesInside:0}:null;
    const attrs=mesh.geometry.attributes;`);
code=code.replace('boots.count++;boots.minY=',`boots.count++;if(overlay){const px=canvas.x+(point.x+1)*canvas.width/2,py=canvas.y+(1-point.y)*canvas.height/2;if(px>=overlay.x&&px<=overlay.x+overlay.width&&py>=overlay.y&&py<=overlay.y+overlay.height)overlay.bootVerticesInside++;}boots.minY=`);
code=code.replace('return{range,boots,groups,baseline,fov:', 'return{range,boots,groups,baseline,overlay,fov:');
code+=`
  await enter('Latest Builds');await capture('latest-entry');report.checks.nativePointerLock=true;
  await page.keyboard.down('KeyS');await page.waitForTimeout(950);await page.keyboard.up('KeyS');await page.waitForTimeout(1500);
  report.hardware=await page.evaluate(()=>window.__qa.hardware);if(/swiftshader|software|llvmpipe/i.test(report.hardware.renderer))throw Error('Physical GPU not confirmed');
  const raw=await page.evaluate(async()=>{const q=window.__qa;q.values={};q.renders=[];q.cameraPositions=[];q.motionFrames=[];q.animationFrames=[];q.active=true;let id;const refresh=()=>{q.refresh();id=requestAnimationFrame(refresh);};refresh();const start=performance.now();await new Promise(r=>setTimeout(r,12000));q.active=false;cancelAnimationFrame(id);return{elapsed:performance.now()-start,renderTimes:q.renders,camera:q.values['frame-priority--3'],animation:q.values['animation-update'],positions:q.cameraPositions,motion:q.motionFrames,resources:q.resources()};});
  const stats=a=>{const s=[...a].sort((a,b)=>a-b);return{count:a.length,mean:a.reduce((sum,x)=>sum+x,0)/a.length,p95:s[Math.floor(s.length*.95)],max:s.at(-1),over33:a.filter(x=>x>33.34).length,over50:a.filter(x=>x>50).length};};
  const intervals=raw.renderTimes.slice(1).map((x,i)=>x-raw.renderTimes[i]);report.sanity={state:'corrected Latest stationary TPS',elapsedMs:raw.elapsed,fps:raw.renderTimes.length*1000/raw.elapsed,frames:stats(intervals),camera:stats(raw.camera),animation:stats(raw.animation),resources:raw.resources,maxCameraStep:Math.max(...raw.positions.slice(1).map((p,i)=>Math.hypot(...p.map((x,j)=>x-raw.positions[i][j])))),movingFrames:raw.motion.filter(x=>x.speed>.0001).length};save();
  const fixed=await capture('latest-corrected-settled');report.checks.characterInsideFrustum=fixed.range.minY>=-1&&fixed.range.maxY<=1&&fixed.range.minX>=-1&&fixed.range.maxX<=1;
  if(fixed.overlay?.bootVerticesInside>0){report.confirmedDefect='Instruction HUD covers real boot vertices at the corrected settled Latest position';report.stoppedUnderDefectRule=true;save();console.log(JSON.stringify({hardware:report.hardware,sanity:report.sanity,projection:fixed,confirmedDefect:report.confirmedDefect},null,2));return;}
  await leave('Latest Builds');report.checks.returnRestoration=true;save();
 }catch(error){report.failure=String(error);save();throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
`;
fs.writeFileSync(path.join(__dirname,'acceptance.cjs'),code);
