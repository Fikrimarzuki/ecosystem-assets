const fs = require('node:fs'), path = require('node:path');
const { chromium, expect } = require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:false});
 const report={browserVersion:browser.version(),cases:[]};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  for(const [width,height] of [[1440,900],[768,700]]){
   await page.setViewportSize({width,height});await page.goto('http://127.0.0.1:3001');
   const region=page.getByRole('region',{name:'Project Universe'}), scene=region.locator('[data-ready="true"]');
   await expect(scene).toBeVisible();await scene.scrollIntoViewIfNeeded();await region.getByRole('button',{name:'Tools',exact:true}).click();await expect(scene).toHaveAttribute('data-state','inspecting');
   const entries=[];
   for(const name of ['Explore in First Person','Explore in Third Person']){
    const button=region.getByRole('button',{name,exact:true});await button.scrollIntoViewIfNeeded();
    entries.push(await button.evaluate(button=>{const box=button.getBoundingClientRect(),x=box.x+box.width/2,y=box.y+box.height/2,hit=document.elementFromPoint(x,y);const parent=button.parentElement;return{name:button.textContent,buttonBounds:box.toJSON(),center:{x,y},hit:{tag:hit?.tagName,role:hit?.getAttribute('role'),label:hit?.getAttribute('aria-label'),className:hit?.className},buttonReceivesPointer:!!hit&&button.contains(hit),rowStyle:{position:getComputedStyle(parent).position,zIndex:getComputedStyle(parent).zIndex}};}));
   }
   await scene.screenshot({path:path.join(__dirname,`entry-hit-${width}.png`)});
   report.cases.push({viewport:{width,height},entries});
  }
  fs.writeFileSync(path.join(__dirname,'entry-hit-test.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
