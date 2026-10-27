import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { generateCatalog, normalizePath, physicalId } from './lib/catalog.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const config = { schemaVersion:1, roots:['projects'], formats:['svg','png'], excludeDirectories:['node_modules','catalog-output'] };
const empty = {schemaVersion:1,approved:[]};
const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="10"><rect width="12" height="10"/></svg>';
const svgHash = createHash('sha256').update(svg).digest('hex');

function fixture(files, fn, publications = empty, metadata) {
  const dir = mkdtempSync(join(tmpdir(),'ecosystem-catalog-'));
  try {
    mkdirSync(join(dir,'projects'),{recursive:true});
    for (const [path,content] of Object.entries(files)) { mkdirSync(dirname(join(dir,path)),{recursive:true}); writeFileSync(join(dir,path),content); }
    return fn(generateCatalog(dir,{config,publications,metadata,integrateManifests:false}));
  } finally { rmSync(dir,{recursive:true,force:true}); }
}

test('path normalization and stable physical IDs', () => {
  assert.equal(physicalId('projects/cv/branding/exports/icon.svg'),'file:projects/cv/branding/exports/icon.svg');
  for (const path of ['../secret.svg','projects//icon.svg','/absolute.svg','projects/./icon.svg','projects\\icon.svg']) assert.throws(() => normalizePath(path));
});

test('deterministic output, metadata, exact duplicates, and default deny', () => {
  const files = {'projects/cv/branding/exports/a.svg':svg,'projects/cv/branding/exports/b.svg':svg};
  fixture(files, first => {
    fixture(files, second => assert.deepEqual(first,second));
    assert.equal(first.internal.assets.length,2);
    assert.deepEqual(first.internal.assets[0].dimensions,{width:12,height:10});
    assert.equal(first.publicCatalog.assets.length,0);
    assert.equal(first.validation.issues.filter(x=>x.code==='exact-duplicate').length,1);
  });
});

test('unapproved file cannot enter public catalog', () => fixture({'projects/cv/branding/exports/icon.svg':svg}, result => {
  assert.equal(result.publicCatalog.assets.length,0);
  assert.equal(result.internal.assets[0].publication,'private');
}));

test('duplicate roots produce duplicate ID and path errors', () => {
  const duplicateConfig = {...config,roots:['projects','projects']};
  const dir = mkdtempSync(join(tmpdir(),'ecosystem-catalog-'));
  try {
    mkdirSync(join(dir,'projects/cv/branding/exports'),{recursive:true});
    writeFileSync(join(dir,'projects/cv/branding/exports/icon.svg'),svg);
    const r = generateCatalog(dir,{config:duplicateConfig,publications:empty,integrateManifests:false});
    assert.ok(r.validation.issues.some(x=>x.code==='duplicate-id'));
    assert.ok(r.validation.issues.some(x=>x.code==='duplicate-path'));
  } finally { rmSync(dir,{recursive:true,force:true}); }
});

test('publication requires export role, verified rights, and explicit approver', () => {
  const files = {'projects/cv/branding/exports/icon.svg':svg,'projects/cv/branding/source/icon.svg':svg};
  const exportId = physicalId('projects/cv/branding/exports/icon.svg');
  const sourceId = physicalId('projects/cv/branding/source/icon.svg');
  fixture(files, r => {
    assert.equal(r.publicCatalog.assets.length,0);
    assert.ok(r.validation.issues.some(x=>x.code==='publication-rights-unresolved'));
    assert.ok(r.validation.issues.some(x=>x.code==='publication-role-denied'));
    assert.ok(r.validation.issues.some(x=>x.code==='invalid-publication-reference'));
  },{schemaVersion:1,approved:[{id:exportId,rightsStatus:'unknown',approvedBy:'Owner',approvedOn:'2026-10-27'},{id:sourceId,rightsStatus:'verified',approvedBy:'Owner',approvedOn:'2026-10-27'},{id:'file:missing.svg',rightsStatus:'verified',approvedBy:'Owner',approvedOn:'2026-10-27'}]});
});

test('public projection excludes private metadata and private records', () => {
  const approved = physicalId('projects/cv/branding/exports/icon.svg');
  const secret = physicalId('projects/cv/branding/source/secret.svg');
  fixture({'projects/cv/branding/exports/icon.svg':svg,'projects/cv/branding/source/secret.svg':svg}, r => {
    assert.equal(r.publicCatalog.assets.length,1);
    assert.equal(r.internal.assets.find(x=>x.id===approved).title,'Private editorial title');
    assert.deepEqual(r.internal.assets.find(x=>x.id===approved).relatedAssetIds,[secret]);
    const encoded = JSON.stringify(r.publicCatalog);
    assert.ok(!encoded.includes('secret.svg'));
    assert.ok(!encoded.includes('Private editorial title'));
    assert.ok(!encoded.includes('sourceMetadata'));
    assert.ok(!encoded.includes('approvedBy'));
    assert.equal(r.publicCatalog.assets[0].rightsStatus,'verified');
  },{schemaVersion:1,approved:[{id:approved,sha256:svgHash,rightsStatus:'verified',approvedBy:'Owner',approvedOn:'2026-10-27'}]},{schemaVersion:1,assets:[{id:approved,title:'Private editorial title',relatedAssetIds:[secret]}]});
});

