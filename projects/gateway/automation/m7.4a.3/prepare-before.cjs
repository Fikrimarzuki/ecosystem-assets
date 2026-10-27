const fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../m7.4a/final-acceptance/acceptance.cjs'),'utf8');
let code=source.slice(0,source.indexOf("  await enter('Latest Builds');await capture('latest-entry')"));
code=code.replace('acceptance-report.json','before-report.json');
code+=`
  for(const [width,height] of [[1440,900],[768,700]]){
    await page.setViewportSize({width,height});await enter('Latest Builds');
    await page.keyboard.down('KeyS');await page.waitForTimeout(950);await page.keyboard.up('KeyS');await page.waitForTimeout(1500);
    await capture('before-latest-settled-'+width);await leave('Latest Builds');
  }
  save();console.log(JSON.stringify(report.captures.map(c=>({name:c.name,projection:c.projection})),null,2));
 }catch(error){report.failure=String(error);save();throw error;}finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
`;
fs.writeFileSync(path.join(__dirname,'before.cjs'),code);
