"""Read corrected source; collect independent dense evidence without saving a blend."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from asset_utils import *

assert not (HERE / 'source-samples.npz').exists()
before = hashes()
scene, rig, mesh = open_source()
scene.render.fps = 30
offset = .009607551704849298
rest = np.asarray([mesh.matrix_world @ v.co for v in mesh.data.vertices])
names = [b.name for b in rig.pose.bones]
boots = {side: np.flatnonzero((rest[:,2] <= (rig.matrix_world @ rig.data.bones['mixamorig:' + side + 'Foot'].head_local).z + .12) & (sign * rest[:,0] > 0)).tolist()
         for side, sign in [('Left',1),('Right',-1)]}
region_bones = {'Helmet':['Head'], 'Neck':['Neck'], 'Shoulders':['LeftShoulder','RightShoulder'],
                'Wrists':['LeftHand','RightHand','LeftForeArm','RightForeArm'],
                'Backpack':['Spine','Spine1','Spine2'], 'Knees':['LeftLeg','RightLeg'],
                'Boots':['LeftFoot','RightFoot','LeftToeBase','RightToeBase']}
regions = {region:[v.index for v in mesh.data.vertices if any(mesh.vertex_groups[g.group].name in ['mixamorig:' + b for b in bs] and g.weight >= .1 for g in v.groups)]
           for region,bs in region_bones.items()}
samples = {'rest': rest, 'bone_names': np.asarray(names)}
reference = {'clips':{}}
for name, end, step in [('Idle',251,.5),('Walk',32,1/32)]:
    frames = np.arange(1,end + step/2,step)
    co, mats = [], []
    for frame in frames:
        activate(rig,bpy.data.actions[name],frame)
        co.append(positions(mesh).astype(np.float32))
        mats.append(bones(rig))
    samples[name + '_frames'] = frames
    samples[name + '_positions'] = np.asarray(co)
    samples[name + '_bones'] = np.asarray(mats)
    reference['clips'][name] = []
    for frame in ([1,56,126,251] if name == 'Idle' else [1,5,12,17,23,23.75,28,32]):
        activate(rig,bpy.data.actions[name],frame)
        heads = {b.name: [float(v) for v in ((rig.matrix_world @ b.matrix).translation)] for b in rig.pose.bones}
        reference['clips'][name].append({'time': (frame-1)/30, 'boneHeads': {n:[v[0],v[2]+offset,-v[1]] for n,v in heads.items()}})
    print('SOURCE_SAMPLED',name,len(frames),flush=True)
np.savez_compressed(HERE / 'source-samples.npz', **samples)
write_json('engine-reference.json', reference)
# Same previously validated, top-four-only reduction. Source files stay untouched.
affected,dropped = limit_weights(mesh)
report = {'sourceHashes':before, 'proposedConstantGroundOffset':offset, 'regions':regions, 'boots':boots,
          'captures':[['Idle',56],['Walk',12],['Walk',23.75]], 'clips':{},
          'fourInfluenceReduction':{'affectedVertices':len(affected),'droppedWeight':stats(dropped),'normalization':'Top four positive weights retained and normalized in export process only'}}
for name in ['Idle','Walk']:
    errors=[]; minima=[]
    for i,frame in enumerate(samples[name + '_frames']):
        activate(rig,bpy.data.actions[name],frame)
        co = positions(mesh)
        errors.append(np.linalg.norm(co-samples[name + '_positions'][i],axis=1))
        minima.append(float(co[:,2].min()+offset))
    report['clips'][name]={'allVertexErrors':stats(errors),'affectedVertexErrors':stats(np.asarray(errors)[:,affected]), 'groundMinimum':min(minima)}
    print('SKIN_REDUCTION',name,json.dumps(report['clips'][name]),flush=True)
write_json('skinning-analysis.json',report)
assert hashes() == before
