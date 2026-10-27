"""Matched source/final renders; reference scenes are never saved."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *
before=hashes()
audit=json.loads((HERE/'export-validation.json').read_text())
from mathutils import Vector
captures=[('Idle',56,'front'),('Idle',56,'back'),('Walk',12,'front'),('Walk',23.75,'front')]
targets={}
baseline=dict(np.load(HERE/'source-samples.npz'))
targets['neck']=baseline['Idle_positions'][110,4251].copy()
targets['wrist']=baseline['Walk_positions'][352,9542].copy()
targets['boots']=np.array([0.,-.04,.14])
targets['knees']=np.array([0.,0.,.42])
for k in ['neck','wrist']:targets[k][2]+=audit['constantGroundOffset']
for version in ['source','final']:
    if version=='source':
        scene,rig,mesh=open_source()
        rig.location.z+=audit['constantGroundOffset']
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.render.fps=240
        bpy.ops.import_scene.gltf(filepath=str(OUTPUT))
        rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    camera=render_setup()
    for name,frame,view in ([] if '--close-only' in sys.argv else captures):
        activate(rig,bpy.data.actions[name],frame if version=='source' else (frame-1)*8)
        render(camera,HERE/f'{version}-{name.lower()}-{frame:g}-{view}.png',view)
    for region,name,frame in [('neck','Idle',56),('wrist','Walk',12),('knees','Walk',23),('boots','Walk',23.75)]:
        activate(rig,bpy.data.actions[name],frame if version=='source' else (frame-1)*8)
        target=Vector(targets[region])
        camera.location=target+Vector((-.7,-.6,.25)).normalized()*(.9 if region in ['neck','wrist'] else 1.6)
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.lens=55
        bpy.context.scene.render.filepath=str(HERE/f'{version}-close-{region}.png')
        bpy.ops.render.render(write_still=True)
assert hashes()==before
print('DEFORMATION_RENDERS_COMPLETE source hashes unchanged',flush=True)
