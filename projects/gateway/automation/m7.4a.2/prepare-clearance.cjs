const fs=require('node:fs'),path=require('node:path');
let code=fs.readFileSync(path.join(__dirname,'after.cjs'),'utf8').replace('after-report.json','clearance-report.json');
const start=code.indexOf("  await enter('Latest Builds');await capture"),end=code.indexOf('save(); }catch(error)',start);
code=code.slice(0,start)+`
  await enter('Tools');await page.mouse.move(720,450);const heading=(await snap()).player.yaw;await page.mouse.move(720+heading/.0025,450);
  await page.keyboard.down('KeyS');await expect.poll(async()=>(await snap()).player.z).toBeGreaterThan(.58);await page.keyboard.up('KeyS');await page.waitForTimeout(1500);await capture('after-tools-real-bench-side');
  await page.keyboard.down('KeyD');await expect.poll(async()=>{const s=await snap();return s.astronaut.animation.idleWeight===1&&s.player.x>.03;},{timeout:8000}).toBe(true);await page.keyboard.up('KeyD');await page.waitForTimeout(1500);await capture('after-tools-bench-blocked-idle');report.checks.benchBoundary=true;await leave('Tools');
  await enter('Latest Builds');await page.keyboard.down('KeyS');await page.waitForTimeout(950);await page.keyboard.up('KeyS');await page.waitForTimeout(1500);await capture('after-latest-crossbar-approach');
  const before=(await snap()).player;await page.keyboard.down('KeyS');await page.waitForTimeout(450);await page.keyboard.up('KeyS');await page.waitForTimeout(1500);const beyond=await snap();expect(beyond.player.z).toBeGreaterThan(before.z+.1);await capture('after-latest-crossbar-beyond');await leave('Latest Builds');report.checks.crossbarTraversal=true;
  `+code.slice(end);
fs.writeFileSync(path.join(__dirname,'clearance.cjs'),code);
