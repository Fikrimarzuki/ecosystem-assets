import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { resolve, relative, sep } from 'node:path';
import { approvalErrors, visualDirectionErrors } from './lib/momee-approval.mjs';

const root = resolve(import.meta.dirname, '..');
const manifest = JSON.parse(readFileSync(resolve(root, 'projects/momee/manifest.json'), 'utf8'));
const recovery = JSON.parse(readFileSync(resolve(root, 'projects/momee/recovery.json'), 'utf8'));
const directions = JSON.parse(readFileSync(resolve(root, 'projects/momee/visual-directions.json'), 'utf8'));
const directionIds = directions.directions.map((d) => d.id);
const errors = [];
const fail = (message) => errors.push(message);
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
const validHash = (value) => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);

function file(record, label, allowedFormats) {
  if (!record || typeof record !== 'object') return fail(`${label}: missing file record`);
  const { path, format, width, height, sha256 } = record;
  if (typeof path !== 'string' || !path || path.startsWith('/') || path.split('/').includes('..'))
    return fail(`${label}: unsafe path`);
  if (!allowedFormats.includes(format) || !path.endsWith(`.${format}`)) fail(`${label}: format/extension mismatch`);
  if (!Number.isInteger(width) || width < 1 || !Number.isInteger(height) || height < 1)
    fail(`${label}: invalid dimensions`);
  if (!validHash(sha256)) fail(`${label}: invalid SHA-256`);
  const absolute = resolve(root, path);
  if (relative(root, absolute).startsWith(`..${sep}`)) return fail(`${label}: path escapes repository`);
  let bytes;
  try {
    if (realpathSync(absolute) !== absolute) fail(`${label}: symlink is not allowed`);
    bytes = readFileSync(absolute);
  } catch {
    return fail(`${label}: file is absent`);
  }
  if (validHash(sha256) && hash(bytes) !== sha256) fail(`${label}: SHA-256 mismatch`);
  if (format === 'png') {
    if (bytes.length < 24 || bytes.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a')
      fail(`${label}: invalid PNG header`);
    else if (bytes.readUInt32BE(16) !== width || bytes.readUInt32BE(20) !== height)
      fail(`${label}: PNG dimensions differ from manifest`);
  }
  if (format === 'webp') {
    if (bytes.length < 30 || bytes.toString('ascii', 0, 4) !== 'RIFF' || bytes.toString('ascii', 8, 12) !== 'WEBP')
      fail(`${label}: invalid WebP header`);
    else {
      const variant = bytes.toString('ascii', 12, 16);
      let actual;
      if (variant === 'VP8X') actual = [bytes.readUIntLE(24, 3) + 1, bytes.readUIntLE(27, 3) + 1];
      else if (variant === 'VP8 ') actual = [bytes.readUInt16LE(26) & 0x3fff, bytes.readUInt16LE(28) & 0x3fff];
      else if (variant === 'VP8L' && bytes[20] === 0x2f)
        actual = [(bytes[21] | ((bytes[22] & 0x3f) << 8)) + 1,
          ((bytes[22] >> 6) | (bytes[23] << 2) | ((bytes[24] & 0x0f) << 10)) + 1];
      else fail(`${label}: unsupported WebP variant`);
      if (actual && (actual[0] !== width || actual[1] !== height))
        fail(`${label}: WebP dimensions differ from manifest`);
    }
  }
  if (format === 'svg' && !bytes.toString('utf8', 0, 500).includes('<svg'))
    fail(`${label}: SVG root not found`);
}

if (manifest.schemaVersion !== 1 || manifest.projectId !== 'momee' || !Array.isArray(manifest.assets))
  fail('manifest: invalid root');
const ids = new Set();
let reviewRenders = 0;
for (const asset of manifest.assets ?? []) {
  const label = `asset ${asset.id ?? '<missing id>'}`;
  if (typeof asset.id !== 'string' || !/^[a-z0-9]+(?:[.-][a-z0-9]+)*$/.test(asset.id)) fail(`${label}: invalid ID`);
  if (ids.has(asset.id)) fail(`${label}: duplicate ID`);
  ids.add(asset.id);
  if (typeof asset.category !== 'string' || !asset.category) fail(`${label}: missing category`);
  if (!['Working', 'Candidate', 'Approved'].includes(asset.status)) fail(`${label}: invalid status`);
  file(asset.source, `${label} source`, ['kra', 'svg', 'png', 'psd', 'blend']);
  if (!Array.isArray(asset.exports)) fail(`${label}: exports must be an array`);
  for (const item of asset.exports ?? []) {
    file(item, `${label} export ${item.path}`, ['png', 'webp', 'svg']);
    if (!item.path?.startsWith('projects/momee/exports/')) fail(`${label}: export outside project exports`);
    if (typeof item.runtimeDestination !== 'string' ||
      !item.runtimeDestination.startsWith('apps/web/public/game/calm-chibi-storybook/'))
      fail(`${label}: invalid runtime destination`);
    if (item.width > 2048 || item.height > 2048) fail(`${label}: export exceeds 2048-pixel ceiling`);
    if (item.tier != null && !['@1x', '@2x'].includes(item.tier)) fail(`${label}: invalid export tier`);
  }
  // Review-only renders (studies, sheets): hashed like exports, but never runtime files.
  if (asset.reviewRenders != null && !Array.isArray(asset.reviewRenders)) fail(`${label}: reviewRenders must be an array`);
  for (const item of Array.isArray(asset.reviewRenders) ? asset.reviewRenders : []) {
    file(item, `${label} review render ${item.path}`, ['png', 'webp']);
    if (!item.path?.startsWith('projects/momee/review/')) fail(`${label}: review render outside project review`);
    if ('runtimeDestination' in item) fail(`${label}: review render must not name a runtime destination`);
    reviewRenders++;
  }
  const tiers = Object.fromEntries((asset.exports ?? []).filter((item) => item.tier).map((item) => [item.tier, item]));
  if (tiers['@1x'] && tiers['@2x'] &&
    (tiers['@2x'].width !== tiers['@1x'].width * 2 || tiers['@2x'].height !== tiers['@1x'].height * 2))
    fail(`${label}: @2x dimensions must double @1x`);
  if (!Array.isArray(asset.lineage)) fail(`${label}: lineage must be an array`);
  if (!asset.rights || !['unverified', 'verified', 'restricted'].includes(asset.rights.status) ||
    typeof asset.rights.provenancePath !== 'string') fail(`${label}: incomplete rights/provenance`);
  else {
    const provenance = resolve(root, asset.rights.provenancePath);
    if (relative(root, provenance).startsWith(`..${sep}`)) fail(`${label}: provenance path escapes repository`);
    else { try { readFileSync(provenance); } catch { fail(`${label}: provenance file is absent`); } }
  }
  if (typeof asset.intendedAppUsage !== 'string' || !asset.intendedAppUsage) fail(`${label}: missing app usage`);
  // Visual acceptance, production approval and rights are separate gates (scripts/lib/momee-approval.mjs).
  for (const message of approvalErrors(asset)) fail(`${label}: ${message}`);
  for (const message of visualDirectionErrors(asset, directionIds)) fail(`${label}: ${message}`);
}

if (recovery.schemaVersion !== 1 || !Array.isArray(recovery.files) || !validHash(recovery.sourceManifestSha256))
  fail('recovery: invalid root');
const priorPaths = new Set();
for (const entry of recovery.files ?? []) {
  if (priorPaths.has(entry.previousAppPath)) fail(`recovery: duplicate prior path ${entry.previousAppPath}`);
  priorPaths.add(entry.previousAppPath);
  if (!validHash(entry.expectedSha256) && !validHash(entry.expectedPixelSha256))
    fail(`recovery: invalid expected hash ${entry.previousAppPath}`);
  if (!['hash-matched-in-intake', 'unavailable'].includes(entry.availability))
    fail(`recovery: invalid availability ${entry.previousAppPath}`);
  if (entry.availability === 'hash-matched-in-intake') {
    if (!validHash(entry.expectedSha256)) fail(`recovery: a file match requires file SHA-256 ${entry.previousAppPath}`);
    if (!entry.matchedSharedPath?.startsWith('incoming/momee/'))
      fail(`recovery: invalid matched path ${entry.previousAppPath}`);
    else {
      try {
        const bytes = readFileSync(resolve(root, entry.matchedSharedPath));
        if (hash(bytes) !== entry.expectedSha256) fail(`recovery: hash mismatch ${entry.previousAppPath}`);
      } catch { fail(`recovery: matched file absent ${entry.previousAppPath}`); }
    }
  } else if (entry.matchedSharedPath != null) fail(`recovery: unavailable entry has match ${entry.previousAppPath}`);
}

if (errors.length) {
  for (const error of errors) console.error(error);
  process.exitCode = 1;
} else {
  const matched = recovery.files.filter((entry) => entry.availability === 'hash-matched-in-intake').length;
  console.log(`Momee manifest: ${ids.size} asset(s), ${reviewRenders} review render(s); recovery: ${recovery.files.length} prior paths, ${matched} hash-matched, ${recovery.files.length - matched} unavailable.`);
}
