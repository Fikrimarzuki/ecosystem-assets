import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, renameSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { auditDist } from './verify-web-dist.mjs';
import { generateCatalog, publicAssetUrl } from './lib/catalog.mjs';
import { copyApprovedAssets } from './lib/public-delivery.mjs';
import { PNG } from 'pngjs';
import { createHash } from 'node:crypto';

const catalog = { schemaVersion: 1, assets: [], logicalAssets: [] };
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
function fixture(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'web-dist-audit-'));
  try {
    mkdirSync(join(dir, 'assets'));
    writeFileSync(join(dir, 'index.html'), '<div id="root"></div>');
    writeFileSync(join(dir, 'catalog.json'), JSON.stringify(catalog));
    writeFileSync(join(dir, 'assets/index-test.js'), 'console.log("ready")');
    fn(dir);
  } finally { rmSync(dir, {recursive:true,force:true}); }
}

test('empty public build contains only allowed files', () => fixture(dir => {
  assert.equal(auditDist(dir,catalog,['projects/momee/source/private.kra']).files.length,3);
}));

test('public build audit rejects private binaries and reports', () => fixture(dir => {
  writeFileSync(join(dir,'assets/private.png'),'private');
  assert.throws(() => auditDist(dir,catalog,[]), /forbidden public build file/);
}));

test('public build audit rejects stale catalog and private path leaks', () => fixture(dir => {
  writeFileSync(join(dir,'catalog.json'),JSON.stringify({...catalog,assets:[{id:'unapproved'}]}));
  assert.throws(() => auditDist(dir,catalog,[]), /public catalog differs/);
  writeFileSync(join(dir,'catalog.json'),JSON.stringify(catalog));
  writeFileSync(join(dir,'assets/index-test.js'),'projects/momee/source/private.kra');
  assert.throws(() => auditDist(dir,catalog,['projects/momee/source/private.kra']), /private asset path leaked/);
}));

test('public build audit rejects embedded binary data', () => fixture(dir => {
  writeFileSync(join(dir,'assets/index-test.js'),'const image="data:image/png;base64,AAAA"');
  assert.throws(() => auditDist(dir,catalog,[]), /embedded asset binary/);
}));

test('Vercel rewrites only the known client routes', () => {
  const config = JSON.parse(readFileSync(join(root, 'vercel.json'), 'utf8'));
  assert.equal(config.outputDirectory, 'apps/web/dist');
  assert.equal(config.installCommand, undefined);
  assert.deepEqual(config.rewrites.map(rule => rule.source).sort(), ['/about','/assets/:projectId/:slug','/collections','/collections/:projectId','/explore','/health']);
  assert.ok(config.rewrites.every(rule => rule.destination === '/index.html'));
});

function syntheticRepository(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'ea4-assets-'));
  try {
    const exports = join(dir, 'projects/cv/branding/exports');
    mkdirSync(exports, { recursive: true });
    const png = new PNG({ width: 2, height: 2 });
    png.data.fill(255);
    const pngBytes = PNG.sync.write(png);
    const ico = Buffer.alloc(22 + pngBytes.length);
    ico.writeUInt16LE(1, 2); ico.writeUInt16LE(1, 4); ico[6] = 2; ico[7] = 2;
    ico.writeUInt16LE(1, 10); ico.writeUInt16LE(32, 12); ico.writeUInt32LE(pngBytes.length, 14); ico.writeUInt32LE(22, 18);
    pngBytes.copy(ico, 22);
    writeFileSync(join(exports, 'sample.png'), pngBytes);
    writeFileSync(join(exports, 'sample.svg'), readFileSync(join(root, 'tests/fixtures/approved-icon.svg')));
    writeFileSync(join(exports, 'sample.ico'), ico);
    writeFileSync(join(exports, 'private.png'), pngBytes);
    const config = {schemaVersion:1,roots:['projects'],formats:['png','svg','ico'],excludeDirectories:[]};
    const approved = ['sample.png','sample.svg','sample.ico'].map(name => ({id:`file:projects/cv/branding/exports/${name}`,sha256:createHash('sha256').update(readFileSync(join(exports,name))).digest('hex'),rightsStatus:'verified',approvedBy:'Fixture Owner',approvedOn:'2026-10-27',title:`Fixture ${name}`,description:'Synthetic test artwork',tags:['synthetic','approved']}));
    fn({dir, exports, config, publications:{schemaVersion:1,approved}, pngBytes});
  } finally { rmSync(dir, {recursive:true,force:true}); }
}

