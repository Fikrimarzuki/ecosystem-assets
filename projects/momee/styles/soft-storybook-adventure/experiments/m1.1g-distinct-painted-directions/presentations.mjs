import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {openBrowser} from '../../../../../../scripts/lib/render.mjs';
import {measure} from '../m1.1f-painted-redesign/measure.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const items=JSON.parse(fs.readFileSync(path.join(root,'comparison/crops-and-scales.json'))).items.slice(5);
const browser=await openBrowser();
try{
 const page=await browser.newPage();await page.setContent('<canvas width="1024" height="1280"></canvas>');
 for(const [i,it]of items.entries()){
  const file=path.resolve(root,it.source),[x,y,w,h]=it.figure,scale=1000/h;
  const left=(1024-w*scale)/2-x*scale,top=130-y*scale;
  if(left<0||top<0||left+it.source_size[0]*scale>1024||top+it.source_size[1]*scale>1280)throw Error('Full original would clip');
  const base64=await page.evaluate(async({src,scale,left,top})=>{const im=new Image();im.src=src;await im.decode();const c=document.querySelector('canvas'),g=c.getContext('2d');g.clearRect(0,0,1024,1280);g.imageSmoothingQuality='high';g.drawImage(im,left,top,im.width*scale,im.height*scale);return c.toDataURL('image/png').split(',')[1];},{src:'data:image/png;base64,'+fs.readFileSync(file).toString('base64'),scale,left,top});
  const folder=path.dirname(file),name=`mom-${'abc'[i]}-v1.png`,dest=path.join(folder,name);
  fs.writeFileSync(dest,Buffer.from(base64,'base64'),{flag:'wx'});
  const result=measure(dest);result.file=path.relative(root,dest);
  fs.writeFileSync(path.join(folder,'presentation-provenance.json'),JSON.stringify({file:name,source:'generation-01-original.png',source_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),operations:'Uniformly scale the ENTIRE original including faint fringe pixels, then transparent padding only. No cropping, RGB repair, alpha remapping, keying, flattening, retouching or paint changes.',canvas:[1024,1280],scale,left,top,figure_bbox_source:it.figure,target_figure_height:1000,target_figure_top:130,filter:'Existing Chromium canvas high-quality interpolation; RGBA PNG',measurements:result},null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({candidate:'abc'[i],size:result.size,margins:result.nontransparent_margins_px,six_percent_margin:result.minimum_six_percent_empty_left_right_top}));
 }
}finally{await browser.close();}
