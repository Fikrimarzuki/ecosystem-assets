"""Save only a new asset scene after dense validation and still review."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from bake_utils import *
assert not OUTPUT.exists(),'Refusing to overwrite any existing corrected file'
validation=json.loads((HERE/'final-correction-validation.json').read_text())
visual=json.loads((HERE/'visual-review.json').read_text())
assert validation['numericChecksPassed'] and validation['inputsUnchanged']
assert visual['noMajorArtifactsInReviewedStills']
before=hashes();assert before==DIAGNOSIS['inputs']
scene,rig,mesh=open_source()
source_walk=bpy.data.actions['Walk'];idle=bpy.data.actions['Idle']
source_idle_hash=action_hash(idle);source_skin_hash=skin_hash(mesh,rig)
keys=dict(np.load(HERE/'baked-leg-loop-keys.npz'))
result=make_action(rig,source_walk,keys)
source_other_hash=bone_action_hash(source_walk,CHANGED)
source_walk.name='Walk_SourceTransient'
result.name='Walk'
activate(rig,result,1)
bpy.data.actions.remove(source_walk,do_unlink=True)
idle.use_fake_user=True;result.use_fake_user=True
assert sorted(a.name for a in bpy.data.actions)==['Idle','Walk']
assert action_hash(idle)==source_idle_hash
assert bone_action_hash(result,CHANGED)==source_other_hash
assert skin_hash(mesh,rig)==source_skin_hash
assert len(scene.objects)==2
assert not rig.animation_data.nla_tracks and not any(b.constraints for b in rig.pose.bones)
scene.render.fps=30;scene.render.fps_base=1;scene.frame_start=1;scene.frame_end=32
rig['ground_correction_method']='Baked per-foot vertical targets with rest-aware two-bone leg solve; original hips, foot world rotations, lengths and skin retained.'
rig['ground_reference_z']=-OFFSET
rig['common_export_ground_offset_y']=OFFSET
rig['ground_correction_review']='Manual playback approval still required; compare ground at Blender Z=-0.0096075517. Original Idle and object transforms unchanged.'
result['ground_correction_revision']='M7.2 independent foot-contact correction, loop-refined'
scene['ground_correction_note']='No inspection floor/camera/light saved. Ground reference Z=-0.0096075517 matches existing common +9.608mm export offset.'
saved_walk_hash=action_hash(result)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=False)
assert hashes()==before
manifest={'output':str(OUTPUT),'bytes':OUTPUT.stat().st_size,'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    'sourceInputs':before,'sourceIdleActionFingerprint':source_idle_hash,'skinAndTextureFingerprint':source_skin_hash,
    'savedWalkActionFingerprint':saved_walk_hash,'otherWalkChannelsFingerprint':source_other_hash,
    'actions':['Idle','Walk'],'defaultActiveAction':'Walk','defaultTimeline':[1,32],
    'groundReferenceZ':-OFFSET,'commonExportGroundOffsetY':OFFSET,'noGroundOffsetBakedIntoObjectOrIdle':True,
    'readyForManualVisualInspection':True,'finalAnimationApproval':False,'noGlbExported':True,'sourceInputsUnchanged':True}
write('saved-correction.json',manifest)
print('SAVED_CORRECTED',json.dumps(manifest),flush=True)
