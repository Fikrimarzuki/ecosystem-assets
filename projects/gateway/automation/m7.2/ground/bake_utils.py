"""Construct a separate Walk action from measured per-foot correction curves."""
from ground_utils import *
CHANGED=[f'mixamorig:{side}{bone}' for side in ['Left','Right'] for bone in ['UpLeg','Leg','Foot']]

def gather_keys(rig,original):
    correction=dict(np.load(HERE/'correction-final-curves.npz'))
    frames=correction['frames']
    values=[];last={}
    for index,frame in enumerate(frames):
        activate(rig,original,frame)
        world=original_world(rig)
        for side in ['Left','Right']:solve_leg(rig,side,correction[side.lower()][index],world)
        row=[]
        for name in CHANGED:
            bone=rig.pose.bones[name]
            q=bone.rotation_quaternion.copy().normalized()
            if name in last and q.dot(last[name])<0:q.negate()
            last[name]=q.copy()
            row.append(list(bone.location)+list(q))
        values.append(row)
    keys={'frames':frames,'values':np.asarray(values),'boneNames':np.asarray(CHANGED)}
    np.savez_compressed(HERE/'baked-leg-keys.npz',**keys)
    return keys

def make_action(rig,original,keys):
    result=original.copy()
    result.name='Walk_GroundReview'
    bag=result.layers[0].strips[0].channelbags[0]
    for fc in list(bag.fcurves):
        if any(fc.data_path==f'pose.bones["{n}"].{p}' for n in CHANGED for p in ['location','rotation_quaternion']):bag.fcurves.remove(fc)
    for bone_index,name in enumerate(CHANGED):
        for prop,start,size in [('location',0,3),('rotation_quaternion',3,4)]:
            for component in range(size):
                fc=bag.fcurves.new(data_path=f'pose.bones["{name}"].{prop}',index=component)
                group=bag.groups.get(name) or bag.groups.new(name)
                fc.group=group
                co=np.column_stack([keys['frames'],keys['values'][:,bone_index,start+component]]).ravel()
                fc.keyframe_points.add(len(keys['frames']))
                fc.keyframe_points.foreach_set('co',co)
                interpolation=bpy.types.Keyframe.bl_rna.properties['interpolation'].enum_items['LINEAR'].value
                fc.keyframe_points.foreach_set('interpolation',[interpolation]*len(keys['frames']))
                fc.update()
    result.use_fake_user=True
    assert bone_action_hash(original,CHANGED)==bone_action_hash(result,CHANGED)
    return result

def skin_hash(mesh,rig):
    return hashlib.sha256(repr(([tuple(v.co) for v in mesh.data.vertices],[tuple(e.vertices) for e in mesh.data.edges],
        [l.vertex_index for l in mesh.data.loops],[tuple(u.uv) for u in mesh.data.uv_layers.active.data],
        [[(g.group,g.weight) for g in v.groups] for v in mesh.data.vertices],[g.name for g in mesh.vertex_groups],
        [tuple(r) for r in mesh.matrix_world],[tuple(r) for r in rig.matrix_world],
        [(b.name,[tuple(r) for r in b.matrix_local]) for b in rig.data.bones],
        [(m.name,m.type,m.object.name if m.type=='ARMATURE' else None) for m in mesh.modifiers],
        [(n.image.name,hashlib.sha256(n.image.packed_file.data).hexdigest()) for n in mesh.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE'])).encode()).hexdigest()
