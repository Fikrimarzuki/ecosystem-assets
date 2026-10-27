import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {measure} from '../m1.1f-painted-redesign/measure.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const [key,source]=process.argv.slice(2);
const folder={a:'candidate-a-classic-storybook',b:'candidate-b-cinematic-2d',c:'candidate-c-handcrafted-gouache'}[key];
if(!folder||!source)throw Error('Usage: node capture.mjs a|b|c returned-path');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const original=path.join(root,folder,'generation-01-original.png');
fs.copyFileSync(source,original,fs.constants.COPYFILE_EXCL);
const promptPath=path.join(root,folder,'prompt-01.txt');
const inputs=['b-portrait.png','family-master.png'].map(n=>path.join(root,'inputs',n));
const record={candidate:key,generation:1,captured_at_utc:new Date().toISOString(),project_date:'2026-11-17',project_timezone:'Asia/Jakarta',
 tool:'Codex built-in image_gen.imagegen',intent:'independent generation using identity references',model:'not reported by tool',seed:'not reported by tool',rights:'unverified; no production or rights approval inferred',
 arguments:{prompt:fs.readFileSync(promptPath,'utf8'),referenced_image_paths:inputs,transparent_background:true},
 prompt_file:path.relative(root,promptPath),prompt_file_sha256:hash(promptPath),
 inputs:inputs.map(p=>({file:path.relative(root,p),sha256:hash(p)})),
 output:{returned_original_path:source,file:path.relative(root,original),sha256:hash(original),byte_for_byte_copy_verified:hash(original)===hash(source),operations:'none; original copied unchanged'},
 measurements:measure(original)};
record.measurements.file=path.relative(root,original);
fs.writeFileSync(path.join(root,folder,'provenance.json'),JSON.stringify(record,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({candidate:key,hash:record.output.sha256,size:record.measurements.size,alpha:record.measurements.alpha_histogram_summary}));
