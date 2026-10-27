import fs from 'node:fs';
import crypto from 'node:crypto';
import { PNG } from 'pngjs';
import { alphaStats } from '../../../../../../../scripts/lib/png.mjs';
const arm = new URL('./', import.meta.url);
const source = PNG.sync.read(fs.readFileSync(new URL('generations/generation-01-original.png', arm)));
const out = new PNG({width:1024,height:1280});
// Full-frame scale only; bilinear interpolation in premultiplied alpha.
for(let y=0;y<out.height;y++) for(let x=0;x<out.width;x++){
  const sx=(x+.5)*source.width/out.width-.5, sy=(y+.5)*source.height/out.height-.5;
  const ix=Math.floor(sx),iy=Math.floor(sy),fx=sx-ix,fy=sy-iy;
  const sums=[0,0,0,0];
  for(const [dx,dy,w] of [[0,0,(1-fx)*(1-fy)],[1,0,fx*(1-fy)],[0,1,(1-fx)*fy],[1,1,fx*fy]]){
    const xx=Math.max(0,Math.min(source.width-1,ix+dx)), yy=Math.max(0,Math.min(source.height-1,iy+dy));
    const i=(yy*source.width+xx)*4, a=source.data[i+3]/255;
    for(let c=0;c<3;c++)sums[c]+=source.data[i+c]*a*w;
    sums[3]+=a*w;
  }
  const i=(y*out.width+x)*4;
  for(let c=0;c<3;c++)out.data[i+c]=sums[3]?Math.round(sums[c]/sums[3]):0;
  out.data[i+3]=Math.round(sums[3]*255);
}
const bytes=PNG.sync.write(out);
fs.writeFileSync(new URL('mom-neutral-painted-v1.png',arm),bytes,{flag:'wx'});
function stats(p){
  let transparent=0,partial=0,opaque=0;
  for(let i=3;i<p.data.length;i+=4){const a=p.data[i];if(!a)transparent++;else if(a===255)opaque++;else partial++;}
  return {dimensions:[p.width,p.height],transparent_pixels:transparent,partial_alpha_pixels:partial,opaque_pixels:opaque,alpha_bbox_threshold_1:alphaStats(p,1),alpha_bbox_threshold_128:alphaStats(p,128),corner_alpha:[p.data[3],p.data[(p.width-1)*4+3],p.data[((p.height-1)*p.width)*4+3],p.data[(p.width*p.height-1)*4+3]]};
}
const metrics={source:stats(source),derived:stats(out),derivation:{source:'generations/generation-01-original.png',output:'mom-neutral-painted-v1.png',method:'Full-frame bilinear scale only, premultiplied-alpha interpolation; no crop, repaint, matte removal, defringe, sharpening or retouch',scale_xy:[1024/source.width,1280/source.height],aspect_ratio_change_percent:((1024/1280)/(source.width/source.height)-1)*100,sha256:crypto.createHash('sha256').update(bytes).digest('hex')},eye_crop_xywh:[295,390,458,205]};
const eyes=new PNG({width:458,height:205});PNG.bitblt(out,eyes,295,390,458,205,0,0);
fs.writeFileSync(new URL('review/candidate-eyes.png',arm),PNG.sync.write(eyes),{flag:'wx'});
for(const [name,rgb] of [['alpha-white',[255,255,255]],['alpha-dark',[30,35,40]]]){
 const p=new PNG({width:out.width,height:out.height});
 for(let i=0;i<p.data.length;i+=4){const a=out.data[i+3]/255;for(let c=0;c<3;c++)p.data[i+c]=Math.round(out.data[i+c]*a+rgb[c]*(1-a));p.data[i+3]=255;}
 fs.writeFileSync(new URL('review/'+name+'.png',arm),PNG.sync.write(p),{flag:'wx'});
}
fs.writeFileSync(new URL('review/measurements.json',arm),JSON.stringify(metrics,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(metrics,null,2));
