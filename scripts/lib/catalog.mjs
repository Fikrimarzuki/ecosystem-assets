import { createHash } from 'node:crypto';
import { existsSync, lstatSync, readFileSync, readdirSync } from 'node:fs';
import { extname, join, posix, resolve } from 'node:path';
import { optimize } from 'svgo';

export const SCHEMA_VERSION = 1;
const ROLES = new Set(['source', 'export', 'candidate', 'review', 'reference', 'legacy']);
const RIGHTS = new Set(['unknown', 'unverified', 'verified', 'restricted']);
const ASSET_LIKE = new Set(['svg', 'png', 'jpg', 'jpeg', 'webp', 'gif', 'avif', 'ico', 'glb', 'gltf', 'blend', 'fbx', 'kra', 'webm', 'psd', 'obj', 'mtl', 'tif', 'tiff', 'exr', 'hdr', 'wav', 'mp3', 'mp4', 'ase', 'aseprite']);

export function normalizePath(input) {
  if (typeof input !== 'string' || !input || input.includes('\\') || input.includes('\0') || input.startsWith('/')) throw new Error(`unsafe path: ${input}`);
  const parts = input.split('/');
  if (parts.some(part => !part || part === '.' || part === '..') || posix.normalize(input) !== input) throw new Error(`unsafe path: ${input}`);
  return input;
}

export function physicalId(path) { return `file:${normalizePath(path)}`; }
export function publicAssetUrl(asset) {
  if (asset.id !== physicalId(asset.path) || !/^[a-z0-9]+$/.test(asset.format) || extname(asset.path).slice(1).toLowerCase() !== asset.format) throw new Error(`invalid public asset URL input: ${asset.path}`);
  return `/published/${createHash('sha256').update(asset.id).digest('hex')}.${asset.format}`;
}

