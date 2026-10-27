// Local review orchestration; reuses existing PNG helpers, Chromium and skill comparison script.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {decode,alphaStats} from '../../../../../../scripts/lib/png.mjs';
import {openBrowser} from '../../../../../../scripts/lib/render.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const compare=path.resolve('../ecosystem-skills/skills/projects/momee/momee-character-art/scripts/compare-sheet.mjs');
const alphaOnly=process.argv.includes('--alpha-only');
const f='../m1.1f-painted-redesign';
const items=[
 {id:'original-b',label:'Original B',source:`${f}/inputs/b-portrait.png`,figure:[0,14,294,337],face:[62,104,188,155],eyes:[71,142,159,60]},
 {id:'retained-m11e',label:'Retained M1.1e',source:`${f}/inputs/gate-a-painted.png`,face:[260,277,548,568],eyes:[293,457,467,137]},
 {id:'m11f-a',label:'M1.1f A',source:`${f}/candidate-a-refined-b/mom-a-v1.png`,face:[336,327,366,424],eyes:[363,475,310,88]},
 {id:'m11f-b',label:'M1.1f B',source:`${f}/candidate-b-premium-painted/mom-b-v1.png`,face:[340,330,370,424],eyes:[378,475,296,88]},
 {id:'m11f-c',label:'M1.1f C',source:`${f}/candidate-c-gouache-adventure/mom-c-v1.png`,face:[341,336,360,420],eyes:[375,480,294,88]},
 {id:'m11g-a',label:'M1.1g A / Classic',source:'candidate-a-classic-storybook/generation-01-original.png',face:[265,274,574,584],eyes:[334,479,476,166]},
 {id:'m11g-b',label:'M1.1g B / Cinema',source:'candidate-b-cinematic-2d/generation-01-original.png',face:[283,277,556,572],eyes:[357,469,440,133]},
 {id:'m11g-c',label:'M1.1g C / Gouache',source:'candidate-c-handcrafted-gouache/generation-01-original.png',face:[272,277,564,571],eyes:[336,480,471,164]},
];
const browser=await openBrowser();
try{
 const page=await browser.newPage({viewport:{width:1200,height:1000},deviceScaleFactor:1});
 await page.setContent('<!doctype html><canvas></canvas>');
 if(!alphaOnly)for(const it of items){
  const full=path.resolve(root,it.source),png=decode(fs.readFileSync(full));
  if(!it.figure){const a=alphaStats(png,128);it.figure=[a.minX,a.minY,a.maxX-a.minX,a.maxY-a.minY];}
  it.source_size=[png.width,png.height];
  const src='data:image/png;base64,'+fs.readFileSync(full).toString('base64');
  for(const h of [256,144]){
   const out=await page.evaluate(async({src,crop,h})=>{
    const img=new Image();img.src=src;await img.decode();const [x,y,w,sh]=crop,scale=h/sh;
    const c=document.querySelector('canvas');c.width=Math.ceil(w*scale);c.height=h;
    const g=c.getContext('2d');g.clearRect(0,0,c.width,h);g.imageSmoothingEnabled=true;g.imageSmoothingQuality='high';
    g.drawImage(img,x,y,w,sh,(c.width-w*scale)/2,0,w*scale,h);return c.toDataURL('image/png').split(',')[1];
   },{src,crop:it.figure,h});
   fs.writeFileSync(path.join(root,'comparison',`${it.id}-figure-${h}.png`),Buffer.from(out,'base64'),{flag:'wx'});
  }
 }
 await page.close();
 // Background composites: display-only sheets. The test PNG keeps its RGBA.
 const original=path.resolve(root,`${f}/candidate-b-premium-painted/generations/generation-02-original.png`);
 const tested=path.join(root,'alpha-test/m11f-b-interior-opacity-test.png');
 const testImages=[original,tested].map(p=>'data:image/png;base64,'+fs.readFileSync(p).toString('base64'));
 const p=await browser.newPage({viewport:{width:1088,height:428},deviceScaleFactor:1});
 await p.setContent(`<!doctype html><style>body{margin:0;background:#eee;font:12px system-ui}main{display:flex;gap:8px;padding:8px}.col{width:260px}.pair{display:flex;gap:4px}.pair img{width:128px;height:160px;object-fit:contain}.caption{padding:6px 0}h4{margin:4px 0}</style><main></main>`);
 await p.evaluate(async images=>{
  for(const [label,bg]of [['White','#ffffff'],['Cream','#f8f0e5'],['Dark','#18202a'],['Magenta','#d94cbd']]){
   const col=document.createElement('div');col.className='col';col.innerHTML=`<h4>${label}</h4><div class="caption">Original (left) / technical test (right)</div>`;
   for(const crop of [null,[512,40,128,160]]){
    const pair=document.createElement('div');pair.className='pair';pair.style.background=bg;
    for(const src of images){const im=new Image();im.src=src;await im.decode();const c=document.createElement('canvas');c.width=128;c.height=160;const g=c.getContext('2d');g.imageSmoothingQuality='high';
     if(crop)g.drawImage(im,...crop,0,0,128,160);else g.drawImage(im,0,0,128,160);
     pair.append(c);
    }
    col.append(pair);const cap=document.createElement('div');cap.className='caption';cap.textContent=crop?'Crown edge; native-resolution crop':'Whole portrait; same display size';col.append(cap);
   }
   document.querySelector('main').append(col);
  }
 },testImages);
 await p.screenshot({path:path.join(root,'alpha-test/background-comparison.png'),fullPage:true});await p.close();
}finally{await browser.close();}
if(alphaOnly)process.exit(0);
fs.writeFileSync(path.join(root,'comparison/crops-and-scales.json'),JSON.stringify({coordinates:'Source pixels; top-left x,y,width,height. Alpha bbox uses max-exclusive coordinates.',normalization:'Crown to blouse cut: bbox of alpha>=128, used only for crop/scale, never alpha thresholding. Original B is opaque and uses manual crown-to-blouse crop. Uniform scale to exactly 256 or 144px figure height; ceil canvas width, centred fractional placement. Chromium high-quality canvas interpolation; RGBA PNG derivatives.',detail_note:'Manual face and eye crop boxes; enlarged evidence, not recovered detail. Original B is only 294x351; its clipped sides/bottom and low-resolution face limit comparisons.',items},null,2)+'\n',{flag:'wx'});
function sheet(name,height,entries){execFileSync(process.execPath,[compare,'--out',path.join(root,'comparison',name),'--height',String(height),...entries],{stdio:'inherit'});}
for(const h of [256,144]){
 sheet(`figure-normalized-${h}.png`,h,items.map(it=>`${it.label}=${root}/comparison/${it.id}-figure-${h}.png`));
 sheet(`owner-comparison-${h}.png`,h,[items[0],items[1],...items.slice(5)].map(it=>`${it.label}=${root}/comparison/${it.id}-figure-${h}.png`));
}
for(const [part,h]of [['face',200],['eyes',100]])sheet(`${part}-detail.png`,h,items.map(it=>`${it.label}=${path.resolve(root,it.source)}@${it[part].join(',')}`));
console.log('Review derivatives and alpha background sheet created. Sources unchanged.');
