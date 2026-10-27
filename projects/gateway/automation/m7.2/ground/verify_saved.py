"""Fresh process: verify saved action/skin/Idle and dense serialized boot clearance."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from bake_utils import *
manifest=json.loads((HERE/'saved-correction.json').read_text())
validation=json.loads((HERE/'final-correction-validation.json').read_text())
assert hashes()==manifest['sourceInputs']
scene,rig,mesh=open_source()
source_idle=bpy.data.actions['Idle'];source_poses=[]
for frame in [1,126,251]:
    activate(rig,source_idle,frame);source_poses.append(positions(mesh))
bpy.ops.wm.open_mainfile(filepath=str(OUTPUT),load_ui=False,use_scripts=False)
scene=bpy.context.scene
rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH')
assert len(scene.objects)==2 and sorted(a.name for a in bpy.data.actions)==['Idle','Walk']
assert len(rig.data.bones)==41 and len(mesh.data.vertices)==11181 and len(mesh.vertex_groups)==34
mesh.data.calc_loop_triangles();assert len(mesh.data.loop_triangles)==10357
assert not rig.animation_data.nla_tracks and not any(b.constraints for b in rig.pose.bones)
assert skin_hash(mesh,rig)==manifest['skinAndTextureFingerprint']
assert action_hash(bpy.data.actions['Idle'])==manifest['sourceIdleActionFingerprint']
assert action_hash(bpy.data.actions['Walk'])==manifest['savedWalkActionFingerprint']
assert bone_action_hash(bpy.data.actions['Walk'],CHANGED)==manifest['otherWalkChannelsFingerprint']
assert tuple(bpy.data.actions['Idle'].frame_range)==(1,251)
assert tuple(bpy.data.actions['Walk'].frame_range)==(1,32)
idle_errors=[]
for frame,source in zip([1,126,251],source_poses):
    activate(rig,bpy.data.actions['Idle'],frame);idle_errors.append(float(np.linalg.norm(positions(mesh)-source,axis=1).max()))
assert max(idle_errors)==0
masks=boot_masks(mesh,rig);minimums={s:[] for s in masks}
for frame in np.arange(1,32+.001,.03125):
    activate(rig,bpy.data.actions['Walk'],frame);co=positions(mesh);co[:,2]+=OFFSET
    assert np.isfinite(co).all()
    for side,ids in masks.items():minimums[side].append(float(co[ids,2].min()))
for side in masks:
    assert min(minimums[side])>0
    assert abs(min(minimums[side])-validation['boots'][side]['afterMinimum'])<1e-8
assert hashes()==manifest['sourceInputs']
assert hashlib.sha256(OUTPUT.read_bytes()).hexdigest()==manifest['sha256']
result={'freshBlenderVersion':bpy.app.version_string,'oneMeshOneArmature':True,'triangles':10357,'vertices':11181,'bones':41,
    'idleDurationSeconds':250/30,'walkDurationSeconds':31/30,'actionSerializationExact':True,'skinGeometryUvRestObjectsAndPackedTexturesExact':True,
    'idleWorldPoseErrorsAtFrames1_126_251':idle_errors,'serializedWalkSampleCount':len(minimums['Left']),
    'serializedBootMinimumClearance':{s:min(h) for s,h in minimums.items()},'sourceInputsAndFirstCandidateUnchanged':True,
    'newFileHashUnchangedAfterReadOnlyVerification':True,'noExportPerformed':True}
write('saved-file-validation.json',result)
print('FRESH_FILE_PASS',json.dumps(result),flush=True)
