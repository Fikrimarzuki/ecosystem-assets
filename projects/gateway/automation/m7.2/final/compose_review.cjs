const fs = require('node:fs');
const path = require('node:path');
const sharp = require('../../../../app-gateway-fe/node_modules/sharp');
const here = __dirname;
async function sheet(name, files) {
  const width=384, height=510;
  const panels=[];
  for (let i=0;i<files.length;i++) {
    const [file,label]=files[i];
    const text=Buffer.from(`<svg width="384" height="30"><rect width="100%" height="100%" fill="#102233"/><text x="10" y="20" fill="white" font-family="sans-serif" font-size="14">${label}</text></svg>`);
    const picture=await sharp(path.join(here,file)).resize(width,480).toBuffer();
    panels.push({input:text,left:(i%4)*width,top:Math.floor(i/4)*height});
    panels.push({input:picture,left:(i%4)*width,top:Math.floor(i/4)*height+30});
  }
  await sharp({create:{width:width*4,height:height*2,channels:3,background:'#102233'}}).composite(panels).png().toFile(path.join(here,name));
}
(async()=>{
  const full=['idle-56-front','idle-56-back','walk-12-front','walk-23.75-front'];
  const close=['neck','wrist','knees','boots'];
  await sheet('deformation-overview.png',['source','final'].flatMap(v=>full.map(f=>[`${v}-${f}.png`,`${v}: ${f}`])));
  await sheet('deformation-closeups.png',['source','final'].flatMap(v=>close.map(f=>[`${v}-close-${f}.png`,`${v}: ${f}`])));
  console.log('Two matched comparison sheets created.');
})();
