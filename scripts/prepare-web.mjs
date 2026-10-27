import { mkdirSync, mkdtempSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateCatalog } from './lib/catalog.mjs';
import { copyApprovedAssets } from './lib/public-delivery.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const generated = join(root, 'apps/web/.generated/public');

try {
  const { publicCatalog, deliveries, validation } = generateCatalog(root);
  if (validation.summary.errors) throw new Error(`catalog validation has ${validation.summary.errors} error(s)`);
  mkdirSync(dirname(generated), { recursive: true });
  const staging = mkdtempSync(join(dirname(generated), '.public-stage-'));
  try {
    copyApprovedAssets(root, deliveries, staging);
    writeFileSync(join(staging, 'catalog.json'), JSON.stringify(publicCatalog, null, 2) + '\n');
    rmSync(generated, { recursive: true, force: true });
    renameSync(staging, generated);
  } finally { rmSync(staging, { recursive: true, force: true }); }
  console.log(`Prepared web catalog: ${publicCatalog.showcases.length} showcases, ${deliveries.length} approved file references`);
} catch (error) {
  rmSync(generated, { recursive: true, force: true });
  console.error(error.stack || String(error));
  process.exitCode = 1;
}
