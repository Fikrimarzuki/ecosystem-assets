"""Matching source/candidate neck and wrist closeups at measured worst frames."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *
before=hashes()
audit=json.loads((HERE/'export-validation.json').read_text())
analysis=json.loads((HERE/'skinning-analysis.json').read_text())
baseline=dict(np.load(HERE/'source-samples.npz'))
targets={}
for name in ['Idle','Walk']:
    result=analysis['clips'][name]
    frame=result['worstFrame']
    target=baseline[name+'_positions'][int((frame-1)*2),result['worstVertex']].copy()
    target[2]+=audit['constantGroundOffset']
    targets[name]=target
for version in ['approved-source','candidate']:
    if version=='approved-source':
        scene,rig,mesh=open_source()
        rig.location.z+=audit['constantGroundOffset']
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.render.fps=30
        bpy.ops.import_scene.gltf(filepath=str(OUTPUT))
        rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    camera=render_setup()
    bpy.context.scene.render.resolution_x=512
    bpy.context.scene.render.resolution_y=512
    for name in ['Idle','Walk']:
        frame=analysis['clips'][name]['worstFrame']
        activate(rig,bpy.data.actions[name],frame if version=='approved-source' else frame-1)
        target=Vector(targets[name])
        distance=.45 if name=='Idle' else .37
        camera.location=target+Vector((-.7,-.6,.25)).normalized()*distance
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.lens=55
        bpy.context.scene.render.filepath=str(HERE/f'closeup-{version}-{name.lower()}.png')
        bpy.ops.render.render(write_still=True)
assert hashes()==before
print('CLOSEUPS_COMPLETE Source files unchanged',flush=True)
