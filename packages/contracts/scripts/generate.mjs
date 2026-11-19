import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const output = join(root, 'src', 'api.ts');

mkdirSync(dirname(output), { recursive: true });

execFileSync('npx', ['openapi-typescript', 'openapi.json', '--output', output], {
  cwd: root,
  stdio: 'inherit',
  shell: process.platform === 'win32',
});

console.log(`generated ${output}`);
