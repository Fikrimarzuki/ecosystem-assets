"""Read-only diagnosis of imported representation; no exports or saves."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(OUTPUT))
info={'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,
    'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler)} for o in bpy.context.scene.objects],
    'fps':bpy.context.scene.render.fps,'fpsBase':bpy.context.scene.render.fps_base,
    'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[{'id':s.identifier,'name':s.name_display} for s in a.slots]} for a in bpy.data.actions]}
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
m=next(o for o in bpy.context.scene.objects if o.type=='MESH')
info['tracks']=[{'name':t.name,'strips':[{'start':s.frame_start,'end':s.frame_end,'actionStart':s.action_frame_start,'actionEnd':s.action_frame_end,'slot':s.action_slot.identifier if s.action_slot else None} for s in t.strips]} for t in r.animation_data.nla_tracks]
for mode in ['REST','POSE']:
    r.data.pose_position=mode
    for frame in [0,1,12]:
        activate(r,bpy.data.actions['Idle'],frame)
        co=positions(m)
        info[f'{mode}-{frame}']={'min':co.min(axis=0).tolist(),'max':co.max(axis=0).tolist()}
write_json('roundtrip-diagnosis.json',info)
print('DIAGNOSIS',json.dumps(info),flush=True)
