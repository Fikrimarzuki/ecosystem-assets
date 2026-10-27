import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { PNG } from 'pngjs';
import { generateCatalog } from './lib/catalog.mjs';
import { copyApprovedAssets } from './lib/public-delivery.mjs';
import { auditDist } from './verify-web-dist.mjs';

const approval = bytes => ({ sha256:createHash('sha256').update(bytes).digest('hex'), rightsStatus:'verified', approvedBy:'Fixture Owner', approvedOn:'2026-10-27' });
const id = path => `file:${path}`;

function fixture(fn) {
  const dir = mkdtempSync(join(tmpdir(),'ea5b-showcase-'));
  try {
    const paths = {
      original:'projects/cv/branding/source/master.png',
      hero:'projects/cv/branding/review/hero.png',
      detail:'projects/cv/branding/review/detail.png',
      unapproved:'projects/cv/branding/review/private.png',
      png:'projects/cv/branding/exports/icon.png',
      svg:'projects/cv/branding/exports/icon.svg',
    };
    const png = new PNG({width:2,height:2}); png.data.fill(255);
    const bytes = {
      original:PNG.sync.write(png),
      hero:PNG.sync.write(png),
      detail:PNG.sync.write(png),
      unapproved:PNG.sync.write(png),
      png:PNG.sync.write(png),
      svg:Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 2"><path fill="#123456" d="M0 0h2v2H0z"/></svg>'),
    };
    for (const [key,path] of Object.entries(paths)) { mkdirSync(join(dir,path,'..'),{recursive:true}); writeFileSync(join(dir,path),bytes[key]); }
    const config = {schemaVersion:1,roots:['projects'],formats:['png','svg'],excludeDirectories:[]};
    const entry = {
      projectId:'cv',slug:'icon',title:'CV Icon',description:'A public description',category:'branding',tags:['identity'],
      showcaseApproval:{approvedBy:'Fixture Owner',approvedOn:'2026-10-27'},
      media:[
        {key:'hero',assetId:id(paths.hero),approval:approval(bytes.hero),caption:'Final view'},
        {key:'detail',assetId:id(paths.detail),approval:approval(bytes.detail),caption:'Design detail'},
      ],
      downloads:[],
    };
    fn({dir,paths,bytes,config,entry});
  } finally { rmSync(dir,{recursive:true,force:true}); }
}

function generate(dir,config,entries) { return generateCatalog(dir,{config,publications:{schemaVersion:1,approved:[],showcases:entries},integrateManifests:false}); }

test('private, showcase, and downloadable states require separate approvals', () => fixture(({dir,paths,bytes,config,entry}) => {
  const empty = generate(dir,config,[]);
  assert.equal(empty.validation.summary.errors,0);
  assert.equal(empty.publicCatalog.showcases.length,0);
  assert.ok(empty.internal.assets.every(asset => asset.publication === 'private'));

  const shown = generate(dir,config,[entry]);
  assert.equal(shown.validation.summary.errors,0);
  assert.equal(shown.publicCatalog.showcases.length,1);
  const publicEntry = shown.publicCatalog.showcases[0];
  assert.equal(publicEntry.publication,'showcase');
  assert.deepEqual(publicEntry.media.map(item => item.key),['hero','detail']);
  assert.deepEqual(publicEntry.media.map(item => item.caption),['Final view','Design detail']);
  assert.deepEqual(publicEntry.downloads,[]);
  assert.equal(shown.deliveries.length,2);
  assert.ok(shown.internal.assets.find(asset => asset.path === paths.original).publication === 'private');
  const serialized = JSON.stringify(publicEntry);
  for (const privateText of [paths.original,paths.unapproved,'assetId','approvedBy','sourceMetadata','Fixture Owner']) assert.ok(!serialized.includes(privateText));

  const dist = join(dir,'dist'); mkdirSync(dist);
  writeFileSync(join(dist,'index.html'),'<div id="root"></div>');
  writeFileSync(join(dist,'catalog.json'),JSON.stringify(shown.publicCatalog));
  copyApprovedAssets(dir,shown.deliveries,dist);
  assert.equal(auditDist(dist,shown.publicCatalog,shown.internal.assets.filter(asset => asset.publication === 'private').map(asset => asset.path)).files.length,4);
  assert.ok(!existsSync(join(dist,paths.original)));
  assert.ok(!existsSync(join(dist,paths.unapproved)));
  const publicPreview = publicEntry.media[0];
  assert.deepEqual(readFileSync(join(dist,publicPreview.url.slice(1))),bytes.hero);
  writeFileSync(join(dist,publicPreview.url.slice(1)),Buffer.from('tampered'));
  assert.throws(() => auditDist(dist,shown.publicCatalog,[]), /published byte count differs|published hash differs/);

  const downloadable = generate(dir,config,[{...entry,downloads:[
    {key:'png',assetId:id(paths.png),approval:approval(bytes.png),label:'PNG'},
    {key:'svg',assetId:id(paths.svg),approval:approval(bytes.svg),label:'SVG'},
  ]}]);
  assert.equal(downloadable.validation.summary.errors,0);
  assert.equal(downloadable.publicCatalog.showcases[0].publication,'downloadable');
  assert.deepEqual(downloadable.publicCatalog.showcases[0].downloads.map(item => item.format),['png','svg']);
  assert.equal(downloadable.deliveries.length,4);
}));

test('preview and download gates reject missing rights, bad hashes, wrong roles, and unsafe SVG', () => fixture(({dir,paths,bytes,config,entry}) => {
  const denied = changed => generate(dir,config,[changed]).validation.issues.map(item => item.code);
  assert.ok(denied({...entry,showcaseApproval:undefined}).includes('invalid-showcase'));
  assert.ok(denied({...entry,media:[{...entry.media[0],approval:{...entry.media[0].approval,sha256:'0'.repeat(64)}}]}).includes('showcase-file-denied'));
  assert.ok(denied({...entry,media:[{...entry.media[0],approval:{...entry.media[0].approval,rightsStatus:'unverified'}}]}).includes('showcase-file-denied'));
  assert.ok(denied({...entry,media:[{key:'source',assetId:id(paths.original),approval:approval(bytes.original)}]}).includes('showcase-file-denied'));
  assert.ok(denied({...entry,downloads:[{key:'source',assetId:id(paths.original),approval:approval(bytes.original)}]}).includes('showcase-file-denied'));
  assert.equal(generate(dir,config,[{...entry,downloads:[{key:'source',assetId:id(paths.original),approval:approval(bytes.original),allowSource:true}]}]).validation.summary.errors,0);
  assert.ok(denied({...entry,downloads:[{key:'png',assetId:id(paths.png),approval:{...approval(bytes.png),sha256:'0'.repeat(64)}}]}).includes('showcase-file-denied'));
  assert.ok(denied({...entry,title:`Private ${paths.original}`}).includes('invalid-showcase'));
  assert.ok(denied({...entry,relatedShowcaseIds:['cv/unpublished']}).includes('invalid-showcase-related'));
  writeFileSync(join(dir,paths.svg),'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>');
  const unsafe = readFileSync(join(dir,paths.svg));
  assert.ok(denied({...entry,downloads:[{key:'svg',assetId:id(paths.svg),approval:approval(unsafe)}]}).includes('showcase-file-denied'));
}));

test('explicit logical group must exist and contain every published file', () => fixture(({dir,config,entry}) => {
  const result = generate(dir,config,[{...entry,logicalAssetId:'group1:cv:icon'}]);
  assert.ok(result.validation.issues.some(item => item.code === 'invalid-showcase-group'));
  assert.equal(result.publicCatalog.showcases.length,0);
}));