test('approval pins exact export bytes', () => {
  const id = physicalId('projects/cv/branding/exports/icon.svg');
  fixture({'projects/cv/branding/exports/icon.svg':svg}, r => {
    assert.equal(r.publicCatalog.assets.length,0);
    assert.ok(r.validation.issues.some(x => x.code === 'publication-hash-conflict'));
  },{schemaVersion:1,approved:[{id,sha256:'0'.repeat(64),rightsStatus:'verified',approvedBy:'Owner',approvedOn:'2026-10-27'}]});
});

test('editorial metadata rejects unknown asset relationships', () => {
  const id = physicalId('projects/cv/branding/exports/icon.svg');
  fixture({'projects/cv/branding/exports/icon.svg':svg}, r => {
    assert.ok(r.validation.issues.some(x=>x.code==='invalid-related-asset'));
  },empty,{schemaVersion:1,assets:[{id,relatedAssetIds:['file:missing.svg']}]});
});

test('malformed SVG and unavailable Git LFS content are reported', () => {
  const pointer = 'version https://git-lfs.github.com/spec/v1\noid sha256:'+'0'.repeat(64)+'\nsize 24\n';
  fixture({'projects/cv/branding/source/bad.svg':'<svg><path d="<!--bad-->"/></svg>','projects/cv/branding/exports/pointer.png':pointer}, r => {
    assert.ok(r.validation.issues.some(x=>x.code==='invalid-asset' && x.path.endsWith('bad.svg')));
    assert.ok(r.validation.issues.some(x=>x.code==='lfs-unavailable' && x.path.endsWith('pointer.png')));
    assert.ok(!r.internal.assets.some(x=>x.path.endsWith('pointer.png')));
  });
});

test('a malformed export cannot be approved into the public catalog', () => {
  const path = 'projects/cv/branding/exports/bad.svg';
  fixture({[path]:'<svg><path d="<!--bad-->"/></svg>'}, r => {
    assert.equal(r.publicCatalog.assets.length,0);
    assert.ok(r.validation.issues.some(x=>x.code==='publication-invalid-asset'));
  },{schemaVersion:1,approved:[{id:physicalId(path),rightsStatus:'verified',approvedBy:'Owner',approvedOn:'2026-10-27'}]});
});

test('unsafe symlinks are skipped and unsupported asset-like formats are reported', () => {
  const dir = mkdtempSync(join(tmpdir(),'ecosystem-catalog-'));
  try {
    mkdirSync(join(dir,'projects/cv'),{recursive:true});
    writeFileSync(join(dir,'projects/cv/draft.psd'),'not a catalog format');
    symlinkSync('/etc/hosts',join(dir,'projects/cv/linked.svg'));
    const r = generateCatalog(dir,{config,publications:empty,integrateManifests:false});
    assert.equal(r.internal.assets.length,0);
    assert.ok(r.validation.issues.some(x=>x.code==='symlink-skipped'));
    assert.ok(r.validation.issues.some(x=>x.code==='unsupported-format'));
  } finally { rmSync(dir,{recursive:true,force:true}); }
});

test('existing manifests map without changing legacy IDs or publishing Momee', () => {
  const r = generateCatalog(root);
  assert.equal(r.validation.summary.assets,849); // 794 + 27 Links M1.5 + 28 Templates M1.3 branding files (candidates, unpublished)
  assert.equal(r.internal.assets.filter(x=>x.path.startsWith('projects/links/')).length,27);
  assert.equal(r.internal.assets.filter(x=>x.path.startsWith('projects/templates/')).length,28);
  assert.equal(r.validation.summary.errors,0);
  assert.equal(r.publicCatalog.assets.length,0);
  assert.ok(r.internal.logicalAssets.some(x=>x.id==='momee:candidate.boy-3quarter-v1' && x.legacyId==='candidate.boy-3quarter-v1'));
  assert.equal(r.internal.logicalAssets.filter(x=>x.id.startsWith('group1:')).length,7);
  const momee = r.internal.assets.find(x=>x.path==='incoming/momee/local-assets/m0.3c.1/boy/boy-3quarter-candidate-v1.png');
  assert.equal(momee.rightsStatus,'unverified');
  assert.ok(momee.sourceMetadata.import);
  assert.ok(momee.sourceMetadata.momee);
  assert.ok(r.validation.issues.some(x=>x.code==='invalid-asset' && x.path.endsWith('mom-head-template.svg')));
});

test('Momee remains blocked even with a forged rights assertion', () => {
  const id = physicalId('projects/momee/exports/rooms/bedroom/pillow-unmade.v1.@1x.png');
  const r = generateCatalog(root,{publications:{schemaVersion:1,approved:[{id,rightsStatus:'verified',approvedBy:'Owner',approvedOn:'2026-10-27'}]}});
  assert.equal(r.publicCatalog.assets.length,0);
  assert.ok(r.validation.issues.some(x=>x.code==='publication-role-denied'));
});
