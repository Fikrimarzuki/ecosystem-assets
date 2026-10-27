"""Blender 5.2.2: create a new assembled .blend; never overwrite inputs or export GLB."""
import bpy, pathlib, hashlib, json, math, statistics
from mathutils import Matrix, Vector

ROOT = pathlib.Path('D:/Code/porto-projects/gateway-assets/astronaut')
EVIDENCE = pathlib.Path(__file__).parent
INPUTS = {
    'working': ROOT / 'animated/m7.2/astronaut-working.blend',
    'walk': ROOT / 'animated/m7.2/astronaut-walk.fbx',
    'material': ROOT / 'prepared/m7.1/astronaut-meshy-textures-1024.glb',
}
OUTPUT = ROOT / 'animated/m7.2/astronaut-assembled.blend'
REPORT = EVIDENCE / 'assembly-validation.json'
EXPECTED = {
    'working': 'e94b8f926330ac07f8c8dda5d828269acf015d3ed836da8b84464f7a581898f4',
    'walk': 'cd11b0ba2434c0e575ce8f23a47eb3773367756984a1326c44946962274d7ff1',
    'material': 'fdd18dab76af15e1fcd171b7bae43f2061724ac471598f19de36c97f9a87ea68',
}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def curve_list(a):
    return [fc for layer in a.layers for strip in layer.strips for bag in getattr(strip, 'channelbags', []) for fc in bag.fcurves]
def action_fingerprint(a):
    values = [(fc.data_path, fc.array_index, [(tuple(k.co), k.interpolation, tuple(k.handle_left), tuple(k.handle_right)) for k in fc.keyframe_points]) for fc in curve_list(a)]
    return hashlib.sha256(repr(values).encode()).hexdigest()
def skin_snapshot(mesh):
    return {'vertices': [tuple(v.co) for v in mesh.data.vertices],
        'loops': [l.vertex_index for l in mesh.data.loops],
        'uv': [tuple(v.uv) for v in mesh.data.uv_layers.active.data],
        'groups': [g.name for g in mesh.vertex_groups],
        'weights': [[(g.group, g.weight) for g in v.groups] for v in mesh.data.vertices],
        'parent': mesh.parent.name, 'world': [tuple(r) for r in mesh.matrix_world],
        'modifiers': [(m.name, m.type, m.object.name if m.type == 'ARMATURE' and m.object else None) for m in mesh.modifiers]}
def angle_degrees(a, b):
    q1, q2 = a.to_quaternion().normalized(), b.to_quaternion().normalized()
    # acos(dot) overstates small errors in float32; quaternion difference's
    # vector part is stable around zero and is insensitive to equivalent signs.
    q = q1.rotation_difference(q2).normalized()
    return math.degrees(2 * math.atan2(math.sqrt(q.x*q.x+q.y*q.y+q.z*q.z), abs(q.w)))
def set_frame(frame):
    bpy.context.scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
    bpy.context.view_layer.update()
def bind_action(rig, action, slot):
    rig.animation_data.action = action
    rig.animation_data.action_slot = slot
def evaluated_points(mesh):
    obj = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [obj.matrix_world @ v.co for v in obj.data.vertices]

assert bpy.app.version == (5, 2, 2), bpy.app.version_string
assert not OUTPUT.exists(), 'Refusing to overwrite an existing assembled file'
assert {k: digest(p) for k,p in INPUTS.items()} == EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(INPUTS['working']), load_ui=False, use_scripts=False)
scene = bpy.context.scene
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in scene.objects if o.type == 'MESH')
idle = rig.animation_data.action
idle_slot = rig.animation_data.action_slot
idle_signature = action_fingerprint(idle)
skin = skin_snapshot(mesh)
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
assert all(b.rotation_mode == 'QUATERNION' for b in rig.pose.bones)
assert len(rig.data.bones) == 41
assert tuple(idle.frame_range) == (1, 251)
scene.render.fps = 30; scene.render.fps_base = 1

