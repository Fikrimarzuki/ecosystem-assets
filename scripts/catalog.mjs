import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { generateCatalog } from './lib/catalog.mjs';

const repository = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const command = process.argv[2] || 'build';
if (!['build','validate'].includes(command)) {
  console.error('Usage: node scripts/catalog.mjs [build|validate]');
  process.exit(2);
}

try {
  const {internal,publicCatalog,validation} = generateCatalog(repository);
  if (command === 'build') {
    const output = join(repository,'catalog-output');
    mkdirSync(output,{recursive:true});
    for (const [name,value] of [['internal.json',internal],['public.json',publicCatalog],['validation.json',validation]]) {
      writeFileSync(join(output,name),JSON.stringify(value,null,2)+'\n');
    }
    console.log(`Wrote catalog-output/{internal,public,validation}.json`);
  }
  console.log(JSON.stringify(validation.summary));
  for (const issue of validation.issues.filter(x => x.severity === 'error')) console.error(`${issue.code}: ${issue.path}: ${issue.message}`);
  if (validation.summary.errors) process.exitCode = 1;
} catch (error) {
  console.error(error.stack || String(error));
  process.exitCode = 1;
}
