"""Measure four-influence reduction against every integer and half source frame."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *

assert not (HERE / 'source-samples.npz').exists(), 'Refusing to overwrite inspection evidence'
before = hashes()
scene, rig, mesh = open_source()
original_weights = [[(g.group, g.weight) for g in v.groups] for v in mesh.data.vertices]
bone_names = [b.name for b in rig.pose.bones]
rest = np.asarray([mesh.matrix_world @ v.co for v in mesh.data.vertices])
samples = {'rest': rest, 'bone_names': np.asarray(bone_names)}
report = {'sourceHashes': before, 'blender': bpy.app.version_string, 'units': 'Blender world units (nominal meters; no rescale)',
          'originalInfluenceCounts': {str(n): sum(sum(g.weight > 0 for g in v.groups) == n for v in mesh.data.vertices) for n in range(1,7)}, 'clips': {}}
for name, end in [('Idle',251), ('Walk',32)]:
    frames = np.arange(1, end + .1, .5)
    coords, matrices, skins = [], [], []
    for frame in frames:
        activate(rig, bpy.data.actions[name], frame)
        coords.append(positions(mesh))
        matrices.append(bones(rig))
        skins.append(skin_matrices(rig))
    samples[name + '_frames'] = frames
    samples[name + '_positions'] = np.asarray(coords)
    samples[name + '_bones'] = np.asarray(matrices)
    samples[name + '_skins'] = np.asarray(skins)
    print('SOURCE_SAMPLED', name, len(frames), flush=True)
affected, dropped = limit_weights(mesh)
report['fourInfluenceReduction'] = {'affectedVertices': len(affected), 'droppedWeight': stats(dropped), 'normalization': 'Top four positive weights retained and normalized, only in this temporary scene'}
captures = []
for name in ['Idle','Walk']:
    frame_errors = []
    minimums = []
    worst = (0, 0, 0)
    for index, frame in enumerate(samples[name + '_frames']):
        activate(rig, bpy.data.actions[name], frame)
        co = positions(mesh)
        error = np.linalg.norm(co - samples[name + '_positions'][index], axis=1)
        frame_errors.append(error)
        minimums.append(float(co[:,2].min()))
        if error.max() > worst[0]:
            worst = (float(error.max()), float(frame), int(error.argmax()))
    frame_errors = np.asarray(frame_errors)
    source_min = samples[name + '_positions'][:,:,2].min(axis=1)
    root_index = bone_names.index('mixamorig:Hips')
    root = samples[name + '_bones'][:,root_index,:3,3]
    report['clips'][name] = {'sampleCount': len(frame_errors), 'frameRange': [1,251 if name == 'Idle' else 32],
        'durationSeconds': (250 if name == 'Idle' else 31)/30,
        'allVertexErrors': stats(frame_errors), 'affectedVertexErrors': stats(frame_errors[:,affected]),
        'worstFrame': worst[1], 'worstVertex': worst[2], 'worstVertexWeights': [(mesh.vertex_groups[g].name,w) for g,w in original_weights[worst[2]]],
        'sourceGroundMinimum': float(source_min.min()), 'fourInfluenceGroundMinimum': min(minimums),
        'sourceRootEndpointHorizontalDrift': float(np.linalg.norm((root[-1]-root[0])[:2])),
        'sourceRootHorizontalRange': np.ptp(root[:,:2],axis=0).tolist()}
    captures.append((name,worst[1]))
    print('SKIN_ERROR', name, json.dumps(report['clips'][name]), flush=True)
# Keep the nominal Idle reference pose on the floor. Do not alter animated hips,
# vertically lock gait, or move all poses above the deepest source boot penetration.
ground_offset = -float(samples['Idle_positions'][0,:,2].min())
report['proposedConstantGroundOffset'] = ground_offset
report['captures'] = captures
np.savez_compressed(HERE / 'source-samples.npz', **samples)
write_json('skinning-analysis.json', report)

# Original versus four-influence comparisons at each clip's worst error frame.
rig.location.z += ground_offset
camera = render_setup()
for version in ['four-influence','approved-source']:
    if version == 'approved-source':
        for group in mesh.vertex_groups:
            group.remove(list(range(len(mesh.data.vertices))))
        for index, groups in enumerate(original_weights):
            for group, weight in groups:
                mesh.vertex_groups[group].add([index], weight, 'REPLACE')
    for name, frame in captures:
        activate(rig, bpy.data.actions[name], frame)
        for view in ['front','back']:
            render(camera, HERE / f'{version}-{name.lower()}-{frame:g}-{view}.png', view)
assert hashes() == before
print('MEASURE_COMPLETE Source hashes unchanged', flush=True)