before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(INPUTS['walk']))
temporary_walk_objects = set(bpy.data.objects) - before
source = next(o for o in temporary_walk_objects if o.type == 'ARMATURE')
native_action = source.animation_data.action
assert tuple(native_action.frame_range) == (1, 32)
assert {b.name: b.parent.name if b.parent else None for b in source.data.bones} == {b.name: b.parent.name if b.parent else None for b in rig.data.bones}
assert not any(b.constraints for b in rig.pose.bones)
assert not rig.animation_data.nla_tracks

# Capture the native evaluated pose, not source F-curves. The inverse world
# transform converts it into the target armature's coordinate system. No bind
# bone, object transform, weight, parent or source action is changed.
frames = [float(f) for f in range(1, 33)]
check_frames = sorted(set(frames + [f + .5 for f in range(1, 32)]))
native = {}
for f in check_frames:
    set_frame(f)
    native[f] = {b.name: source.matrix_world @ b.matrix for b in source.pose.bones}
walk = bpy.data.actions.new('Walk')
slot = walk.slots.new('OBJECT', rig.name)
bind_action(rig, walk, slot)
previous_q = {}
inverse_world = rig.matrix_world.inverted()
for f in frames:
    set_frame(f)
    desired = {n: inverse_world @ m for n,m in native[f].items()}
    for bone in rig.pose.bones:
        kwargs = {'matrix': desired[bone.name], 'matrix_local': bone.bone.matrix_local, 'invert': True}
        if bone.parent:
            kwargs['parent_matrix'] = desired[bone.parent.name]
            kwargs['parent_matrix_local'] = bone.parent.bone.matrix_local
        basis = bone.bone.convert_local_to_pose(**kwargs)
        location, rotation, scale = basis.decompose()
        if bone.name in previous_q and rotation.dot(previous_q[bone.name]) < 0:
            rotation.negate()
        previous_q[bone.name] = rotation.copy()
        bone.location = location; bone.rotation_quaternion = rotation; bone.scale = scale
        for prop in ('location', 'rotation_quaternion', 'scale'):
            assert bone.keyframe_insert(prop, frame=f, group=bone.name)
for fc in curve_list(walk):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
walk.use_fake_user = True
idle.name = 'Idle'; idle.use_fake_user = True
assert action_fingerprint(idle) == idle_signature

position_errors = []; rotation_errors = []; scale_errors = []; sample_errors = []
for f in check_frames:
    set_frame(f)
    ps=[]; rs=[]
    for b in rig.pose.bones:
        actual = rig.matrix_world @ b.matrix; expected = native[f][b.name]
        p = (actual.translation - expected.translation).length
        r = angle_degrees(actual, expected)
        position_errors.append(p); rotation_errors.append(r)
        scale_errors.append((actual.to_scale() - expected.to_scale()).length)
        ps.append(p); rs.append(r)
    sample_errors.append({'frame': f, 'maximumPositionError': max(ps), 'maximumRotationErrorDegrees': max(rs)})
integer = [v for v in sample_errors if v['frame'].is_integer()]
subframe = [v for v in sample_errors if not v['frame'].is_integer()]
pose_summary = {
    'frames':len(check_frames), 'bonesPerFrame':len(rig.pose.bones),
    'maximumPositionError':max(position_errors), 'averagePositionError':statistics.mean(position_errors),
    'maximumRotationErrorDegrees':max(rotation_errors), 'averageRotationErrorDegrees':statistics.mean(rotation_errors),
    'maximumScaleError':max(scale_errors),
    'integerFrameMaximumPositionError':max(v['maximumPositionError'] for v in integer),
    'halfFrameMaximumPositionError':max(v['maximumPositionError'] for v in subframe),
    'samples':sample_errors,
}
assert pose_summary['maximumPositionError'] < .001, pose_summary
assert pose_summary['maximumRotationErrorDegrees'] < .25, pose_summary
assert max(scale_errors) < .00001

