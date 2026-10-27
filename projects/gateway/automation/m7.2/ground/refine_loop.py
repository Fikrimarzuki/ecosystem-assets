"""Match correction seam slopes without changing the endpoint poses."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from bake_utils import *
assert not (HERE/'baked-leg-loop-keys.npz').exists()
curves_data=dict(np.load(HERE/'correction-final-curves.npz'))
keys=dict(np.load(HERE/'baked-leg-keys.npz'))
adjustments={}
for side in ['Left','Right']:
    h=curves_data[side.lower()].copy()
    difference=(h[1]-h[-2])/2
    changed=[h[0]+difference,h[0]-difference]
    adjustments[side]={'firstChangedFrame':float(curves_data['frames'][1]),'lastChangedFrame':float(curves_data['frames'][-2]),
        'deltaFirst':float(changed[0]-h[1]),'deltaLast':float(changed[1]-h[-2])}
    h[1],h[-2]=changed
    curves_data[side.lower()]=h
scene,rig,mesh=open_source();original=bpy.data.actions['Walk']
for index in [1,len(curves_data['frames'])-2]:
    frame=curves_data['frames'][index]
    activate(rig,original,frame);world=original_world(rig)
    for side in ['Left','Right']:solve_leg(rig,side,curves_data[side.lower()][index],world)
    for bone_index,name in enumerate(CHANGED):
        bone=rig.pose.bones[name];q=bone.rotation_quaternion.copy().normalized()
        old=Quaternion(keys['values'][index,bone_index,3:].tolist())
        if q.dot(old)<0:q.negate()
        keys['values'][index,bone_index]=list(bone.location)+list(q)
np.savez_compressed(HERE/'correction-loop-curves.npz',**curves_data)
np.savez_compressed(HERE/'baked-leg-loop-keys.npz',**keys)
write('loop-refinement.json',{'adjustments':adjustments,'changedBakeFrames':[1.125,31.875],
    'unchangedEndpointPoses':True,'method':'Match first/last correction slopes; only the two adjacent sampled keys change',
    'sourceHashesUnchanged':hashes()==DIAGNOSIS['inputs']})
assert hashes()==DIAGNOSIS['inputs']
print('LOOP_REFINEMENT',json.dumps(adjustments),flush=True)
