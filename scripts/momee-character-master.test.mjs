import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { test } from 'node:test';
import { check, place, readPng } from './momee-character-master.mjs';

const M = resolve(import.meta.dirname, '../projects/momee/');
const mom1x = () => readPng(resolve(M, 'exports/characters/mom/mom-three-quarter-accepted-clean.v1.@1x.png'));
const fails = (img, opts) => check(img, 'mom', { ppu: 1, ...opts }).filter((r) => r.level === 'FAIL').map((r) => r.name);

test('the accepted Mom @1x export passes every check at 1 px/u', () => {
  assert.deepEqual(fails(mom1x(), { chinY: 100 }), []);
});

test('a mirrored (right-facing) Mom fails the facing check', () => {
  const b = mom1x(), m = { ...b, data: new Uint8Array(b.data.length) };
  for (let y = 0; y < b.height; y++) for (let x = 0; x < b.width; x++)
    m.data.set(b.data.subarray((y * b.width + x) * 4, (y * b.width + x) * 4 + 4), (y * b.width + b.width - 1 - x) * 4);
  assert.deepEqual(fails(m), ['facing (left, as accepted)']);
});

test('an opaque, background-filled image fails transparency', () => {
  const b = mom1x();
  for (let i = 0; i < b.data.length; i += 4) b.data[i + 3] = 255;
  b.hasAlpha = false;
  assert.ok(fails(b).includes('alpha channel'));
  assert.ok(fails(b).includes('transparent background'));
});

test('cropped hair and a baked floor shadow are caught', () => {
  const c = mom1x();
  c.data.fill(0, 0, c.width * 30 * 4);
  assert.ok(fails(c).includes('figure height'));
  const s = mom1x();
  for (let y = 296; y <= 303; y++) for (let x = 30; x < 170; x++) { const o = (y * s.width + x) * 4; if (!s.data[o + 3]) s.data.set([110, 100, 96, 110], o); }
  assert.deepEqual(fails(s), ['no baked floor shadow']);
});

test('place refuses to enlarge the 514 px accepted cutout into a 4 px/u master', () => {
  const nat = readPng(resolve(M, 'source/characters/mom/mom-three-quarter-accepted-clean.v1.native.png'));
  assert.throws(() => place(nat, 'mom', 4), /refusing to enlarge/);
});

test('place at a density the source supports reproduces the spec geometry', () => {
  const nat = readPng(resolve(M, 'source/characters/mom/mom-three-quarter-accepted-clean.v1.native.png'));
  const { image } = place(nat, 'mom', 1);
  assert.deepEqual(fails({ ...image, hasAlpha: true }), []);
});
