"""Export a new local candidate, inspect its binary, and reimport into an empty scene.

No .blend is saved. Source assets are hash guarded. Existing output is never replaced.
Four-influence changes exist only in the export process, following measured/rendered
comparisons. Absolute joint heads and relative world rotations avoid comparing
incompatible Blender bone roll conventions on roundtrip.
"""
import sys
import pathlib
import struct
import math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *
from mathutils import Matrix, Quaternion
from mathutils.kdtree import KDTree

validate_only = '--validate-only' in sys.argv
assert validate_only or not OUTPUT.exists(), 'Refusing to overwrite an existing asset'
assert not validate_only or OUTPUT.exists(), 'Candidate does not exist'
analysis = json.loads((HERE / 'skinning-analysis.json').read_text())
before = hashes()
assert before == analysis['sourceHashes']
baseline = dict(np.load(HERE / 'source-samples.npz'))
scene, rig, mesh = open_source()
scene.render.fps = 30
scene.render.fps_base = 1
assert all(not m.use_deform_preserve_volume for m in mesh.modifiers if m.type == 'ARMATURE')
rest = np.asarray([mesh.matrix_world @ v.co for v in mesh.data.vertices])
# Correct the rest-only snapshot; animation snapshots use evaluated mesh world
# transforms and are independent of this field. Do not repeat successful sampling.
baseline['rest'] = rest
np.savez_compressed(HERE / 'source-samples.npz', **baseline)
mesh.data.calc_loop_triangles()
triangles = len(mesh.data.loop_triangles)
affected, dropped = limit_weights(mesh)
assert len(affected) == analysis['fourInfluenceReduction']['affectedVertices']
offset = float(analysis['proposedConstantGroundOffset'])
rig.location.z += offset
bpy.context.view_layer.update()
limited = {}
for name in ['Idle','Walk']:
    co = []
    for frame in baseline[name + '_frames']:
        activate(rig, bpy.data.actions[name], frame)
        co.append(positions(mesh))
    limited[name] = np.asarray(co)
source_uv = [set() for _ in mesh.data.vertices]
for loop in mesh.data.loops:
    source_uv[loop.vertex_index].add(tuple(mesh.data.uv_layers.active.data[loop.index].uv))
tiny_weight_vertices = sum(any(0 < g.weight <= .0001 for g in v.groups) for v in mesh.data.vertices)
# Blender's installed glTF exporter drops weights <= 0.0001 before normalizing.
# Use that inspected rule for identity matching; deformation comparison still
# uses the untouched four-influence input and measures the cleanup's actual cost.
source_weights = [{mesh.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight > .0001} for v in mesh.data.vertices]
for weights_by_name in source_weights:
    total = sum(weights_by_name.values())
    for name in weights_by_name:
        weights_by_name[name] /= total

# Independent actions: active Idle + one stashed, muted Walk track. No duplicate
# Idle NLA strip and no multi-action track. Nothing is written back to the blend.
activate(rig, bpy.data.actions['Idle'], 1)
walk = bpy.data.actions['Walk']
track = rig.animation_data.nla_tracks.new()
track.name = 'Walk'
strip = track.strips.new('Walk', 1, walk)
strip.action_slot = walk.slots[0]
strip.action_frame_start = 1
strip.action_frame_end = 32
track.mute = True
track.lock = True
for obj in scene.objects:
    obj.select_set(False)
mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
settings = dict(filepath=str(OUTPUT), export_format='GLB', use_selection=True,
    export_yup=True, export_apply=False, export_materials='EXPORT', export_image_format='AUTO',
    export_animations=True, export_animation_mode='ACTIONS', export_frame_range=False,
    export_frame_step=1, export_force_sampling=True, export_anim_slide_to_zero=True,
    export_reset_pose_bones=True, export_current_frame=True, export_rest_position_armature=False,
    export_optimize_animation_size=True, export_skins=True, export_influence_nb=4,
    export_all_influences=False, export_def_bones=False, export_leaf_bone=False,
    export_armature_object_remove=False, export_morph=False, export_cameras=False, export_lights=False,
    export_draco_mesh_compression_enable=False, export_use_gltfpack=False)
