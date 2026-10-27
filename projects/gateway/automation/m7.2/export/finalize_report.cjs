// Read-only asset verification; write a new approval summary beside evidence.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const here = __dirname;
const destination = path.join(here, 'approval-summary.json');
assert(!fs.existsSync(destination), 'Refusing to overwrite an existing approval summary');
const report = JSON.parse(fs.readFileSync(path.join(here, 'export-validation.json')));
const engine = JSON.parse(fs.readFileSync(path.join(here, 'three-validation.json')));
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
for (const [file, expected] of Object.entries(report.sourceHashes)) assert.equal(digest(file), expected);
assert.equal(digest(report.output), report.sha256);
assert.equal(fs.statSync(report.output).size, report.fileBytes);
assert.equal(engine.passed, true);
assert.equal(report.technicalChecksPassedExceptGrounding, true);
assert.deepEqual(report.checks.filter(c => !c.passed).map(c => c.name), ['Walk floor clearance within 1mm']);
for (const file of ['export-comparison.png', 'skinning-closeups.png', 'walk-worst-ground-boots.png']) assert(fs.existsSync(path.join(here, file)));
const summary = {
  output: report.output, sha256: report.sha256, bytes: report.fileBytes, triangles: report.triangleCount,
  sourceFilesUnchanged: true, technicalValidationPassedExceptGroundClearance: true,
  groundClearancePassed: false, readyForUnconditionalFinalApproval: false,
  reviewStatus: 'Ready for owner inspection; retain as candidate until ground-contact and skinning approximation are accepted',
  visualInspection: { fullBody: 'Original source, four-influence input and reimported candidate front/back poses inspected; helmet, backpack, shoulders and knees remain coherent',
    closeups: 'Neck and wrist show small local shape/shading differences; no obvious tearing in reviewed stills',
    boots: 'Retained Walk sole/heel floor intersection visible at source frame 23.5' },
  remainingIssues: [
    'Retained Walk boot penetration up to 45.126 mm; diagnostic 1 mm floor-clearance criterion fails',
    'Owner playback and closeup approval of the four-influence candidate is still needed (maximum vertex approximation 9.3 mm)',
    'Existing redistribution/attribution provenance unresolved for public release',
    'Actual GPU/device rendering and Idle/Walk blending were not tested in Gateway'
  ],
  verificationScope: 'Blender 5.2.2 background export, fresh-scene import, 564 sampled poses, binary checks, matching stills and offline Three CPU loader/mixer; no runtime changes or publication'
};
fs.writeFileSync(destination, JSON.stringify(summary, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(summary, null, 2));
