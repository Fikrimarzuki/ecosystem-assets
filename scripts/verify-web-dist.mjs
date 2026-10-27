import assert from 'node:assert/strict';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateCatalog } from './lib/catalog.mjs';
import { publishedFilename } from './lib/public-delivery.mjs';
import { createHash } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function listFiles(base, current = base) {
  const result = [];
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    const path = join(current, entry.name);
    assert.ok(!entry.isSymbolicLink(), `symlink in public build: ${path}`);
    if (entry.isDirectory()) result.push(...listFiles(base, path));
    else if (entry.isFile()) result.push(relative(base, path).replaceAll('\\', '/'));
    else throw new Error(`unexpected entry in public build: ${path}`);
  }
  return result.sort();
}

export function auditDist(dist, expectedCatalog, privatePaths) {
  assert.ok(existsSync(dist) && lstatSync(dist).isDirectory(), 'web dist is missing');
  const files = listFiles(dist);
  assert.ok(files.includes('index.html'), 'index.html is missing');
  assert.ok(files.includes('catalog.json'), 'catalog.json is missing');
  const expectedBinaries = new Map();
  for (const asset of expectedCatalog.assets) expectedBinaries.set(publishedFilename(asset), asset);
  for (const showcase of expectedCatalog.showcases || []) {
    assert.ok(!/(?:"(?:path|assetId|approvedBy|approvedOn|sourceMetadata)"|file:|(?:projects|incoming|references|shared)\/)/i.test(JSON.stringify(showcase)), `private metadata in public showcase: ${showcase.id}`);
    for (const file of [...showcase.media,...showcase.downloads]) {
      assert.match(file.url, /^\/published\/[a-f0-9]{64}\.[a-z0-9]+$/, 'invalid public media URL');
      assert.equal(file.url.endsWith(`.${file.format}`), true, 'public media format mismatch');
      assert.match(file.sha256, /^[a-f0-9]{64}$/, 'invalid public media hash');
      assert.ok(Number.isSafeInteger(file.bytes) && file.bytes >= 0, 'invalid public media size');
      const filename = file.url.slice(1), prior = expectedBinaries.get(filename);
      if (prior) assert.ok(prior.sha256 === file.sha256 && prior.bytes === file.bytes, `public URL collision: ${filename}`);
      expectedBinaries.set(filename,file);
    }
  }
  for (const file of files) assert.ok(/^(?:index\.html|catalog\.json|assets\/[A-Za-z0-9_-]+\.(?:js|css))$/.test(file) || expectedBinaries.has(file), `forbidden public build file: ${file}`);
  for (const [file, asset] of expectedBinaries) {
    assert.ok(files.includes(file), `approved binary missing: ${file}`);
    const bytes = readFileSync(join(dist, file));
    assert.equal(bytes.length, asset.bytes, `published byte count differs: ${file}`);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256, `published hash differs: ${file}`);
  }
  const catalogText = readFileSync(join(dist, 'catalog.json'), 'utf8');
  const actualCatalog = JSON.parse(catalogText);
  assert.deepEqual(actualCatalog, expectedCatalog, 'public catalog differs from the current allowlist output');
  const text = files.filter(file => /\.(?:html|js|css|json)$/.test(file)).map(file => readFileSync(join(dist, file), 'utf8')).join('\n');
  assert.ok(!/data:(?:image\/(?:png|jpeg|webp|gif|svg\+xml)|model\/|application\/octet-stream)[^\s"']*;base64,/i.test(text), 'embedded asset binary in public build');
  for (const path of privatePaths) assert.ok(!text.includes(path), `private asset path leaked into public build: ${path}`);
  for (const marker of ['sourceMetadata', 'collection-import.json', 'manifest-checksum-conflict', 'validation.json', 'internal.json']) {
    assert.ok(!catalogText.includes(marker), `private catalog marker leaked into public catalog: ${marker}`);
  }
  return { files, bytes: files.reduce((sum, file) => sum + lstatSync(join(dist, file)).size, 0) };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const { internal, publicCatalog, validation } = generateCatalog(root);
    assert.equal(validation.summary.errors, 0, 'catalog validation failed');
    const privatePaths = internal.assets.filter(asset => asset.publication !== 'public').map(asset => asset.path);
    const result = auditDist(join(root, 'apps/web/dist'), publicCatalog, privatePaths);
    console.log(`Public build verified: ${result.files.length} files, ${result.bytes} bytes, ${publicCatalog.showcases.length} showcases`);
  } catch (error) {
    console.error(error.stack || String(error));
    process.exitCode = 1;
  }
}