function issue(issues, severity, code, path, message) { issues.push({ severity, code, path, message }); }
function readJson(root, path) { return JSON.parse(readFileSync(join(root, normalizePath(path)), 'utf8')); }
function compareStrings(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function sortByPath(a, b) { return compareStrings(a.path, b.path); }

function inferRole(path) {
  const parts = path.split('/');
  if (parts[0] === 'references') return 'reference';
  if (parts.includes('review') || parts.includes('previews') || parts.includes('automation') || parts.includes('inspection') || parts.includes('checks')) return 'review';
  if (parts[0] === 'incoming' || parts.includes('candidates') || parts.includes('concepts')) return 'candidate';
  if (parts.includes('exports')) return 'export';
  if (parts.includes('source')) return 'source';
  return 'legacy';
}

function inferCategory(path) {
  const parts = path.split('/');
  if (parts.includes('branding')) return 'branding';
  if (parts.includes('characters') || parts.includes('astronaut') || parts.includes('explorer')) return 'character';
  if (parts.includes('planets') || parts.includes('spacecraft') || parts.includes('bedroom') || parts.includes('rooms')) return 'environment';
  if (parts.includes('automation') || parts.includes('inspection')) return 'diagnostic';
  return 'uncategorized';
}

function projectId(path) {
  const parts = path.split('/');
  if (parts[0] === 'projects' || parts[0] === 'incoming') return parts[1];
  return 'shared';
}

function svgDimensions(text) {
  const svg = text.match(/<svg\b[^>]*>/i)?.[0];
  if (!svg) return undefined;
  const attr = name => svg.match(new RegExp(`\\b${name}=["']([^"']+)["']`, 'i'))?.[1];
  const width = Number(attr('width')); const height = Number(attr('height'));
  if (width > 0 && height > 0) return { width, height };
  const box = attr('viewBox')?.trim().split(/[\s,]+/).map(Number);
  if (box?.length === 4 && box[2] > 0 && box[3] > 0) return { width: box[2], height: box[3] };
  return undefined;
}

// SVGO parses SVG structure, while this guard rejects XML comments inside quoted attributes,
// which its parser otherwise accepts and which strict XML renderers reject.
function svgHasCommentInAttribute(text) {
  let inTag = false, quote = '';
  for (let i = 0; i < text.length; i++) {
    if (!inTag && text.startsWith('<!--', i)) { const end = text.indexOf('-->', i + 4); if (end < 0) return true; i = end + 2; continue; }
    const c = text[i];
    if (!inTag) { if (c === '<') inTag = true; continue; }
    if (quote) { if (text.startsWith('<!--', i)) return true; if (c === quote) quote = ''; continue; }
    if (c === '"' || c === "'") quote = c;
    else if (c === '>') inTag = false;
  }
  return Boolean(quote);
}

function jpegDimensions(bytes) {
  if (bytes[0] !== 0xff || bytes[1] !== 0xd8) return undefined;
  for (let i = 2; i + 9 < bytes.length;) {
    if (bytes[i] !== 0xff) break;
    const marker = bytes[i + 1];
    if (marker === 0xd9 || marker === 0xda) break;
    const length = bytes.readUInt16BE(i + 2);
    if (length < 2) break;
    if ([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker)) return { width: bytes.readUInt16BE(i + 7), height: bytes.readUInt16BE(i + 5) };
    i += 2 + length;
  }
  return undefined;
}

function inspect(bytes, format, path, issues) {
  if (bytes.subarray(0, 43).toString('utf8').startsWith('version https://git-lfs.github.com/spec/v1')) {
    issue(issues, 'error', 'lfs-unavailable', path, 'Git LFS pointer found; fetch content outside catalog generation');
    return { available: false };
  }
  const result = { available: true };
  try {
    if (format === 'png') {
      if (bytes.length < 24 || !bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])) || bytes.toString('ascii',12,16) !== 'IHDR') throw new Error('invalid PNG header');
      result.dimensions = { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
      if (!result.dimensions.width || !result.dimensions.height) throw new Error('invalid PNG dimensions');
    } else if (format === 'svg') {
      const text = bytes.toString('utf8');
      if (svgHasCommentInAttribute(text)) throw new Error('malformed XML attribute or comment');
      optimize(text, { path, plugins: [] });
      result.dimensions = svgDimensions(text);
    } else if (format === 'gif') {
      if (bytes.length < 10 || !['GIF87a','GIF89a'].includes(bytes.toString('ascii',0,6))) throw new Error('invalid GIF header');
      result.dimensions = { width: bytes.readUInt16LE(6), height: bytes.readUInt16LE(8) };
    } else if (format === 'webp') {
      if (bytes.length < 30 || bytes.toString('ascii',0,4) !== 'RIFF' || bytes.toString('ascii',8,12) !== 'WEBP') throw new Error('invalid WebP header');
      const kind = bytes.toString('ascii',12,16);
      if (kind === 'VP8X') result.dimensions = {width:bytes.readUIntLE(24,3)+1,height:bytes.readUIntLE(27,3)+1};
      else if (kind === 'VP8 ') result.dimensions = {width:bytes.readUInt16LE(26)&0x3fff,height:bytes.readUInt16LE(28)&0x3fff};
      else if (kind === 'VP8L' && bytes[20] === 0x2f) result.dimensions = {width:(bytes[21]|((bytes[22]&0x3f)<<8))+1,height:((bytes[22]>>6)|(bytes[23]<<2)|((bytes[24]&0x0f)<<10))+1};
      else throw new Error('unsupported WebP variant');
    } else if (format === 'avif') {
      if (bytes.length < 16 || bytes.toString('ascii',4,8) !== 'ftyp' || !['avif','avis'].includes(bytes.toString('ascii',8,12))) throw new Error('invalid AVIF header');
    } else if (format === 'jpg' || format === 'jpeg') {
      result.dimensions = jpegDimensions(bytes);
      if (!result.dimensions) throw new Error('invalid or unsupported JPEG structure');
    } else if (format === 'glb') {
      if (bytes.toString('ascii',0,4) !== 'glTF' || bytes.readUInt32LE(8) !== bytes.length) throw new Error('invalid GLB header or length');
    } else if (format === 'gltf') {
      const gltf = JSON.parse(bytes.toString('utf8'));
      if (gltf.asset?.version !== '2.0') throw new Error('unsupported glTF version');
    } else if (format === 'blend' && bytes.toString('ascii',0,7) !== 'BLENDER' && !bytes.subarray(0,4).equals(Buffer.from([0x28,0xb5,0x2f,0xfd]))) throw new Error('invalid Blender or compressed Blender header');
    else if (format === 'kra' && bytes.toString('ascii',0,2) !== 'PK') throw new Error('invalid Krita archive header');
    else if (format === 'webm' && !bytes.subarray(0,4).equals(Buffer.from([0x1a,0x45,0xdf,0xa3]))) throw new Error('invalid WebM header');
    else if (format === 'fbx' && !bytes.toString('ascii',0,20).startsWith('Kaydara FBX Binary') && !bytes.toString('ascii',0,30).includes('FBX')) throw new Error('invalid FBX header');
    else if (format === 'ico') {
      if (bytes.length < 22 || bytes.readUInt16LE(0) !== 0 || bytes.readUInt16LE(2) !== 1 || bytes.readUInt16LE(4) < 1) throw new Error('invalid ICO header');
      result.dimensions = {width:bytes[6] || 256,height:bytes[7] || 256};
    }
  } catch (error) {
    issue(issues, 'warning', 'invalid-asset', path, error.message);
  }
  return result;
}

