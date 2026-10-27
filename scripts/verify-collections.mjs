// Verify the imported snapshot without depending on the original workspaces.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const manifest = JSON.parse(await readFile(new URL('../docs/collection-import.json', import.meta.url), 'utf8'));
if (manifest.schemaVersion !== 1 || manifest.algorithm !== 'sha256') throw new Error('Unsupported import manifest');
let failures = 0;
let total = 0;
const seen = new Set();
for (const collection of manifest.collections) {
  let bytes = 0;
  for (const file of collection.files) {
    const name = `${collection.destination}/${file.path}`;
    const target = resolve(root, name);
    if (!target.startsWith(resolve(root) + sep) || seen.has(target)) throw new Error(`Invalid or duplicate import path: ${name}`);
    seen.add(target);
    try {
      const data = await readFile(target);
      const hash = createHash('sha256').update(data).digest('hex');
      if (data.length !== file.bytes || hash !== file.sha256) throw new Error('Size or SHA-256 differs from the imported snapshot');
      bytes += data.length;
      total++;
    } catch (error) {
      failures++;
      console.error(`${name}: ${error.message}`);
    }
  }
  console.log(`${collection.destination}: ${collection.files.length} expected files, ${bytes} verified bytes`);
}
console.log(`${total} files verified; ${failures} failures.`);
process.exitCode = failures ? 1 : 0;
