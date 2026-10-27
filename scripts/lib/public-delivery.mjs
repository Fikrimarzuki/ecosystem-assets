import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { normalizePath, physicalId, publicAssetUrl } from './catalog.mjs';

export function publishedFilename(asset) {
  assert.equal(asset.id, physicalId(normalizePath(asset.path)), 'public asset ID/path mismatch');
  if (asset.kind === 'preview') assert.equal(asset.role, 'review', 'only curated review media may be previewed');
  else assert.ok(asset.role === 'export' || (asset.role === 'source' && asset.sourceApproved === true), 'download role is not approved');
  assert.equal(asset.publication, 'public', 'asset is not published');
  assert.equal(asset.rightsStatus, 'verified', 'asset rights are not verified');
  assert.match(asset.sha256, /^[a-f0-9]{64}$/, 'invalid approved SHA-256');
  assert.ok(Number.isSafeInteger(asset.bytes) && asset.bytes >= 0, 'invalid approved byte count');
  assert.equal(asset.url, publicAssetUrl(asset), 'public URL does not match asset ID');
  return asset.url.slice(1);
}

function safeSource(root, path) {
  const base = resolve(root);
  assert.ok(lstatSync(base).isDirectory() && !lstatSync(base).isSymbolicLink(), 'unsafe repository root');
  const realBase = realpathSync(base);
  let current = base;
  for (const part of normalizePath(path).split('/')) {
    current = join(current, part);
    assert.ok(!lstatSync(current).isSymbolicLink(), `unsafe source symlink: ${path}`);
  }
  const actual = realpathSync(current);
  assert.ok(actual.startsWith(`${realBase}${sep}`) && relative(realBase, actual).split(sep).join('/') === path, `source escapes repository: ${path}`);
  assert.ok(lstatSync(current).isFile(), `approved source is not a file: ${path}`);
  return current;
}

export function copyApprovedAssets(root, publicCatalog, destination) {
  const filenames = new Set();
  const assets = Array.isArray(publicCatalog) ? publicCatalog : publicCatalog.assets;
  for (const asset of assets) {
    const filename = publishedFilename(asset);
    if (filenames.has(filename)) continue;
    filenames.add(filename);
    const bytes = readFileSync(safeSource(root, asset.path));
    assert.equal(bytes.length, asset.bytes, `approved byte count changed: ${asset.path}`);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256, `approved source hash changed: ${asset.path}`);
    const target = join(destination, filename);
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, bytes, { flag: 'wx' });
  }
  return filenames;
}
