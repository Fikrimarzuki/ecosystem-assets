"""Dense boot/native Walk diagnosis. No source saves, edits or exports."""
import sys,pathlib,json,hashlib,math
import bpy,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'export'))
from asset_utils import open_source,activate,positions,bones

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'astronaut'
INPUTS=[ROOT/'animated/m7.2/astronaut-assembled.blend',ROOT/'animated/m7.2/astronaut-animated-candidate.glb',
        ROOT/'animated/m7.2/astronaut-walk.fbx',ROOT/'animated/m7.2/astronaut-idle.fbx',ROOT/'prepared/m7.1/astronaut-meshy-textures-1024.glb']
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
def write(name,data): (HERE/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
assert not (HERE/'diagnosis.json').exists(),'Refusing to replace existing diagnosis'
before=hashes()
scene,rig,mesh=open_source()
scene.render.fps=30;scene.render.fps_base=1
walk=bpy.data.actions['Walk']
rest=np.asarray([mesh.matrix_world@v.co for v in mesh.data.vertices])
rest_bones={b.name:{'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local)} for b in rig.data.bones}
groups=[{mesh.vertex_groups[g.group].name:g.weight for g in v.groups} for v in mesh.data.vertices]
# The source is one mesh. Isolate boot/cuff regions using rest-space ankle height
# plus a conservative 0.12m cuff margin and side-of-body sign. Validate that these
# regions include every penetrating vertex; no dynamic region changes per frame.
masks={}
for side,sign in [('Left',1),('Right',-1)]:
    head=np.asarray(rest_bones['mixamorig:'+side+'Foot']['head'])
    assert sign*head[0]>0
    masks[side]=np.flatnonzero((rest[:,2]<=head[2]+.12)&(sign*rest[:,0]>0))
mask_all=set(int(i) for a in masks.values() for i in a)
activate(rig,bpy.data.actions['Idle'],1)
idle_pose=positions(mesh)
offset=-float(idle_pose[:,2].min())
frames=np.arange(1,32+.01,.125)
all_co=[];all_bones=[];samples=[]
for frame in frames:
    activate(rig,walk,frame)
    co=positions(mesh);co[:,2]+=offset
    mats=bones(rig);mats[:,2,3]+=offset
    all_co.append(co);all_bones.append(mats)
    sides={}
    for side,ids in masks.items():
        boot=co[ids]
        ankle=rig.pose.bones['mixamorig:'+side+'Foot']
        toe=rig.pose.bones['mixamorig:'+side+'ToeBase']
        ankle_world=rig.matrix_world@ankle.matrix
        toe_world=rig.matrix_world@toe.matrix
        q=ankle_world.to_quaternion().normalized()
        ankle_co=np.asarray(ankle_world.translation).copy();ankle_co[2]+=offset
        toe_co=np.asarray(toe_world.translation).copy();toe_co[2]+=offset
        low=int(ids[boot[:,2].argmin()])
        sides[side]={'minimum':float(boot[:,2].min()),'maximum':float(boot[:,2].max()),
            'lowestVertex':low,'lowestPosition':co[low].tolist(),'ankle':ankle_co.tolist(),'toe':toe_co.tolist(),
            'ankleQuaternionWxyz':list(q),'toeGround':float(toe_co[2]),
            'bootVerticesBelowMinus1mm':int(np.sum(boot[:,2]<-.001))}
    hips=rig.matrix_world@rig.pose.bones['mixamorig:Hips'].matrix
    penetrating=set(map(int,np.flatnonzero(co[:,2]<-.001)))
    assert not penetrating-mask_all, f'Boot mask misses penetrating vertices at {frame}'
    samples.append({'frame':float(frame),'time':float((frame-1)/30),'hipHeight':float(hips.translation.z+offset),
                    'wholeMeshMinimum':float(co[:,2].min()),'boots':sides})
all_co=np.asarray(all_co);all_bones=np.asarray(all_bones)

# The downloaded native Walk is without skin. Compare its actual evaluated joint
# poses, then apply those native world poses through the Idle inverse binds in a
# temporary copy of the approved target rig. Do not assign the native action.
existing=set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'animated/m7.2/astronaut-walk.fbx'))
temporary=set(bpy.data.objects)-existing
native=next(o for o in temporary if o.type=='ARMATURE')
native_action=native.animation_data.action
native_slot=native.animation_data.action_slot
assert not any(o.type=='MESH' for o in temporary),'Expected Without Skin FBX'
assert set(b.name for b in native.data.bones)==set(b.name for b in rig.data.bones)
names=[b.name for b in rig.pose.bones]
native_matrices=[];native_joint_error=[];rotation_error=[];native_deform=[]
native_hip=[];native_feet={'Left':[],'Right':[]}
inverse=rig.matrix_world.inverted()
for index,frame in enumerate(frames):
    activate(native,native_action,frame)
    mats={b.name:native.matrix_world@b.matrix for b in native.pose.bones}
    raw=np.asarray([mats[n] for n in names]);raw[:,2,3]+=offset
    native_matrices.append(raw)
    native_joint_error.extend(np.linalg.norm(raw[:,:3,3]-all_bones[index,:,:3,3],axis=1))
    for n,expected in zip(names,all_bones[index]):
        q=mats[n].to_quaternion().normalized()
        q0=__import__('mathutils').Matrix(expected.tolist()).to_quaternion().normalized()
        d=q.rotation_difference(q0)
        rotation_error.append(math.degrees(2*math.atan2(math.sqrt(d.x*d.x+d.y*d.y+d.z*d.z),abs(d.w))))
    native_hip.append(raw[names.index('mixamorig:Hips'),:3,3])
    for side in native_feet:native_feet[side].append(raw[names.index('mixamorig:'+side+'Foot'),:3,3])

# Clear only the target's action in this process, then build a rest-aware native
# pose on that same rig for an exact same-geometry counterfactual.
rig.animation_data.action=None
for index,frame in enumerate(frames):
    activate(native,native_action,frame)
    desired={b.name:inverse@(native.matrix_world@b.matrix) for b in native.pose.bones}
    for bone in rig.pose.bones:
        kwargs={'matrix':desired[bone.name],'matrix_local':bone.bone.matrix_local,'invert':True}
        if bone.parent:
            kwargs.update(parent_matrix=desired[bone.parent.name],parent_matrix_local=bone.parent.bone.matrix_local)
        bone.matrix_basis=bone.bone.convert_local_to_pose(**kwargs)
    bpy.context.view_layer.update()
    co=positions(mesh);co[:,2]+=offset
    native_deform.append(co)
native_deform=np.asarray(native_deform)
native_boot={side:native_deform[:,ids,2].min(axis=1) for side,ids in masks.items()}
native_mesh_error=np.linalg.norm(native_deform-all_co,axis=2)

# Kinematic contact inference, not measured physical contact. Stance is backward
# sole travel relative to this in-place character, with low boot height; transition
# and swing labels are kept separate for uncertainty around toe-off/heel-strike.
for side in masks:
    ankle=np.asarray([s['boots'][side]['ankle'] for s in samples])
    heights=np.asarray([s['boots'][side]['minimum'] for s in samples])
    velocity=np.gradient(ankle,(frames-1)/30,axis=0)
    for index,s in enumerate(samples):
        # Character faces -Y in Blender, so planted-foot travel is +Y.
        phase='stance' if velocity[index,1]>.08 and heights[index]<.04 else ('swing' if velocity[index,1]<-.08 else 'transition')
        s['boots'][side]['phase']=phase
        s['boots'][side]['ankleVelocity']=velocity[index].tolist()
        s['boots'][side]['nativeMinimum']=float(native_boot[side][index])

summary={}
for side,ids in masks.items():
    h=np.asarray([s['boots'][side]['minimum'] for s in samples])
    summary[side]={'vertices':len(ids),'restBoundsMin':rest[ids].min(axis=0).tolist(),'restBoundsMax':rest[ids].max(axis=0).tolist(),
        'minimumGroundClearance':float(h.min()),'maximumGroundClearance':float(h.max()),'worstFrame':float(frames[h.argmin()]),
        'nativeMinimumGroundClearance':float(native_boot[side].min()),
        'phaseCounts':{p:sum(s['boots'][side]['phase']==p for s in samples) for p in ['stance','swing','transition']}}
hip=np.asarray([s['hipHeight'] for s in samples])
required=np.maximum(0,-np.min(np.stack([np.asarray([s['boots'][side]['minimum'] for s in samples]) for side in masks]),axis=0))
global_clearance={side:np.asarray([s['boots'][side]['minimum'] for s in samples])+required for side in masks}
global_stance_float={side:float(max(global_clearance[side][i] for i,s in enumerate(samples) if s['boots'][side]['phase']=='stance')) for side in masks}
report={'inputs':before,'blender':bpy.app.version_string,'fps':30,'samplingStepFrames':.125,'sampleCount':len(frames),
    'idleReferenceOffset':offset,'bootRegionDefinition':'One mesh; fixed rest-space regions below ankle head + 0.12m, split by rest X side; every penetrating vertex lies in these regions',
    'bootSummaries':summary,'restFootAndToeBones':{n:v for n,v in rest_bones.items() if n.endswith(('Foot','ToeBase'))},
    'hipHeightRange':[float(hip.min()),float(hip.max())],
    'rootEndpointDrift':np.linalg.norm(all_bones[-1,names.index('mixamorig:Hips'),:2,3]-all_bones[0,names.index('mixamorig:Hips'),:2,3]).item(),
    'nativeComparison':{'walkHasSkin':False,'maximumJointPositionError':float(max(native_joint_error)),
        'meanJointPositionError':float(np.mean(native_joint_error)),'maximumRotationErrorDegrees':float(max(rotation_error)),
        'meanRotationErrorDegrees':float(np.mean(rotation_error)),
        'maximumSameGeometryVertexError':float(native_mesh_error.max()),'meanSameGeometryVertexError':float(native_mesh_error.mean()),
        'interpretation':'Native skeleton poses applied through the original Idle inverse binds produce the same boot intersection; no native skinned Walk mesh is available'},
    'rawGlobalLiftTest':{'maximumLift':float(required.max()),'meanLift':float(required.mean()),
        'hipRangeAfterLift':[float((hip+required).min()),float((hip+required).max())],
        'inferredStanceMaximumFloating':global_stance_float,
        'maximumLiftVelocity':float(np.abs(np.gradient(required,(frames-1)/30)).max())},
    'samples':samples,'sourceHashesUnchanged':hashes()==before}
write('diagnosis.json',report)
np.savez_compressed(HERE/'diagnosis-samples.npz',frames=frames,positions=all_co,boneMatrices=all_bones,
    nativePositions=native_deform,hip=hip,requiredGlobalLift=required,boneNames=np.asarray(names),
    leftBoot=masks['Left'],rightBoot=masks['Right'])
assert hashes()==before
print('DIAGNOSIS',json.dumps({k:v for k,v in report.items() if k not in ['samples','inputs','restFootAndToeBones']}),flush=True)
