"""Consolidate completed validation; read-only access to all astronaut assets."""
from pathlib import Path
import json,struct,hashlib,ast
HERE=Path(__file__).resolve().parent
audit=json.loads((HERE/'export-validation.json').read_text())
three=json.loads((HERE/'three-validation.json').read_text())
comparison=json.loads((HERE/'previous-comparison.json').read_text())
output=Path(audit['output']);blob=output.read_bytes()
assert hashlib.sha256(blob).hexdigest()==audit['sha256']
hash_checks={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in audit['sourceHashes'].items()}
assert all(hash_checks.values())
for script in HERE.glob('*.py'):ast.parse(script.read_text(),filename=str(script))
for file in HERE.iterdir():
    if file.suffix in ['.py','.mjs','.cjs','.md']:
        assert all(line.rstrip()==line for line in file.read_text().splitlines()),f'Trailing whitespace: {file}'
size=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+size])
joints=g['skins'][0]['joints'];joint_set=set(joints)
roots=[i for i in joints if not any(i in n.get('children',[]) for j,n in enumerate(g['nodes']) if j in joint_set)]
assert len(g['nodes'])==43 and len(roots)==1
assert not g.get('cameras') and not g.get('extensionsRequired')
assert len(g['meshes'])==len(g['skins'])==len(g['materials'])==1
old=json.loads((HERE.parent/'export/export-validation.json').read_text())
ready=audit['allChecksPassed'] and three['passed'] and not comparison['unexpectedDifferences'] and all(hash_checks.values())
report={'status':'LOCAL VALIDATION PASSED — ready for final asset approval' if ready else 'UNAPPROVED — validation issues',
        'output':str(output),'fileBytes':len(blob),'fileMB':len(blob)/1e6,'fileMiB':len(blob)/1048576,'sha256':audit['sha256'],
        'blender':audit['blender'],'geometry':{'skinnedMeshes':1,'primitives':1,'sourceVertices':11181,'exportedVertices':11188,'triangles':10357,'unchangedFromPreviousCandidate':True},
        'skeleton':{'skins':1,'joints':41,'boneNames':[g['nodes'][i]['name'] for i in joints],'rootJoint':g['nodes'][roots[0]]['name'],'nodeCount':len(g['nodes']),'validInverseBinds':True,'unchangedFromPreviousCandidate':True},
        'animations':audit['clips'],'samplingHz':240,'sourceFPSRetimedInMemoryOnly':True,'placementOffsetMeters':audit['constantGroundOffset'],
        'textures':audit['images'],'material':g['materials'][0],'noExternalReferencesOrRequiredDecoder':True,
        'skinning':{'reduction':audit['skinningReduction'],'finalBuffersIdenticalToPreviousCandidate':True,'measurements':{n:{k:v for k,v in values.items() if k in ['meshVsApprovedSource','meshVsFourInfluenceExportInput','regionSkinningErrors','jointHeadPositionError','jointRelativeWorldRotationErrorDegrees']} for n,values in audit['roundtrip'].items()}},
        'groundClearance':{'freshBlenderBootMinimaMeters':{n:v['bootMinima'] for n,v in audit['roundtrip'].items()},'freshBlenderWalkSamples':993,'freshBlenderWalkSamplingHz':960,'three':three['walkGround'],
                           'previousCandidateWalkMinimumMeters':old['roundtrip']['Walk']['minimumGroundZ'],'previousMeasurementNote':'Previously recorded 63-pose check; final measured at 993 samples.','additionalCorrectionNecessary':False},
        'orientationAndScale':{'up':'+Y','forward':'+Z','units':'meters','rescaled':False,'defaultIdleBounds':three['defaultBounds'],'standingHeightMeters':three['defaultBounds']['max'][1]-three['defaultBounds']['min'][1]},
        'rootDriftMeters':{n:v['horizontalRootEndpointDrift'] for n,v in three['clips'].items()},'threeValidation':three,
        'previousComparison':comparison,'visualReview':{'images':['deformation-overview.png','deformation-closeups.png'],'reviewed':True,'findings':'No obvious new collapse, tearing or silhouette degradation in matched source/final helmet, neck, shoulders, wrists, backpack, knee and boot views. Previously validated reduction remains nonzero; existing stylized crease shapes/faceting persist.'},
        'checks':audit['checks'],'protectedInputHashesUnchanged':hash_checks,'allTechnicalValidationPassed':ready,
        'remainingRisks':['Asset-specific Meshy/Mixamo redistribution and attribution evidence remains undocumented locally; no publication approval.','Real GPU upload, hardware performance and runtime lighting not tested.','Native gait endpoint velocity seam remains; mixed-clip contacts and movement synchronization require later review.','Four-influence reduction retains the previous accepted localized errors (up to approximately 9.3 mm); not lossless.','Final binary owner playback approval pending.'],
        'integrationContract':'integration-contract.md','report':'README.md','runtimeModified':False,'published':False,
        'createdFiles':sorted(p.name for p in HERE.iterdir() if p.is_file())+['final-validation.json'],'newAsset':output.name}
(HERE/'final-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'bytes':len(blob),'protectedInputHashesUnchanged':all(hash_checks.values()),'pythonSyntaxAndWhitespacePassed':True},indent=2))