# Original GLB importer constructs the complete PBR graph and packed images.
# Assign that material to the existing skinned mesh, never replace mesh data.
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(INPUTS['material']))
material_objects = set(bpy.data.objects) - before
reference = next(o for o in material_objects if o.type == 'MESH')
assert len(reference.data.vertices) == len(mesh.data.vertices)
assert [l.vertex_index for l in reference.data.loops] == skin['loops']
assert [tuple(v.uv) for v in reference.data.uv_layers.active.data] == skin['uv']
material = reference.data.materials[0]
mesh.data.materials.clear(); mesh.data.materials.append(material)
material.name = 'AstronautOriginalPBR'
images = [n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE']
assert len(images) == 3
assert all(list(im.size) == [1024,1024] and im.packed_file for im in images)
connections = [(l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name) for l in material.node_tree.links]
for connection in [('TEX_IMAGE','Color','BSDF_PRINCIPLED','Base Color'), ('TEX_IMAGE','Color','NORMAL_MAP','Color'),
    ('NORMAL_MAP','Normal','BSDF_PRINCIPLED','Normal'), ('SEPARATE_COLOR','Blue','BSDF_PRINCIPLED','Metallic'),
    ('SEPARATE_COLOR','Green','BSDF_PRINCIPLED','Roughness')]: assert connection in connections
assert skin_snapshot(mesh) == skin
assert all(max(abs(rig.data.bones[n].matrix_local[i][j]-m[i][j]) for i in range(4) for j in range(4)) < 1e-6 for n,m in rest.items())

# Region edge changes flag possible deformation; they are not a visual-quality
# proof. Keep original weights intact and inspect contact sheets separately.
base_points = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
weights = [{mesh.vertex_groups[g.group].name:g.weight for g in v.groups} for v in mesh.data.vertices]
regions = {
    'helmet': {i for i,w in enumerate(weights) if w.get('mixamorig:Head',0)>.9},
    'backpack': {i for i,p in enumerate(base_points) if p.y>.2 and -.25<p.z<.35},
    'shoulders': {i for i,w in enumerate(weights) if max(w.get(n,0) for n in ['mixamorig:LeftShoulder','mixamorig:RightShoulder','mixamorig:LeftArm','mixamorig:RightArm'])>.35},
    'knees': {i for i,p in enumerate(base_points) if min((p-rig.matrix_world@rig.data.bones[n].head_local).length for n in ['mixamorig:LeftLeg','mixamorig:RightLeg'])<.14},
}
region_edges = {n:[tuple(e.vertices) for e in mesh.data.edges if all(i in ids for i in e.vertices) and (base_points[e.vertices[0]]-base_points[e.vertices[1]]).length>.00001] for n,ids in regions.items()}
deformation = {n:[] for n in regions}
def scan(action, action_slot):
    bind_action(rig,action,action_slot)
    lo,hi=map(int,action.frame_range); samples=[]
    for f in range(lo,hi+1):
        set_frame(float(f)); pts=evaluated_points(mesh)
        assert all(math.isfinite(c) for p in pts for c in p)
        hips=rig.matrix_world@rig.pose.bones['mixamorig:Hips'].head
        samples.append({'frame':f,'minimumZ':min(p.z for p in pts),'maximumZ':max(p.z for p in pts),'hipsWorld':list(hips),
            'leftFootWorld':list(rig.matrix_world@rig.pose.bones['mixamorig:LeftFoot'].head),
            'rightFootWorld':list(rig.matrix_world@rig.pose.bones['mixamorig:RightFoot'].head)})
        if action==walk:
            for n,edges in region_edges.items():
                deformation[n].extend((pts[a]-pts[b]).length/(base_points[a]-base_points[b]).length for a,b in edges)
    first,last=samples[0]['hipsWorld'],samples[-1]['hipsWorld']
    delta=[last[i]-first[i] for i in range(3)]
    return {'name':action.name,'range':[lo,hi],'durationSeconds':(hi-lo)/30,
        'groundMinimum':min(s['minimumZ'] for s in samples),'groundMaximumOfMinima':max(s['minimumZ'] for s in samples),
        'hipsEndMinusStart':delta,'horizontalAccumulatedMovement':math.hypot(delta[0],delta[1]),'samples':samples}
idle_scan=scan(idle,idle_slot);walk_scan=scan(walk,slot)
assert walk_scan['horizontalAccumulatedMovement']<.00001
for n,values in deformation.items():
    values.sort()
    deformation[n]={'vertices':len(regions[n]),'edgesPerFrame':len(region_edges[n]),
        'minEdgeLengthRatio':values[0] if values else None,'maxEdgeLengthRatio':values[-1] if values else None,
        'p95EdgeLengthRatio':values[int(.95*(len(values)-1))] if values else None}

# Delete only temporary objects in memory; clean unused import datablocks so
# there is one intended mesh, rig, material and exactly two persistent actions.
for o in list(bpy.data.objects):
    if o not in (rig,mesh): bpy.data.objects.remove(o,do_unlink=True)
for a in list(bpy.data.actions):
    if a not in (idle,walk): bpy.data.actions.remove(a,do_unlink=True)
for data in (bpy.data.meshes,bpy.data.armatures,bpy.data.materials,bpy.data.images):
    for block in list(data):
        if block.users==0: data.remove(block)
# Removing orphan materials can release old missing images; clear those too.
for im in list(bpy.data.images):
    if im.users==0: bpy.data.images.remove(im)
assert len(bpy.data.objects)==2
assert len(bpy.data.meshes)==1 and len(bpy.data.armatures)==1
assert sorted(a.name for a in bpy.data.actions)==['Idle','Walk']
bind_action(rig,idle,idle_slot);set_frame(1.)
scene.frame_start=1;scene.frame_end=251
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
scene.timeline_markers.new('Idle: 1-251 (8.333s)',frame=1)
scene.timeline_markers.new('Walk: 1-32 (1.033s); choose Walk action',frame=32)
rig['assembly_note']='Idle unchanged; Walk rest-aware local-channel bake from native world poses. Two fake-user actions; no NLA blending.'
rig['walk_frames']='1-32';rig['idle_frames']='1-251'
bpy.context.view_layer.objects.active=rig
for o in scene.objects:o.select_set(o==rig)
report={'blender':bpy.app.version_string,'inputs':EXPECTED,'output':str(OUTPUT),'method':'Native evaluated world poses -> target armature space -> target rest/parent-aware local basis -> quaternion-continuous 30fps bake; original bind/weights unchanged',
    'poseErrors':pose_summary,'clips':[idle_scan,walk_scan],'deformation':deformation,
    'material':{'name':material.name,'connections':connections,'images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'colorSpace':im.colorspace_settings.name} for im in images]},
    'preservation':{'idleCurveFingerprint':idle_signature,'idleCurvesUnchanged':action_fingerprint(idle)==idle_signature,'meshAndSkinUnchanged':skin_snapshot(mesh)==skin,'boneRestTransformsUnchanged':True},
    'objects':[{'name':o.name,'type':o.type} for o in scene.objects],
    'risks':['Auto skinning has up to six influences; no weights changed.','Ground penetration reported, not hidden by per-frame root correction.','Manual visual review and GLB export validation remain necessary.']}
assert {k:digest(p) for k,p in INPUTS.items()}==EXPECTED
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),check_existing=True)
assert {k:digest(p) for k,p in INPUTS.items()}==EXPECTED
report['outputSha256']=digest(OUTPUT)
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print('ASSEMBLY_SUMMARY '+json.dumps({**report,'poseErrors':{k:v for k,v in pose_summary.items() if k!='samples'},'clips':[{k:v for k,v in c.items() if k!='samples'} for c in report['clips']]}))
