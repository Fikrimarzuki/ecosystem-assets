// Momee manifest approval contract (M1.0j-C). Three independent states, plus the workflow `status`:
//
//   visualAcceptance  — the owner's judgement of a *design direction* (looks right / looks wrong).
//                       absent | null | { state, scope, recordedOn, evidence }.
//                       Says nothing about production use or rights.
//   productionApproval — the owner's approval to ship the file in a production runtime.
//                       absent | null | { by, date, scope? }. The legacy field `approval` means the
//                       same thing; if both are set they must be identical.
//   rights            — { status: unverified | verified | restricted, provenancePath, … }.
//                       `verified` needs who/when/evidence.
//   status            — workflow stage: Working | Candidate | Approved. `Approved` is the only
//                       production-ready stage and requires all three gates.
//
// Optional `visualDirection` (M1.1a): which visual direction an entry belongs to, by id in projects/momee/visual-directions.json.
// Legacy entries omit it and inherit the manifest's top-level theme. `visualAcceptance.provisional: true` marks a provisional acceptance;
// it changes neither the state names nor the three gates.
//
// Pure function: returns a list of error strings; never reads files.

export const VISUAL_STATES = ['owner-accepted-visual-direction', 'owner-rejected-visual-direction'];
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const text = (v) => typeof v === 'string' && v.trim().length > 0;
const set = (v) => v !== undefined && v !== null;

export function approvalErrors(asset) {
  const e = [];
  const va = asset.visualAcceptance;
  const legacy = asset.approval;
  const pa = asset.productionApproval;
  const rights = asset.rights ?? {};

  if (set(va)) {
    if (typeof va !== 'object') e.push('visualAcceptance must be an object or null');
    else {
      if (!VISUAL_STATES.includes(va.state)) e.push(`visualAcceptance.state must be one of ${VISUAL_STATES.join(', ')}`);
      if (!text(va.scope)) e.push('visualAcceptance.scope is required');
      if (!ISO_DATE.test(va.recordedOn ?? '')) e.push('visualAcceptance.recordedOn must be YYYY-MM-DD');
      if (!text(va.evidence)) e.push('visualAcceptance.evidence is required');
      if ('provisional' in va && typeof va.provisional !== 'boolean') e.push('visualAcceptance.provisional must be a boolean');
    }
  }
  for (const [name, v] of [['approval', legacy], ['productionApproval', pa]]) {
    if (!set(v)) continue;
    if (typeof v !== 'object' || !text(v.by) || !ISO_DATE.test(v.date ?? ''))
      e.push(`${name} must record by and date (YYYY-MM-DD)`);
  }
  if (set(legacy) && set(pa) && JSON.stringify(legacy) !== JSON.stringify(pa))
    e.push('approval and productionApproval disagree');

  const production = set(pa) ? pa : legacy;
  const rejected = va?.state === 'owner-rejected-visual-direction';
  if (set(production) && asset.status !== 'Approved') e.push('non-approved entry carries production approval');
  if (rejected && (set(production) || asset.status === 'Approved'))
    e.push('a rejected visual direction cannot be production-approved');
  if (asset.status === 'Approved') {
    if (!set(production)) e.push('Approved requires production approval (by, date)');
    if (rights.status !== 'verified') e.push('rights-unverified or restricted assets cannot be Approved');
    if (va?.state !== 'owner-accepted-visual-direction') e.push('Approved requires an owner-accepted visual direction');
    if (!asset.exports?.length) e.push('Approved requires exports');
  }
  if (rights.status === 'verified' && (!text(rights.verifiedBy) || !ISO_DATE.test(rights.verifiedOn ?? '') || !text(rights.evidence)))
    e.push('verified rights require verifiedBy, verifiedOn (YYYY-MM-DD) and evidence');
  return e;
}

/** Errors for an entry's optional `visualDirection` against the known direction ids. */
export function visualDirectionErrors(asset, directionIds) {
  if (asset.visualDirection === undefined) return [];
  if (typeof asset.visualDirection !== 'string' || !directionIds.includes(asset.visualDirection))
    return [`visualDirection must be one of ${directionIds.join(', ')}`];
  return [];
}
