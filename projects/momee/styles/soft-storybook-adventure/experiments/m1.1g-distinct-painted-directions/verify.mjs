import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {decode} from '../../../../../../scripts/lib/png.mjs';
import {measure} from '../m1.1f-painted-redesign/measure.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),repo=path.resolve(root,'../../../../../..');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p)));
const failures=[],check=(ok,message)=>{if(!ok)failures.push(message);};
const before=read('preservation-before.json');
for(const it of before){const p=path.resolve(repo,it.file);check(fs.existsSync(p)&&hash(p)===it.sha256,`Preservation: ${it.file}`);}
const originals=[],presentations=[];
for(const folder of ['candidate-a-classic-storybook','candidate-b-cinematic-2d','candidate-c-handcrafted-gouache']){
 const p=read(`${folder}/provenance.json`),out=path.join(root,p.output.file);
 check(hash(out)===p.output.sha256,`Original hash: ${folder}`);
 check(hash(out)===hash(p.output.returned_original_path),`Returned file copy: ${folder}`);
 check(hash(path.join(root,p.prompt_file))===p.prompt_file_sha256,`Prompt hash: ${folder}`);
 check(fs.readFileSync(path.join(root,p.prompt_file),'utf8')===p.arguments.prompt,`Prompt argument: ${folder}`);
 for(const it of p.inputs)check(hash(path.join(root,it.file))===it.sha256,`Input hash: ${it.file}`);
 const src=decode(fs.readFileSync(out));check(src.width===1122&&src.height===1402,`Original size: ${folder}`);
 originals.push({candidate:p.candidate,file:p.output.file,sha256:hash(out),size:[src.width,src.height],original_copy_identical:true});
 const pr=read(`${folder}/presentation-provenance.json`),file=path.join(root,folder,pr.file),m=measure(file);
 check(m.size.width===1024&&m.size.height===1280,`Presentation size: ${folder}`);
 check(m.minimum_six_percent_empty_left_right_top&&!m.anything_touches_edge,`Presentation clear margins: ${folder}`);
 presentations.push({candidate:p.candidate,file:path.relative(root,file),sha256:hash(file),size:m.size,margins:m.nontransparent_margins_px,all_clear_margins_pass:true});
}
const crops=read('comparison/crops-and-scales.json');
for(const it of crops.items)for(const h of [256,144]){
 const p=decode(fs.readFileSync(path.join(root,'comparison',`${it.id}-figure-${h}.png`)));
 check(p.height===h,`Normalized height: ${it.id}/${h}`);
}
const sheets=['owner-comparison-256.png','owner-comparison-144.png','figure-normalized-256.png','figure-normalized-144.png','face-detail.png','eyes-detail.png'];
const sheetDimensions=sheets.map(file=>{const p=decode(fs.readFileSync(path.join(root,'comparison',file)));return{file:`comparison/${file}`,width:p.width,height:p.height};});
const a=read('alpha-test/measurements.json');
check(a.source_unchanged&&a.unchanged_rgb&&a.protected_edge_changes===0&&a.decode_encode_roundtrip_pixels_identical,'Alpha experiment invariants');
const originalProbe=decode(fs.readFileSync(path.resolve(root,'alpha-test',a.source))),testProbe=decode(fs.readFileSync(path.join(root,'alpha-test/m11f-b-interior-opacity-test.png')));
let rgbChanges=0,lowAlphaChanges=0;
for(let i=0;i<originalProbe.data.length;i+=4){
 for(let c=0;c<3;c++)if(originalProbe.data[i+c]!==testProbe.data[i+c])rgbChanges++;
 if(originalProbe.data[i+3]<240&&originalProbe.data[i+3]!==testProbe.data[i+3])lowAlphaChanges++;
}
check(rgbChanges===0&&lowAlphaChanges===0,'Independent alpha test RGB / low-alpha preservation');
const afterAssets=execFileSync('git',['status','--short'],{cwd:repo,encoding:'utf8'}),afterApp=execFileSync('git',['status','--short'],{cwd:path.resolve(repo,'../app-momee'),encoding:'utf8'});
fs.writeFileSync(path.join(root,'git-status-after-assets.txt'),afterAssets);
fs.writeFileSync(path.join(root,'git-status-after-app.txt'),afterApp);
check(afterApp===fs.readFileSync(path.join(root,'git-status-before-app.txt'),'utf8'),'App git status unchanged');
check(afterAssets===fs.readFileSync(path.join(root,'git-status-before-assets.txt'),'utf8'),'Assets status contains only the same new experiment entry');
const report={checked_at_utc:new Date().toISOString(),project_date:'2026-11-17',preserved_preexisting_files:before.length,preservation_pass:!failures.some(s=>s.startsWith('Preservation:')),originals,presentations,normalized_comparison_subjects:crops.items.length,normalized_figure_heights:[256,144],sheetDimensions,alpha_test:{rgb_changes:rgbChanges,low_alpha_changes:lowAlphaChanges,protected_edge_changes:a.protected_edge_changes,source_unchanged:a.source_unchanged},app_status_unchanged:afterApp===fs.readFileSync(path.join(root,'git-status-before-app.txt'),'utf8'),assets_status:afterAssets,failures,technical_checks_pass:failures.length===0,visual_status:'candidate for owner review; no acceptance claimed; see REVIEW.md'};
fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({preserved:before.length,originals:originals.length,presentations:presentations.length,normalized_subjects:crops.items.length,technical_checks_pass:!failures.length,failures}));
if(failures.length)process.exitCode=1;
