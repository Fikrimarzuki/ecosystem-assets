// Experiment-local diagnostic; uses the repository's existing pngjs helpers.
// No source writes. Test output is NOT a candidate or a production repair.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {decode,encode} from '../../../../../../../scripts/lib/png.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const source=path.resolve(root,'../../m1.1f-painted-redesign/candidate-b-premium-painted/generations/generation-02-original.png');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(source),src=decode(bytes),{width:w,height:h,data}=src;
const out=decode(bytes),dist=new Uint16Array(w*h),hist=new Uint32Array(256);
// Distance from alpha<240, or the image boundary, in Manhattan pixels.
for(let y=0;y<h;y++)for(let x=0;x<w;x++){
 const i=y*w+x;hist[data[4*i+3]]++;
 dist[i]=data[4*i+3]<240?0:Math.min(x+1,y+1,w-x,h-y,65534);
 if(x)dist[i]=Math.min(dist[i],dist[i-1]+1);
 if(y)dist[i]=Math.min(dist[i],dist[i-w]+1);
}
for(let y=h-1;y>=0;y--)for(let x=w-1;x>=0;x--){const i=y*w+x;if(x<w-1)dist[i]=Math.min(dist[i],dist[i+1]+1);if(y<h-1)dist[i]=Math.min(dist[i],dist[i+w]+1);}
const coreHist=new Uint32Array(256),outHist=new Uint32Array(256);
let changed=0,rgbChanges=0,protectedChanges=0,coreCount=0,maxDelta=0;
for(let i=0;i<w*h;i++){
 const a=data[4*i+3];
 if(dist[i]>=32){coreHist[a]++;coreCount++;}
 // Eight pixels of untouched near-opaque boundary, then a smooth 24-px transition.
 if(dist[i]>8){const t=Math.min(1,(dist[i]-8)/24),weight=t*t*(3-2*t);out.data[4*i+3]=Math.round(a+(255-a)*weight);}
 const b=out.data[4*i+3];outHist[b]++;
 if(a!==b){changed++;maxDelta=Math.max(maxDelta,b-a);if(a<240||dist[i]<=8)protectedChanges++;}
 for(let c=0;c<3;c++)if(data[4*i+c]!==out.data[4*i+c])rgbChanges++;
}
fs.writeFileSync(path.join(root,'m11f-b-interior-opacity-test.png'),encode(out),{flag:'wx'});
// Identity roundtrip separates encoder behaviour from actual source transparency.
const roundtrip=decode(encode(src));
const sameDecodedPixels=Buffer.compare(data,roundtrip.data)===0;
const report={source:path.relative(root,source),source_sha256:hash(bytes),size:{width:w,height:h},
 method:'Support alpha>=240; Manhattan distance from lower-alpha pixels or image boundary; alpha unchanged within 8px of support boundary; smoothstep promotion toward 255 from distance 8 to 32px; deep core alpha=255. RGB unchanged everywhere. No colour keying, flattening, RGB unpremultiplication or edge thresholding.',
 original_histogram:[...hist],test_histogram:[...outHist],deep_interior_histogram:[...coreHist],deep_interior_pixels:coreCount,
 modal_deep_interior_alpha:[...coreHist].indexOf(Math.max(...coreHist)),changed_alpha_pixels:changed,maximum_alpha_delta:maxDelta,
 unchanged_rgb:rgbChanges===0,protected_edge_changes:protectedChanges,decode_encode_roundtrip_pixels_identical:sameDecodedPixels,
 source_unchanged:hash(fs.readFileSync(source))===hash(bytes),
 limitation:'A technical feasibility probe only. Near-opaque specks and transparency outside the selected interior stay unchanged. This cannot infer intended opacity or correct RGB contamination. The 240/8/32 settings are conservative test parameters, not a validated production pipeline.'};
fs.writeFileSync(path.join(root,'measurements.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({size:report.size,modal_core:report.modal_deep_interior_alpha,coreCount,changed,maxDelta,protectedChanges,rgbChanges,sameDecodedPixels,source_unchanged:report.source_unchanged}));