test('synthetic approvals deliver exact PNG, SVG, and ICO bytes and public references', () => syntheticRepository(({dir,config,publications}) => {
  const generated = generateCatalog(dir,{config,publications,integrateManifests:false});
  assert.equal(generated.validation.summary.errors,0);
  assert.equal(generated.publicCatalog.assets.length,3);
  assert.ok(generated.publicCatalog.assets.every(asset => asset.url === publicAssetUrl(asset) && asset.title?.startsWith('Fixture')));
  const dist = join(dir,'dist'); mkdirSync(dist);
  writeFileSync(join(dist,'index.html'),'<div id="root"></div>');
  writeFileSync(join(dist,'catalog.json'),JSON.stringify(generated.publicCatalog));
  copyApprovedAssets(dir,generated.publicCatalog,dist);
  assert.equal(auditDist(dist,generated.publicCatalog,generated.internal.assets.filter(asset => asset.publication !== 'public').map(asset => asset.path)).files.length,5);
  assert.ok(!readFileSync(join(dist,'catalog.json'),'utf8').includes('private.png'));
  const published = generated.publicCatalog.assets[0];
  writeFileSync(join(dist,published.url.slice(1)),Buffer.alloc(published.bytes,0x58));
  assert.throws(() => auditDist(dist,generated.publicCatalog,[]), /published hash differs/);
  rmSync(join(dist,published.url.slice(1)));
  assert.throws(() => auditDist(dist,generated.publicCatalog,[]), /approved binary missing/);
  writeFileSync(join(dist,'published/extra.png'),'extra');
  assert.throws(() => auditDist(dist,generated.publicCatalog,[]), /forbidden public build file/);
}));

test('delivery rejects traversal, symlinks, and changed source bytes', () => syntheticRepository(({dir,exports,config,publications}) => {
  const {publicCatalog} = generateCatalog(dir,{config,publications,integrateManifests:false});
  const out = join(dir,'out'); mkdirSync(out);
  assert.throws(() => copyApprovedAssets(dir,{assets:[{...publicCatalog.assets[0],path:'../secret.png'}]},out), /unsafe path|mismatch/);
  const asset = publicCatalog.assets.find(item => item.path.endsWith('sample.svg'));
  rmSync(join(exports,'sample.svg'));
  symlinkSync(join(root,'tests/fixtures/approved-icon.svg'),join(exports,'sample.svg'));
  assert.throws(() => copyApprovedAssets(dir,{assets:[asset]},out), /unsafe source symlink/);
  rmSync(join(exports,'sample.svg'));
  writeFileSync(join(exports,'sample.svg'),Buffer.alloc(asset.bytes,0x58));
  assert.throws(() => copyApprovedAssets(dir,{assets:[asset]},out), /approved source hash changed/);
  renameSync(exports,join(dir,'moved-exports'));
  symlinkSync(join(dir,'moved-exports'),exports);
  assert.throws(() => copyApprovedAssets(dir,{assets:[asset]},out), /unsafe source symlink/);
}));

test('production approval list stays empty and synthetic fixtures are outside inventory', () => {
  const publications = JSON.parse(readFileSync(join(root,'catalog/publications.json'),'utf8'));
  assert.deepEqual(publications.approved,[]);
  const generated = generateCatalog(root);
  assert.equal(generated.validation.summary.errors,0);
  assert.equal(generated.publicCatalog.assets.length,0);
  assert.ok(generated.internal.assets.every(asset => !asset.path.startsWith('tests/fixtures/')));
});