if not validate_only:
    assert bpy.ops.export_scene.gltf(**settings) == {'FINISHED'}
    print('EXPORTED', str(OUTPUT), OUTPUT.stat().st_size, flush=True)
else:
    print('VALIDATE_ONLY Candidate bytes are not rewritten', flush=True)

checks = []
def check(name, passed, detail=None):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

blob = OUTPUT.read_bytes()
magic, version, length = struct.unpack_from('<4sII', blob)
assert magic == b'glTF' and version == 2 and length == len(blob)
chunks = {}
cursor = 12
while cursor < len(blob):
    n, kind = struct.unpack_from('<II', blob, cursor)
    assert n % 4 == 0 and cursor + 8 + n <= len(blob)
    chunks[kind] = blob[cursor + 8:cursor + 8 + n]
    cursor += 8 + n
assert cursor == len(blob)
gltf = json.loads(chunks[0x4E4F534A])
binary = chunks[0x004E4942]
assert len(gltf['buffers']) == 1 and 'uri' not in gltf['buffers'][0]
assert gltf['buffers'][0]['byteLength'] <= len(binary)
for view in gltf['bufferViews']:
    assert view.get('buffer',0) == 0 and view.get('byteOffset',0) + view['byteLength'] <= len(binary)

def accessor(index):
    a = gltf['accessors'][index]
    assert 'sparse' not in a
    v = gltf['bufferViews'][a['bufferView']]
    dtype = {5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    size = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    itemsize = np.dtype(dtype).itemsize
    stride = v.get('byteStride', itemsize * size)
    offset_bytes = v.get('byteOffset',0) + a.get('byteOffset',0)
    assert offset_bytes + (a['count']-1)*stride + size*itemsize <= v.get('byteOffset',0)+v['byteLength']
    data = np.ndarray((a['count'],size), dtype=dtype, buffer=binary, offset=offset_bytes, strides=(stride,itemsize)).copy()
    if a.get('normalized'):
        data = data / np.iinfo(dtype).max
    return data

check('one mesh and material', len(gltf.get('meshes',[])) == len(gltf.get('materials',[])) == 1)
check('one skin', len(gltf.get('skins',[])) == 1)
skin = gltf['skins'][0]
joint_names = [gltf['nodes'][i]['name'] for i in skin['joints']]
check('41 original joints', len(joint_names) == 41 and set(joint_names) == set(baseline['bone_names']))
inverse_bind = accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
check('valid inverse bind matrices', np.isfinite(inverse_bind).all() and len(inverse_bind) == 41 and np.all(np.abs(np.linalg.det(inverse_bind)) > 1e-9))
primitive = gltf['meshes'][0]['primitives'][0]
attrs = primitive['attributes']
weights, joints = accessor(attrs['WEIGHTS_0']), accessor(attrs['JOINTS_0'])
indices = accessor(primitive['indices'])
check('triangles unchanged', len(indices)//3 == triangles == 10357)
check('four-influence skin', 'JOINTS_1' not in attrs and 'WEIGHTS_1' not in attrs and weights.shape[1] == 4)
check('finite normalized weights and valid joints', np.isfinite(weights).all() and (weights >= 0).all() and np.max(np.abs(weights.sum(axis=1)-1)) < 1e-6 and joints.max() < 41)
check('valid geometry accessors', np.isfinite(accessor(attrs['POSITION'])).all() and int(indices.max()) < len(weights))
clips = {}
for animation in gltf['animations']:
    times = [accessor(s['input']).ravel() for s in animation['samplers']]
    assert all(np.isfinite(t).all() and np.all(np.diff(t)>0) for t in times)
    clips[animation['name']] = {'start': min(float(t.min()) for t in times), 'end': max(float(t.max()) for t in times),
                               'channels': len(animation['channels'])}
check('two independent named clips', sorted(clips) == ['Idle','Walk'] and len(gltf['animations']) == 2)
check('correct clip durations', abs(clips['Idle']['end'] - 250/30) < 1e-5 and abs(clips['Walk']['end'] - 31/30) < 1e-5 and all(c['start'] == 0 for c in clips.values()))
images = []
for image in gltf['images']:
    view = gltf['bufferViews'][image['bufferView']]
    payload = binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
    assert payload[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack_from('>II',payload,16)
    images.append({'name': image.get('name'), 'bytes':len(payload), 'dimensions':[width,height], 'sha256':hashlib.sha256(payload).hexdigest()})
original = (ASSETS / 'prepared/m7.1/astronaut-meshy-textures-1024.glb').read_bytes()
jn = struct.unpack_from('<I',original,12)[0]
og = json.loads(original[20:20+jn])
ob = original[28+jn:]
original_image_hashes = []
for image in og['images']:
    view = og['bufferViews'][image['bufferView']]
    original_image_hashes.append(hashlib.sha256(ob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]).hexdigest())
check('three embedded 1024px PNG textures', len(images) == 3 and all(i['dimensions'] == [1024,1024] for i in images))
check('original texture bytes unchanged', sorted(i['sha256'] for i in images) == sorted(original_image_hashes))
material = gltf['materials'][0]
pbr = material['pbrMetallicRoughness']
bindings = {'baseColor':pbr.get('baseColorTexture'), 'normal':material.get('normalTexture'), 'metallicRoughness':pbr.get('metallicRoughnessTexture')}
check('all PBR texture slots linked', all(b is not None for b in bindings.values()))
check('no external URI or required decoder', all('uri' not in i for i in gltf['images']) and not gltf.get('extensionsRequired'))

report = {'sourceHashes': before, 'blender': bpy.app.version_string, 'output':str(OUTPUT),
    'fileBytes':len(blob), 'sha256':hashlib.sha256(blob).hexdigest(), 'triangleCount':triangles,
    'gltfVertexCount':len(weights), 'settings':settings, 'clips':clips, 'images':images,
    'PBRBindings':bindings, 'constantGroundOffset':offset, 'skinningReduction':analysis['fourInfluenceReduction'],
    'exporterTinyWeightCleanup':{'thresholdInclusive':.0001,'verticesAffected':tiny_weight_vertices,'deformationIncludedInExportInputComparison':True},
    'checks':checks, 'roundtrip':{}, 'orientation':'Y-up / +Z-forward; Blender Z-up / -Y-forward; no rescaling or facing rotation'}
write_json('export-validation.json', report)

# Fresh scene: no source objects/actions/materials survive this reset.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.context.scene.render.fps_base = 1
assert len(bpy.data.objects) == 0 and len(bpy.data.actions) == 0
bpy.ops.import_scene.gltf(filepath=str(OUTPUT))
scene = bpy.context.scene
rigs = [o for o in scene.objects if o.type == 'ARMATURE']
meshes = [o for o in scene.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]
check('fresh Blender one mesh one armature', len(meshes) == len(rigs) == 1)
rig, mesh = rigs[0], meshes[0]
helpers = [o for o in scene.objects if o.type == 'MESH' and o != mesh]
report['importerDisplayHelpers'] = [{'name':o.name, 'usedAsBoneDisplay':any(b.custom_shape == o for b in rig.pose.bones)} for o in helpers]
check('no unexpected imported mesh', all(h['usedAsBoneDisplay'] for h in report['importerDisplayHelpers']))
check('fresh Blender two named actions', sorted(a.name for a in bpy.data.actions) == ['Idle','Walk'])
check('fresh Blender valid armature modifier', any(m.type == 'ARMATURE' and m.object == rig for m in mesh.modifiers))
check('fresh Blender 41 named bones', set(b.name for b in rig.data.bones) == set(joint_names))
check('fresh Blender three material maps', len([n for n in mesh.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]) == 3)
# Imported action keys start at zero; source keys start at one. The imported
# edit-bone rest pose can differ due to importer bind reconstruction, so establish
# vertex correspondence in the same *animated* Idle reference pose instead.
activate(rig, bpy.data.actions['Idle'], 0)
import_rest = positions(mesh)
tree = KDTree(len(limited['Idle'][0]))
for index, co in enumerate(limited['Idle'][0]):
    tree.insert(co, index)
tree.balance()
mapping = []
distances = []
ambiguity_error = 0.0
import_uv = [set() for _ in mesh.data.vertices]
for loop in mesh.data.loops:
    import_uv[loop.vertex_index].add(tuple(mesh.data.uv_layers.active.data[loop.index].uv))
import_weights = [{mesh.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight > 0} for v in mesh.data.vertices]
uv_errors = []
weight_errors = []
def attribute_errors(target, source):
    uv_error = max(min(np.linalg.norm(np.asarray(uv)-su) for su in source_uv[source]) for uv in import_uv[target])
    iw, sw = import_weights[target], source_weights[source]
    weight_error = max(abs(iw.get(n,0)-sw.get(n,0)) for n in set(iw) | set(sw))
    return float(uv_error), float(weight_error)
for target, co in enumerate(import_rest):
    options = []
    for _, index, distance in tree.find_range(co, 5e-5):
        ue, we = attribute_errors(target,index)
        if ue < 1e-6 and we < 1e-6:
            options.append((distance,index,ue,we))
    if not options:
        _, near, distance = tree.find(co)
        detail = {'importedVertex':target,'nearestSourceVertex':near,'distance':distance,'attributeErrors':attribute_errors(target,near),
                  'importedUv':list(import_uv[target]),'sourceUv':list(source_uv[near]),
                  'importedWeights':import_weights[target],'sourceWeights':source_weights[near]}
        write_json('correspondence-diagnosis.json',detail)
        print('CORRESPONDENCE_DIAGNOSIS',json.dumps(detail),flush=True)
        raise AssertionError(f'No position/UV/skin correspondence for imported vertex {target}')
    distance, index, ue, we = min(options)
    mapping.append(index)
    distances.append(distance)
    uv_errors.append(ue)
    weight_errors.append(we)
    # Coincident vertices from UV seams must have equivalent trajectories. Do not
    # quietly substitute one distinct skin trajectory for another.
    alternatives = [i for d,i,ue,we in options if i != index and d <= distance + 1e-7]
    for alternative in alternatives:
        ambiguity_error = max(ambiguity_error, max(float(np.linalg.norm(limited[name][:,index]-limited[name][:,alternative],axis=1).max()) for name in ['Idle','Walk']))
mapping = np.asarray(mapping)
report['vertexCorrespondence'] = {'maxReferenceDistance':max(distances), 'meanReferenceDistance':float(np.mean(distances)),
    'maxUvError':max(uv_errors), 'maxBoneWeightError':max(weight_errors),
    'importedVertices':len(mapping), 'sourceVertices':len(rest), 'coincidentTrajectoryMaxDifference':ambiguity_error,
    'method':'Animated Idle reference positions within 50 micrometers, UV and named bone weights within 1e-6; coincident trajectories independently checked'}
check('vertex correspondence reliable', max(distances) < 5e-5 and ambiguity_error < 1e-5 and max(uv_errors) < 1e-6 and max(weight_errors) < 1e-6)
bone_order = [list(baseline['bone_names']).index(b.name) for b in rig.pose.bones]

def rotations(matrices):
    u, _, vt = np.linalg.svd(matrices[:,:3,:3])
    return u @ vt

activate(rig, bpy.data.actions['Idle'], 0)
import_initial = bones(rig)
source_initial = baseline['Idle_bones'][0][bone_order].copy()
source_initial[:,2,3] += offset
import_r0 = rotations(import_initial)
source_r0 = rotations(source_initial)
all_imported = {}
for name in ['Idle','Walk']:
    action = bpy.data.actions[name]
    expected_frames = (0,250) if name == 'Idle' else (0,31)
    check(name + ' imported duration', max(abs(float(a)-b) for a,b in zip(action.frame_range,expected_frames)) < 1e-3)
    mesh_errors, export_errors, head_errors, angle_errors, coords_all, roots = [],[],[],[],[],[]
    ground_minima = []
    worst = (0,0,0)
    for index, frame in enumerate(baseline[name + '_frames']):
        activate(rig, action, frame - 1)
        co = positions(mesh)
        coords_all.append(co)
        original_co = baseline[name + '_positions'][index][mapping].copy()
        original_co[:,2] += offset
        original_error = np.linalg.norm(co - original_co, axis=1)
        export_error = np.linalg.norm(co - limited[name][index][mapping],axis=1)
        mesh_errors.append(original_error)
        export_errors.append(export_error)
        if original_error.max() > worst[0]:
            worst = (float(original_error.max()),float(frame),int(original_error.argmax()))
        current = bones(rig)
        expected = baseline[name + '_bones'][index][bone_order].copy()
        expected[:,2,3] += offset
        head_errors.extend(np.linalg.norm(current[:,:3,3] - expected[:,:3,3],axis=1))
        source_motion = rotations(expected) @ source_r0.transpose(0,2,1)
        import_motion = rotations(current) @ import_r0.transpose(0,2,1)
        difference = source_motion.transpose(0,2,1) @ import_motion
        angles = np.degrees(np.arccos(np.clip((np.trace(difference,axis1=1,axis2=2)-1)/2,-1,1)))
        angle_errors.extend(angles)
        roots.append(current[[b.name for b in rig.pose.bones].index('mixamorig:Hips'),:3,3])
        ground_minima.append(float(co[:,2].min()))
    all_imported[name] = np.asarray(coords_all)
    roots = np.asarray(roots)
    result = {'framesCompared':len(mesh_errors), 'jointComparisons':len(head_errors),
        'meshVsApprovedSource':stats(mesh_errors), 'meshVsFourInfluenceExportInput':stats(export_errors),
        'jointHeadPositionError':stats(head_errors), 'jointRelativeWorldRotationErrorDegrees':stats(angle_errors),
        'worstMeshFrame':worst[1], 'worstImportedVertex':worst[2],
        'minimumGroundZ':min(ground_minima), 'groundMinimaRange':[min(ground_minima),max(ground_minima)],
        'worstGroundSourceFrame':float(baseline[name + '_frames'][int(np.argmin(ground_minima))]),
        'worstGroundVerticesBelowFloor':int(np.sum(coords_all[int(np.argmin(ground_minima))][:,2] < -.001)),
        'rootEndpointHorizontalDrift':float(np.linalg.norm((roots[-1]-roots[0])[:2])),
        'rootHorizontalRange':np.ptp(roots[:,:2],axis=0).tolist(),
        'referenceBoundsMin':coords_all[0].min(axis=0).tolist(), 'referenceBoundsMax':coords_all[0].max(axis=0).tolist()}
    report['roundtrip'][name] = result
    check(name + ' joint positions preserved', result['jointHeadPositionError']['max'] < .001)
    check(name + ' joint motion preserved', result['jointRelativeWorldRotationErrorDegrees']['max'] < .1)
    check(name + ' export input deformation preserved', result['meshVsFourInfluenceExportInput']['max'] < .001)
    check(name + ' no accumulated horizontal root drift', result['rootEndpointHorizontalDrift'] < .0001)
    print('ROUNDTRIP',name,json.dumps(result),flush=True)
check('Idle reference grounded', abs(report['roundtrip']['Idle']['referenceBoundsMin'][2]) < 1e-5)
check('Walk floor clearance within 1mm', report['roundtrip']['Walk']['minimumGroundZ'] >= -.001,
      'A diagnostic clearance criterion, not a gait correction; existing source penetration is retained.')
report['sourceHashesUnchanged'] = hashes() == before
report['technicalChecksPassedExceptGrounding'] = all(c['passed'] for c in checks if c['name'] != 'Walk floor clearance within 1mm')
report['allChecksPassed'] = all(c['passed'] for c in checks)
report['status'] = 'CANDIDATE: review four-influence deformation and retained Walk ground penetration before final approval'
write_json('export-validation.json', report)

if '--no-renders' not in sys.argv:
    camera = render_setup()
    for name, frame in analysis['captures']:
        activate(rig,bpy.data.actions[name],frame - 1)
        for view in ['front','back']:
            render(camera,HERE / f'roundtrip-{name.lower()}-{frame:g}-{view}.png',view)
assert hashes() == before
assert report['sourceHashesUnchanged']
print('VALIDATION_COMPLETE',json.dumps({'allChecksPassed':report['allChecksPassed'], 'technicalChecksPassedExceptGrounding':report['technicalChecksPassedExceptGrounding'], 'failed':[c for c in checks if not c['passed']]}),flush=True)