function walk(root, relative, config, paths, issues) {
  const absolute = join(root, relative);
  if (!existsSync(absolute)) { issue(issues, 'error', 'missing-root', relative, 'configured root is missing'); return; }
  if (lstatSync(absolute).isSymbolicLink()) { issue(issues, 'error', 'unsafe-root', relative, 'configured root is a symlink'); return; }
  for (const entry of readdirSync(absolute, { withFileTypes: true }).sort((a,b) => compareStrings(a.name,b.name))) {
    const path = `${relative}/${entry.name}`;
    if (entry.isSymbolicLink()) { issue(issues, 'warning', 'symlink-skipped', path, 'symlink was not followed'); continue; }
    if (entry.isDirectory()) { if (!config.excludeDirectories.includes(entry.name)) walk(root, path, config, paths, issues); continue; }
    if (!entry.isFile()) continue;
    const format = extname(entry.name).slice(1).toLowerCase();
    if (config.formats.includes(format)) paths.push(path);
    else if (ASSET_LIKE.has(format)) issue(issues, 'warning', 'unsupported-format', path, `asset-like format .${format} is not configured`);
  }
}

function addLogical(logical, pathMap, id, projectId, paths, extra, issues) {
  const ids = [...new Set(paths.map(p => {
    try { return pathMap.get(normalizePath(p))?.id; }
    catch { issue(issues, 'error', 'unsafe-manifest-path', p, 'manifest path is unsafe'); return undefined; }
  }).filter(Boolean))].sort();
  if (!ids.length) return;
  if (logical.has(id)) { issue(issues, 'error', 'duplicate-logical-id', id, 'logical ID appears more than once'); return; }
  logical.set(id, { id, projectId, physicalAssetIds: ids, ...extra });
  for (const aid of ids) pathMap.get(aid.slice(5)).logicalAssetIds.push(id);
}

function integrateMomee(root, pathMap, logical, issues) {
  const source = 'projects/momee/manifest.json'; const manifest = readJson(root, source);
  if (manifest.schemaVersion !== 1 || manifest.projectId !== 'momee' || !Array.isArray(manifest.assets)) { issue(issues,'error','invalid-momee-manifest',source,'unsupported manifest'); return; }
  const seen = new Set();
  for (const item of manifest.assets) {
    if (!item.id || seen.has(item.id)) { issue(issues,'error','duplicate-momee-id',source,`duplicate or missing ID ${item.id}`); continue; }
    seen.add(item.id);
    const refs = [item.source, ...(item.exports || []), ...(item.reviewRenders || [])].filter(x => x?.path);
    for (const ref of refs) {
      let path; try { path = normalizePath(ref.path); } catch { issue(issues,'error','unsafe-manifest-path',source,`unsafe path ${ref.path}`); continue; }
      const record = pathMap.get(path);
      if (!record) { issue(issues,'error','missing-manifest-asset',path,`referenced by Momee ${item.id}`); continue; }
      if (ref.sha256 && ref.sha256 !== record.sha256) issue(issues,'warning','manifest-checksum-conflict',path,`Momee ${item.id} checksum differs`);
      if (ref.width && ref.height && record.dimensions && (ref.width !== record.dimensions.width || ref.height !== record.dimensions.height)) issue(issues,'warning','manifest-dimensions-conflict',path,`Momee ${item.id} dimensions differ`);
      if (item.category && record.category !== item.category && record.category !== 'uncategorized' && record.sourceMetadata?.momee?.category && record.sourceMetadata.momee.category !== item.category) issue(issues,'warning','manifest-category-conflict',path,`Momee categories disagree`);
      if (item.category) record.category = item.category;
      const status = item.rights?.status || 'unknown';
      if (RIGHTS.has(status) && status !== 'verified') record.rightsStatus = status;
      record.sourceMetadata ??= {}; record.sourceMetadata.momee ??= { manifest: source, ids: [], status: [], category: item.category };
      if (!record.sourceMetadata.momee.ids.includes(item.id)) record.sourceMetadata.momee.ids.push(item.id);
      if (!record.sourceMetadata.momee.status.includes(item.status)) record.sourceMetadata.momee.status.push(item.status);
    }
    addLogical(logical, pathMap, `momee:${item.id}`, 'momee', refs.map(x => x.path), { legacyId: item.id, status: item.status, category: item.category }, issues);
  }
}

