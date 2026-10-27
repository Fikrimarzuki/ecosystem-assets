import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { test } from 'node:test';
import { approvalErrors, visualDirectionErrors } from './lib/momee-approval.mjs';

const accepted = { state: 'owner-accepted-visual-direction', scope: 'Boy ¾ design', recordedOn: '2026-10-24', evidence: 'owner brief' };
const rejected = { ...accepted, state: 'owner-rejected-visual-direction' };
const owner = { by: 'product owner', date: '2026-11-01' };
const verified = { status: 'verified', provenancePath: 'x', verifiedBy: 'owner', verifiedOn: '2026-11-01', evidence: 'licence record' };
const base = { status: 'Candidate', rights: { status: 'unverified', provenancePath: 'x' }, approval: null, exports: [{}] };
const errs = (a) => approvalErrors({ ...base, ...a });

test('historical shapes stay valid (no visualAcceptance / productionApproval fields)', () => {
  assert.deepEqual(errs({}), []);
  assert.deepEqual(errs({ status: 'Working' }), []);
  assert.deepEqual(errs({ visualAcceptance: null, productionApproval: null }), []);
});

test('visual acceptance alone does not imply production approval', () => {
  assert.deepEqual(errs({ visualAcceptance: accepted, productionApproval: null }), []);
});

test('visual acceptance must be well formed', () => {
  assert.ok(errs({ visualAcceptance: { state: 'approved' } }).some((m) => m.includes('visualAcceptance.state')));
  assert.ok(errs({ visualAcceptance: { ...accepted, recordedOn: 'today' } }).some((m) => m.includes('recordedOn')));
  assert.ok(errs({ visualAcceptance: { ...accepted, evidence: '' } }).some((m) => m.includes('evidence')));
});

test('a Candidate cannot carry production approval (either field name)', () => {
  assert.ok(errs({ approval: owner }).includes('non-approved entry carries production approval'));
  assert.ok(errs({ productionApproval: owner }).includes('non-approved entry carries production approval'));
});

test('rights-unverified assets cannot be production-ready', () => {
  const e = errs({ status: 'Approved', productionApproval: owner, approval: owner, visualAcceptance: accepted });
  assert.ok(e.includes('rights-unverified or restricted assets cannot be Approved'));
  const r = errs({ status: 'Approved', productionApproval: owner, approval: owner, visualAcceptance: accepted, rights: { status: 'restricted', provenancePath: 'x' } });
  assert.ok(r.includes('rights-unverified or restricted assets cannot be Approved'));
});

test('Approved needs all three gates and exports', () => {
  assert.deepEqual(errs({ status: 'Approved', productionApproval: owner, approval: owner, visualAcceptance: accepted, rights: verified }), []);
  assert.ok(errs({ status: 'Approved', rights: verified, visualAcceptance: accepted }).includes('Approved requires production approval (by, date)'));
  assert.ok(errs({ status: 'Approved', productionApproval: owner, rights: verified }).includes('Approved requires an owner-accepted visual direction'));
  assert.ok(errs({ status: 'Approved', productionApproval: owner, rights: verified, visualAcceptance: accepted, exports: [] }).includes('Approved requires exports'));
});

test('contradictions are caught', () => {
  assert.ok(errs({ status: 'Approved', productionApproval: owner, rights: verified, visualAcceptance: rejected })
    .includes('a rejected visual direction cannot be production-approved'));
  assert.ok(errs({ status: 'Approved', rights: verified, visualAcceptance: accepted, approval: owner, productionApproval: { ...owner, date: '2026-12-01' } })
    .includes('approval and productionApproval disagree'));
  assert.ok(errs({ productionApproval: { by: 'owner' } }).some((m) => m.startsWith('productionApproval must record')));
});

test('verified rights need who, when and evidence', () => {
  assert.ok(errs({ rights: { status: 'verified', provenancePath: 'x' } }).some((m) => m.startsWith('verified rights require')));
  assert.deepEqual(errs({ rights: verified }), []);
});

test('every entry in the current Momee manifest satisfies the contract', () => {
  const manifest = JSON.parse(readFileSync(resolve(import.meta.dirname, '../projects/momee/manifest.json'), 'utf8'));
  for (const asset of manifest.assets) assert.deepEqual(approvalErrors(asset), [], asset.id);
});

test('a provisional visual acceptance keeps the three gates separate', () => {
  assert.deepEqual(errs({ visualAcceptance: { ...accepted, provisional: true }, productionApproval: null }), []);
  assert.ok(errs({ visualAcceptance: { ...accepted, provisional: 'yes' } }).some((m) => m.includes('provisional')));
  assert.ok(errs({ visualAcceptance: { ...accepted, provisional: true }, productionApproval: owner })
    .some((m) => m.includes('non-approved entry carries production approval')));
});

test('visualDirection is optional and must name a known direction', () => {
  const ids = ['soft-storybook-adventure', 'calm-chibi-storybook'];
  assert.deepEqual(visualDirectionErrors({}, ids), []);
  assert.deepEqual(visualDirectionErrors({ visualDirection: 'soft-storybook-adventure' }, ids), []);
  assert.equal(visualDirectionErrors({ visualDirection: 'unknown-style' }, ids).length, 1);
  assert.equal(visualDirectionErrors({ visualDirection: 7 }, ids).length, 1);
});
