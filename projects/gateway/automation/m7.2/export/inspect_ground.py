"""Independent fresh-process ground review and engine-check reference points."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *
report=json.loads((HERE/'export-validation.json').read_text())
samples=dict(np.load(HERE/'source-samples.npz'))
names=list(samples['bone_names'])
engine_reference={'clips':{}, 'orientation':'Y-up, +Z-forward', 'sourceHashes':hashes()}
for clip,frames in [('Idle',[1,56,126,251]),('Walk',[1,8,12,16,24,32])]:
    selected=[]
    for frame in frames:
        index=int((frame-1)*2)
        heads=samples[clip+'_bones'][index,:,:3,3]
        selected.append({'time':(frame-1)/30,'sourceFrame':frame,
            'boneHeads':{name:[float(co[0]),float(co[2])+report['constantGroundOffset'],float(-co[1])] for name,co in zip(names,heads)}})
    engine_reference['clips'][clip]=selected
write_json('engine-reference.json',engine_reference)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUTPUT))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
frame=report['roundtrip']['Walk']['worstGroundSourceFrame']
activate(rig,bpy.data.actions['Walk'],frame-1)
co=positions(mesh)
feet={b.name:list(rig.matrix_world @ b.head) for b in rig.pose.bones if b.name.endswith(('LeftFoot','RightFoot','LeftToeBase','RightToeBase'))}
write_json('ground-inspection.json',{'sourceFrame':frame,'importedFrame':frame-1,'lowestVertex':int(co[:,2].argmin()),'lowestPosition':co[co[:,2].argmin()].tolist(),'footAndToeJointPositions':feet,'sourceHashesUnchanged':hashes()==report['sourceHashes']})
camera=render_setup()
render(camera,HERE/'walk-worst-ground-full.png','front')
camera.location=(1.5,-2.5,.7)
camera.rotation_euler=(Vector((0,0,.15))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=100
bpy.context.scene.render.filepath=str(HERE/'walk-worst-ground-boots.png')
bpy.ops.render.render(write_still=True)
assert hashes()==report['sourceHashes']
print('GROUND_REVIEW',frame,float(co[:,2].min()),flush=True)