function integrateImports(root, pathMap, issues) {
  const source = 'docs/collection-import.json'; const manifest = readJson(root, source);
  if (manifest.schemaVersion !== 1 || manifest.algorithm !== 'sha256' || !Array.isArray(manifest.collections)) { issue(issues,'error','invalid-import-manifest',source,'unsupported import manifest'); return; }
  for (const collection of manifest.collections) for (const file of collection.files || []) {
    let path; try { path = normalizePath(`${collection.destination}/${file.path}`); } catch { issue(issues,'error','unsafe-manifest-path',source,`unsafe import path ${file.path}`); continue; }
    const record = pathMap.get(path);
    if (!record) { if (!existsSync(join(root,path))) issue(issues,'error','missing-import-file',path,'import snapshot file is missing'); continue; }
    record.sourceMetadata ??= {}; record.sourceMetadata.import = { manifest: source, collection: collection.source };
    if (record.sha256 !== file.sha256 || record.bytes !== file.bytes) issue(issues,'warning','import-snapshot-conflict',path,'current bytes differ from import snapshot');
  }
}

function integrateGroup1(root, pathMap, logical, issues) {
  const source = 'docs/group1-integration-manifest.md'; const text = readFileSync(join(root, source),'utf8');
  const sections = text.split(/^## /m).slice(1).map(chunk => {
    const match = chunk.match(/^[^\n]+ \(`([A-Za-z][A-Za-z0-9]*)`\)\n/);
    return match ? [null, match[1], chunk.slice(match[0].length)] : null;
  }).filter(Boolean);
  if (sections.length !== 7) issue(issues,'warning','group1-mapping-incomplete',source,`expected 7 project sections, found ${sections.length}`);
  for (const section of sections) {
    const id = section[1]; const body = section[2];
    const src = body.match(/^\| Source SVG masters \| `([^`]+)`/m)?.[1];
    const exp = body.match(/^\| Exports \| `([^`]+)`/m)?.[1];
    const preview = body.match(/^\| Review sheet \| `([^`]+)`/m)?.[1];
    const prefixes = [src,exp].filter(Boolean); const paths = [...pathMap.keys()].filter(p => prefixes.some(prefix => p.startsWith(prefix)) || p === preview);
    if (!src || !exp || !paths.length) issue(issues,'warning','group1-mapping-incomplete',source,`incomplete mapping for ${id}`);
    for (const path of paths) { const record = pathMap.get(path); record.sourceMetadata ??= {}; record.sourceMetadata.group1 = { document: source }; }
    addLogical(logical,pathMap,`group1:${id}:icon`,id,paths,{ category:'branding' },issues);
  }
}

function integrateEditorial(root, pathMap, issues, supplied) {
  const source = 'catalog/metadata.json';
  const metadata = supplied ?? readJson(root, source);
  if (metadata.schemaVersion !== 1 || !Array.isArray(metadata.assets)) { issue(issues,'error','invalid-editorial-metadata',source,'expected schemaVersion 1 and assets array'); return; }
  const byId = new Map([...pathMap.values()].map(asset => [asset.id,asset]));
  const seen = new Set();
  for (const item of metadata.assets) {
    if (!item || typeof item.id !== 'string' || seen.has(item.id)) { issue(issues,'error','duplicate-editorial-id',source,`invalid or repeated ID ${item?.id}`); continue; }
    seen.add(item.id);
    const asset = byId.get(item.id);
    if (!asset) { issue(issues,'error','invalid-editorial-reference',source,`unknown asset ${item.id}`); continue; }
    let valid = true;
    for (const field of ['title','description','version','category']) if (item[field] !== undefined && (typeof item[field] !== 'string' || !item[field].trim())) valid = false;
    for (const field of ['tags','relatedAssetIds']) if (item[field] !== undefined && (!Array.isArray(item[field]) || !item[field].every(x => typeof x === 'string' && x.length > 0))) valid = false;
    if (!valid) { issue(issues,'error','invalid-editorial-record',source,`invalid fields for ${item.id}`); continue; }
    for (const id of item.relatedAssetIds || []) if (!byId.has(id)) issue(issues,'error','invalid-related-asset',source,`${item.id} references unknown ${id}`);
    for (const field of ['title','description','tags','version','category','relatedAssetIds']) if (item[field] !== undefined) asset[field] = item[field];
  }
}

function validateRecords(assets, logical, issues) {
  const ids = new Set(); const paths = new Set();
  for (const a of assets) {
    if (ids.has(a.id)) issue(issues,'error','duplicate-id',a.path,`duplicate ${a.id}`); ids.add(a.id);
    if (paths.has(a.path)) issue(issues,'error','duplicate-path',a.path,'duplicate physical path'); paths.add(a.path);
    try { normalizePath(a.path); } catch { issue(issues,'error','unsafe-path',a.path,'asset path is unsafe'); }
    if (!a.id || !a.projectId || !a.category || !a.format || !ROLES.has(a.role) || !RIGHTS.has(a.rightsStatus) || a.bytes < 0 || !/^[a-f0-9]{64}$/.test(a.sha256)) issue(issues,'error','invalid-record',a.path,'required catalog field is invalid or missing');
    if (a.category === 'uncategorized') issue(issues,'warning','missing-category',a.path,'category is not established');
  }
  for (const group of logical.values()) for (const id of group.physicalAssetIds) if (!ids.has(id)) issue(issues,'error','invalid-relation',group.id,`missing physical asset ${id}`);
}

function applyPublications(root, assets, logical, issues, publications) {
  const source = 'catalog/publications.json'; const list = publications ?? readJson(root, source);
  if (list.schemaVersion !== 1 || !Array.isArray(list.approved)) { issue(issues,'error','invalid-publications',source,'expected schemaVersion 1 and approved array'); return {schemaVersion:1,assets:[],logicalAssets:[]}; }
  const byId = new Map(assets.map(a => [a.id,a])); const seen = new Set(); const publicAssets = [];
  for (const approval of list.approved) {
    const id = approval?.id;
    if (typeof id !== 'string' || seen.has(id)) { issue(issues,'error','duplicate-publication',source,`invalid or repeated approval ID ${id}`); continue; }
    seen.add(id);
    const asset = byId.get(id);
    if (!asset) { issue(issues,'error','invalid-publication-reference',source,`unknown asset ${id}`); continue; }
    if (asset.role !== 'export' || asset.path.startsWith('projects/momee/') || asset.path.startsWith('incoming/momee/')) { issue(issues,'error','publication-role-denied',asset.path,'only eligible exports may be published; Momee is blocked'); continue; }
    if (issues.some(x => x.path === asset.path && x.code === 'invalid-asset') || !safePublicSvg(root,asset)) { issue(issues,'error','publication-invalid-asset',asset.path,'invalid or unsafe asset cannot be published'); continue; }
    if (approval.rightsStatus !== 'verified' || typeof approval.approvedBy !== 'string' || !approval.approvedBy.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(approval.approvedOn || '')) { issue(issues,'error','publication-rights-unresolved',asset.path,'verified rights, approver, and approval date are required'); continue; }
    if (approval.sha256 !== asset.sha256) { issue(issues,'error','publication-hash-conflict',asset.path,'approval SHA-256 must match the current export bytes'); continue; }
    if (asset.rightsStatus === 'restricted' || asset.rightsStatus === 'unverified') { issue(issues,'error','publication-rights-conflict',asset.path,'asset manifest reports unresolved or restricted rights'); continue; }
    const publicCopy = {};
    let metadataValid = true;
    for (const field of ['title', 'description']) {
      if (approval[field] !== undefined) {
        if (!publicText(approval[field],500)) metadataValid = false;
        else publicCopy[field] = approval[field].trim();
      }
    }
    if (approval.tags !== undefined) {
      if (!Array.isArray(approval.tags) || approval.tags.length > 20 || !approval.tags.every(tag => publicText(tag,50))) metadataValid = false;
      else publicCopy.tags = [...new Set(approval.tags.map(tag => tag.trim()))];
    }
    if (!metadataValid) { issue(issues,'error','publication-metadata-invalid',asset.path,'public title, description, or tags are invalid'); continue; }
    asset.publication = 'public'; asset.rightsStatus = 'verified';
    const { id: aid, projectId, path, role, category, format, bytes, sha256, publication, rightsStatus, dimensions } = asset;
    publicAssets.push({ id:aid, projectId, path, role, category, format, bytes, sha256, publication, rightsStatus, url:publicAssetUrl(asset), ...publicCopy, ...(dimensions && {dimensions}) });
  }
  publicAssets.sort(sortByPath);
  const publicIds = new Set(publicAssets.map(x => x.id));
  const publicLogical = [...logical.values()].map(group => ({ id:group.id, projectId:group.projectId, physicalAssetIds:group.physicalAssetIds.filter(id => publicIds.has(id)) })).filter(group => group.physicalAssetIds.length).sort((a,b)=>compareStrings(a.id,b.id));
  return {schemaVersion:1,assets:publicAssets,logicalAssets:publicLogical};
}

const PREVIEW_FORMATS = new Set(['png','jpg','jpeg','webp','gif','avif','ico','svg']);
const PUBLIC_TEXT_LIMITS = {title:120, description:800, category:80, caption:240, label:80};
const PRIVATE_TEXT = /(?:file:|(?:projects|incoming|references|shared|catalog-output)\/|sourceMetadata|\.\.[/\\])/i;
function publicText(value, max) { return typeof value === 'string' && value.trim().length > 0 && value.length <= max && !PRIVATE_TEXT.test(value); }
function approvalValid(approval, asset) {
  return approval && approval.sha256 === asset.sha256 && approval.rightsStatus === 'verified' &&
    typeof approval.approvedBy === 'string' && approval.approvedBy.trim() && /^\d{4}-\d{2}-\d{2}$/.test(approval.approvedOn || '') &&
    !['restricted','unverified'].includes(asset.rightsStatus);
}
function safePublicSvg(root, asset) {
  if (asset.format !== 'svg') return true;
  const svg = readFileSync(join(root, asset.path), 'utf8');
  return !/<script\b|<foreignObject\b|<image\b|<metadata\b|<!DOCTYPE|<\?xml-stylesheet|\bon[a-z]+\s*=|\b(?:href|xlink:href)\s*=|@import|url\(\s*['"]?(?!#)/i.test(svg);
}

function applyShowcases(root, assets, logical, issues, list) {
  const source = 'catalog/publications.json';
  if (list?.showcases !== undefined && !Array.isArray(list.showcases)) { issue(issues,'error','invalid-showcases',source,'showcases must be an array'); return {showcases:[],deliveries:[]}; }
  const byId = new Map(assets.map(asset => [asset.id,asset]));
  const publicShowcases = [], deliveries = [], seen = new Set();
  for (const entry of list?.showcases || []) {
    const project = entry?.projectId, slug = entry?.slug;
    const id = `${project}/${slug}`;
    if (typeof project !== 'string' || !/^[A-Za-z0-9_-]+$/.test(project) || typeof slug !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || seen.has(id)) { issue(issues,'error','invalid-showcase-id',source,`invalid or repeated showcase ${id}`); continue; }
    seen.add(id);
    if (!publicText(entry.title,PUBLIC_TEXT_LIMITS.title) || !publicText(entry.description,PUBLIC_TEXT_LIMITS.description) || !publicText(entry.category,PUBLIC_TEXT_LIMITS.category) ||
      (entry.tags !== undefined && (!Array.isArray(entry.tags) || entry.tags.length > 20 || !entry.tags.every(tag => publicText(tag,50)))) ||
      !entry.showcaseApproval || typeof entry.showcaseApproval.approvedBy !== 'string' || !entry.showcaseApproval.approvedBy.trim() || !/^\d{4}-\d{2}-\d{2}$/.test(entry.showcaseApproval.approvedOn || '') ||
      !Array.isArray(entry.media) || entry.media.length === 0 || !Array.isArray(entry.downloads || [])) {
      issue(issues,'error','invalid-showcase',source,`invalid public metadata or showcase approval for ${id}`); continue;
    }
    if (entry.logicalAssetId !== undefined) {
      const group = logical.get(entry.logicalAssetId);
      if (!group || group.projectId !== project) { issue(issues,'error','invalid-showcase-group',source,`unknown or mismatched logical group for ${id}`); continue; }
    }
    const approvedMedia = [], approvedDownloads = [], staged = [], keys = new Set();
    let valid = true;
    for (const [kind, items] of [['preview',entry.media],['download',entry.downloads || []]]) for (const item of items) {
      const asset = byId.get(item?.assetId);
      if (!asset || typeof item.key !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.key) || keys.has(item.key) ||
        asset.projectId !== project || asset.path.startsWith('projects/momee/') || asset.path.startsWith('incoming/momee/') ||
        issues.some(issue => issue.path === asset.path && (issue.code === 'invalid-asset' || issue.code === 'lfs-unavailable')) ||
        !approvalValid(item.approval,asset) || !safePublicSvg(root,asset) ||
        (entry.logicalAssetId && !logical.get(entry.logicalAssetId).physicalAssetIds.includes(asset.id))) { valid = false; break; }
      if (kind === 'preview' && (asset.role !== 'review' || !PREVIEW_FORMATS.has(asset.format) ||
        (item.caption !== undefined && !publicText(item.caption,PUBLIC_TEXT_LIMITS.caption)))) { valid = false; break; }
      if (kind === 'download' && ((asset.role !== 'export' && !(asset.role === 'source' && item.allowSource === true)) ||
        (item.label !== undefined && !publicText(item.label,PUBLIC_TEXT_LIMITS.label)))) { valid = false; break; }
      keys.add(item.key);
      const publicFile = {key:item.key,url:publicAssetUrl(asset),format:asset.format,bytes:asset.bytes,sha256:asset.sha256,
        ...(asset.dimensions && {dimensions:asset.dimensions}), ...(kind === 'preview' && item.caption && {caption:item.caption.trim()}),
        ...(kind === 'download' && {label:(item.label || `${asset.format.toUpperCase()} file`).trim()})};
      (kind === 'preview' ? approvedMedia : approvedDownloads).push(publicFile);
      staged.push({...asset,url:publicFile.url,kind,publication:'public',rightsStatus:'verified',sourceApproved:kind === 'download' && item.allowSource === true});
    }
    if (!valid || approvedMedia.length !== entry.media.length || approvedDownloads.length !== (entry.downloads || []).length) { issue(issues,'error','showcase-file-denied',source,`preview or download approval denied for ${id}`); continue; }
    if (entry.relatedShowcaseIds !== undefined && (!Array.isArray(entry.relatedShowcaseIds) || !entry.relatedShowcaseIds.every(value => typeof value === 'string' && /^[A-Za-z0-9_-]+\/[a-z0-9-]+$/.test(value)))) { issue(issues,'error','invalid-showcase-related',source,`invalid related showcases for ${id}`); continue; }
    for (const asset of staged) { asset.publication = 'public'; deliveries.push(asset); const internal = byId.get(asset.id); internal.publication = 'public'; internal.rightsStatus = 'verified'; }
    publicShowcases.push({id,projectId:project,slug,title:entry.title.trim(),description:entry.description.trim(),category:entry.category.trim(),
      publication:approvedDownloads.length ? 'downloadable' : 'showcase',
      ...(entry.tags?.length && {tags:[...new Set(entry.tags.map(tag => tag.trim()))]}),
      ...(entry.logicalAssetId && {logicalAssetId:entry.logicalAssetId}),
      ...(entry.relatedShowcaseIds?.length && {relatedShowcaseIds:[...new Set(entry.relatedShowcaseIds)]}),
      media:approvedMedia,downloads:approvedDownloads});
  }
  const publicIds = new Set(publicShowcases.map(item => item.id));
  for (const showcase of publicShowcases) for (const related of showcase.relatedShowcaseIds || []) if (!publicIds.has(related)) issue(issues,'error','invalid-showcase-related',source,`${showcase.id} references unpublished ${related}`);
  publicShowcases.sort((a,b)=>compareStrings(a.id,b.id));
  return {showcases:publicShowcases,deliveries};
}

function legacyShowcases(publicCatalog, claimedIds) {
  const groups = new Map();
  for (const asset of publicCatalog.assets) {
    if (claimedIds.has(asset.id)) continue;
    const logical = publicCatalog.logicalAssets.find(group => group.projectId === asset.projectId && group.physicalAssetIds.includes(asset.id));
    const key = logical?.id || asset.id;
    if (!groups.has(key)) groups.set(key,{projectId:asset.projectId,logicalAssetId:logical?.id,assets:[]});
    groups.get(key).assets.push(asset);
  }
  return [...groups].map(([key,group]) => {
    const first = group.assets[0], slug = `legacy-${createHash('sha256').update(key).digest('hex').slice(0,12)}`;
    const files = group.assets.map((asset,index) => ({key:`file-${index+1}`,url:asset.url,format:asset.format,bytes:asset.bytes,sha256:asset.sha256,...(asset.dimensions && {dimensions:asset.dimensions})}));
    return {id:`${group.projectId}/${slug}`,projectId:group.projectId,slug,
      title:first.title || first.path.split('/').at(-1),description:first.description || 'Approved asset export',category:first.category,
      publication:'downloadable',...(first.tags?.length && {tags:first.tags}),...(group.logicalAssetId && {logicalAssetId:group.logicalAssetId}),
      media:files.filter(file => PREVIEW_FORMATS.has(file.format)).map((file,index) => ({...file,key:`media-${index+1}`})),
      downloads:files.map(file => ({...file,label:`${file.format.toUpperCase()} file`}))};
  });
}

export function generateCatalog(root, options = {}) {
  root = resolve(root);
  const config = options.config ?? readJson(root,'catalog/config.json'); const issues = []; const paths = [];
  if (config.schemaVersion !== 1 || !Array.isArray(config.roots) || !Array.isArray(config.formats) || !Array.isArray(config.excludeDirectories)) throw new Error('invalid catalog config');
  for (const rootPath of config.roots) { normalizePath(rootPath); if (rootPath.includes('/')) throw new Error('catalog roots must be top-level'); walk(root,rootPath,config,paths,issues); }
  paths.sort(); const assets = []; const pathMap = new Map(); const hashMap = new Map();
  for (const path of paths) {
    normalizePath(path);
    const absolute = join(root,path); if (lstatSync(absolute).isSymbolicLink()) { issue(issues,'warning','symlink-skipped',path,'symlink was not followed'); continue; }
    const bytes = readFileSync(absolute); const format = extname(path).slice(1).toLowerCase(); const sha256 = createHash('sha256').update(bytes).digest('hex');
    const inspected = inspect(bytes,format,path,issues);
    if (!inspected.available) continue;
    const record = { id:physicalId(path), projectId:projectId(path), path, role:inferRole(path), category:inferCategory(path), format, bytes:bytes.length, sha256, publication:'private', rightsStatus:'unknown', ...(inspected.dimensions && {dimensions:inspected.dimensions}), logicalAssetIds:[] };
    assets.push(record); pathMap.set(path,record);
    if (!hashMap.has(sha256)) hashMap.set(sha256,[]); hashMap.get(sha256).push(path);
  }
  const logical = new Map();
  if (options.integrateManifests !== false) { integrateImports(root,pathMap,issues); integrateMomee(root,pathMap,logical,issues); integrateGroup1(root,pathMap,logical,issues); }
  if (options.metadata || existsSync(join(root,'catalog/metadata.json'))) integrateEditorial(root,pathMap,issues,options.metadata);
  for (const a of assets) { a.logicalAssetIds.sort(); if (!a.logicalAssetIds.length) delete a.logicalAssetIds; }
  validateRecords(assets,logical,issues);
  for (const paths of hashMap.values()) if (paths.length > 1) issue(issues,'warning','exact-duplicate',paths[0],`identical content: ${paths.join(', ')}`);
  const publications = options.publications ?? readJson(root,'catalog/publications.json');
  const publicCatalog = applyPublications(root,assets,logical,issues,publications);
  const {showcases,deliveries} = applyShowcases(root,assets,logical,issues,publications);
  publicCatalog.showcases = [...showcases,...legacyShowcases(publicCatalog,new Set(deliveries.map(asset => asset.id)))].sort((a,b)=>compareStrings(a.id,b.id));
  if (new Set(publicCatalog.showcases.map(item => item.id)).size !== publicCatalog.showcases.length) issue(issues,'error','duplicate-showcase-id','catalog/publications.json','explicit showcase collides with a legacy approved group');
  const legacyDeliveries = publicCatalog.assets.map(asset => ({...asset,kind:'download'}));
  const internal = {schemaVersion:1,assets,logicalAssets:[...logical.values()].sort((a,b)=>compareStrings(a.id,b.id))};
  issues.sort((a,b)=>compareStrings(a.path,b.path) || compareStrings(a.code,b.code) || compareStrings(a.message,b.message));
  const validation = {schemaVersion:1,summary:{assets:assets.length,logicalAssets:logical.size,publicAssets:publicCatalog.assets.length,publicShowcases:publicCatalog.showcases.length,errors:issues.filter(x=>x.severity==='error').length,warnings:issues.filter(x=>x.severity==='warning').length},issues};
  return {internal,publicCatalog,deliveries:[...legacyDeliveries,...deliveries],validation};
}
