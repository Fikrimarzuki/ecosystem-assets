import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {PNG} from 'pngjs';
const root=path.dirname(fileURLToPath(import.meta.url));
// Permitted operations only: transparent padding and uniform bilinear scaling.
// Premultiplied-alpha interpolation avoids colour bleed from empty source pixels.
function resize(src,width,height) {
  const dst=new PNG({width,height});
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const sx=(x+.5)*src.width/width-.5,sy=(y+.5)*src.height/height-.5;
    const x0=Math.floor(sx),y0=Math.floor(sy),fx=sx-x0,fy=sy-y0;
    let a=0;const rgb=[0,0,0];
    for(let j=0;j<2;j++)for(let i=0;i<2;i++){
      const xx=Math.max(0,Math.min(src.width-1,x0+i)),yy=Math.max(0,Math.min(src.height-1,y0+j));
      const k=(yy*src.width+xx)*4,w=(i?fx:1-fx)*(j?fy:1-fy),aa=src.data[k+3];
      a+=aa*w;for(let c=0;c<3;c++)rgb[c]+=src.data[k+c]*aa*w;
    }
    const k=(y*width+x)*4;dst.data[k+3]=Math.round(a);
    if(a>0)for(let c=0;c<3;c++)dst.data[k+c]=Math.round(rgb[c]/a);
  }
  return dst;
}
for(const [folder,key,selected] of [['candidate-a-refined-b','a',2],['candidate-b-premium-painted','b',2],['candidate-c-gouache-adventure','c',3]]) {
  const original=`generations/generation-${String(selected).padStart(2,'0')}-original.png`;
  const src=PNG.sync.read(fs.readFileSync(path.join(root,folder,original)));
  const pad=new PNG({width:1400,height:1750});
  pad.data.fill(0);
  const left=Math.floor((pad.width-src.width)/2),top=Math.floor((pad.height-src.height)/2);
  PNG.bitblt(src,pad,0,0,src.width,src.height,left,top);
  const dst=resize(pad,1024,1280),file=`mom-${key}-v1.png`;
  fs.writeFileSync(path.join(root,folder,file),PNG.sync.write(dst,{colorType:6,inputColorType:6}));
  fs.writeFileSync(path.join(root,folder,`mom-${key}-thumbnail-144.png`),PNG.sync.write(resize(dst,144,180),{colorType:6}));
  fs.writeFileSync(path.join(root,folder,'derivation.json'),JSON.stringify({selected,source:original,source_size:{width:src.width,height:src.height},crop:{x:0,y:0,width:src.width,height:src.height},pad:{canvas_width:1400,canvas_height:1750,left,top,right:1400-src.width-left,bottom:1750-src.height-top,rgba:[0,0,0,0]},scale:{uniform_factor:1024/1400,width:1024,height:1280,filter:'bilinear, premultiplied-alpha interpolation, round to nearest 8-bit'},deliverable:file,thumbnail:{file:`mom-${key}-thumbnail-144.png`,width:144,height:180,filter:'same bilinear scaler'},other_modifications:'none; no repainting, retouching or alpha cleanup'},null,2)+'\n');
}
