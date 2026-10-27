import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {measure} from './measure.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const folders={a:'candidate-a-refined-b',b:'candidate-b-premium-painted',c:'candidate-c-gouache-adventure'};
const [key,number,source]=process.argv.slice(2),folder=folders[key],nn=String(number).padStart(2,'0');
if(!folder||!source)throw Error('Usage: node capture.mjs a|b|c number generated-original-path');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const dest=path.join(root,folder,'generations',`generation-${nn}-original.png`);
if(fs.existsSync(dest)){if(hash(source)!==hash(dest))throw Error('Existing different original');}
else fs.copyFileSync(source,dest);
const promptFile=path.join(root,folder,'generations',`prompt-${nn}.txt`);
const inputs=Number(number)===1?['b-portrait.png','b-eye.png','gate-a-painted.png','family-master.png'].map(x=>path.join(root,'inputs',x)):[path.join(root,folder,'generations','generation-01-original.png')];
const record={call:Number(number),captured_at_utc:new Date().toISOString(),tool:'Codex built-in image_gen',model:'not recorded',transparent_background:true,prompt:fs.readFileSync(promptFile,'utf8').replace(/\n$/,''),prompt_file:path.relative(root,promptFile),prompt_file_sha256:hash(promptFile),inputs:inputs.map(file=>({file:path.relative(root,file),sha256:hash(file)})),output:{generated_source_path:source,file:path.relative(root,dest),sha256:hash(dest),byte_for_byte_copy_verified:hash(source)===hash(dest)},measurements:measure(dest)};
fs.writeFileSync(path.join(root,folder,'generations',`record-${nn}.json`),JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify({key,call:number,alpha:record.measurements.alpha_histogram_summary,margins:record.measurements.nontransparent_margins_px}));
