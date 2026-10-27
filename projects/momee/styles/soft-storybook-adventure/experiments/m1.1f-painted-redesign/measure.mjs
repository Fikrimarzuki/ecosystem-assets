import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { PNG } from 'pngjs';

const root = path.dirname(fileURLToPath(import.meta.url));
const candidates = [['candidate-a-refined-b','a'], ['candidate-b-premium-painted','b'], ['candidate-c-gouache-adventure','c']];
// Records only. Never changes a PNG or its alpha.
export function measure(file) {
  const bytes = fs.readFileSync(file), png = PNG.sync.read(bytes);
  const {width, height, data} = png;
  const counts = {fully_transparent:0, fully_opaque:0, partial:0};
  const boxes = {opaque:{minX:width,minY:height,maxX:-1,maxY:-1}, nontransparent:{minX:width,minY:height,maxX:-1,maxY:-1}};
  for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
    const a=data[(y*width+x)*4+3];
    counts[a===0?'fully_transparent':a===255?'fully_opaque':'partial']++;
    for(const [name,test] of [['opaque',a===255],['nontransparent',a>0]]) if(test) {
      const b=boxes[name];b.minX=Math.min(b.minX,x);b.minY=Math.min(b.minY,y);b.maxX=Math.max(b.maxX,x);b.maxY=Math.max(b.maxY,y);
    }
  }
  const result={file:path.relative(root,file),sha256:crypto.createHash('sha256').update(bytes).digest('hex'),size:{width,height},png_header:{bit_depth:bytes[24],colour_type:bytes[25],colour_type_6_means:'RGBA'},alpha_histogram_summary:counts,bounding_box_convention:'inclusive; opaque means alpha=255; nontransparent means alpha>0'};
  for(const [name,b] of Object.entries(boxes)) {
    result[name+'_bounding_box']=b.maxX<0?null:{x:b.minX,y:b.minY,width:b.maxX-b.minX+1,height:b.maxY-b.minY+1};
    result[name+'_margins_px']=b.maxX<0?null:{left:b.minX,right:width-1-b.maxX,top:b.minY,bottom:height-1-b.maxY};
  }
  const m=result.nontransparent_margins_px;
  result.touches_edge=m?Object.fromEntries(Object.entries(m).map(([k,v])=>[k,v===0])):null;
  result.anything_touches_edge=m?Object.values(m).some(v=>v===0):false;
  result.minimum_six_percent_empty_left_right_top=m?m.left>=width*.06&&m.right>=width*.06&&m.top>=height*.06:false;
  return result;
}
if(process.argv[1]===fileURLToPath(import.meta.url)) for(const [folder,key] of candidates) {
  const file=path.join(root,folder,`mom-${key}-v1.png`);
  const result=measure(file);
  fs.writeFileSync(path.join(root,folder,'measurements.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));
}
