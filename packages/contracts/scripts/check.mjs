import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');

const generated = execFileSync('npx', ['openapi-typescript', 'openapi.json'], {
  cwd: root,
  shell: process.platform === 'win32',
})
  .toString()
  .trim();

let committed = '';
try {
  committed = readFileSync(join(root, 'src', 'api.ts'), 'utf8').trim();
} catch {
  console.error('DRIFT: packages/contracts/src/api.ts is missing — run `npm run generate`');
  process.exit(1);
}

if (generated !== committed) {
  console.error('DRIFT: packages/contracts/src/api.ts is stale — run `npm run generate`');
  process.exit(1);
}

console.log('contract: up to date');
