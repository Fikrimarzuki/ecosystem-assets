"""Diagnose counterfactuals and measure a foot-only correction; do not save a blend."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from ground_utils import *

contact_adjustment='--contact' in sys.argv
local_padding='--local-padding' in sys.argv
trial_name='correction-final-trial.json' if local_padding else ('correction-contact-trial.json' if contact_adjustment else 'correction-trial.json')
curve_name='correction-final-curves.npz' if local_padding else ('correction-contact-curves.npz' if contact_adjustment else 'correction-curves.npz')
assert not (HERE/trial_name).exists()
assert hashes()==DIAGNOSIS['inputs']
scene,rig,mesh=open_source()
scene.render.fps=30;scene.render.fps_base=1
walk=bpy.data.actions['Walk'];idle=bpy.data.actions['Idle']
masks=boot_masks(mesh,rig)
activate(rig,idle,1)
idle_world=original_world(rig)
names=[b.name for b in rig.pose.bones]
bone_lengths={side:{'upper':(idle_world['mixamorig:'+side+'Leg'].translation-idle_world['mixamorig:'+side+'UpLeg'].translation).length,
    'lower':(idle_world['mixamorig:'+side+'Foot'].translation-idle_world['mixamorig:'+side+'Leg'].translation).length} for side in masks}
counterfactual={}
for side in masks:
    frame=DIAGNOSIS['bootSummaries'][side]['worstFrame']
    activate(rig,walk,frame)
    orig=original_world(rig)
    current=positions(mesh)[masks[side],2].min()+OFFSET
    name='mixamorig:'+side+'Foot'
    flat=idle_world[name].copy();flat.translation=orig[name].translation
    set_world(rig,name,flat,dict(orig));bpy.context.view_layer.update()
    flat_clear=positions(mesh)[masks[side],2].min()+OFFSET
    counterfactual[side]={'frame':frame,'originalClearance':float(current),'idleFootOrientationAtSameAnkleClearance':float(flat_clear),
       'originalFootRotationDifferenceFromIdleDegrees':angle(orig[name],idle_world[name]),
       'hipHeight':float(orig['mixamorig:Hips'].translation.z+OFFSET),
       'lowestSourceVertexWeights':{mesh.vertex_groups[g.group].name:g.weight for g in mesh.data.vertices[DIAGNOSIS['samples'][int(round((frame-1)*8))]['boots'][side]['lowestVertex']].groups}}

frames=np.arange(1,32,.125) # 248 periodic samples; final frame is the duplicated seam.
required={side:[] for side in masks}
raw_solve=[]
reach_limited=0
def ease(value):
    value=float(np.clip(value,0,1))
    return value*value*(3-2*value)
for frame_index,frame in enumerate(frames):
    activate(rig,walk,frame);orig=original_world(rig)
    for side,ids in masks.items():
        low=positions(mesh)[ids,2].min()+OFFSET
        native_sample=DIAGNOSIS['samples'][frame_index]['boots'][side]
        contact_weight=ease(native_sample['ankleVelocity'][1]/.08)*(1-ease((native_sample['toeGround']-.02)/.02)) if contact_adjustment else 0.
        target_clearance=.0005 if low<.0005 else low+contact_weight*(.0005-low)
        if abs(target_clearance-low)<.00001:
            required[side].append(0.)
            continue
        lo,hi=(-.012 if contact_adjustment and target_clearance<low else 0.),.065
        if lo<0:
            upper=orig['mixamorig:'+side+'UpLeg'].translation
            knee=orig['mixamorig:'+side+'Leg'].translation
            ankle=orig['mixamorig:'+side+'Foot'].translation
            max_reach=math.sqrt((knee-upper).length**2+(ankle-knee).length**2+2*(knee-upper).length*(ankle-knee).length*math.cos(math.radians(5)))
            while (ankle+Vector((0,0,lo))-upper).length>=max_reach:
                lo/=2
                reach_limited+=1
                if abs(lo)<.0001:lo=0.;break
            solve_leg(rig,side,lo,orig)
            if positions(mesh)[ids,2].min()+OFFSET>target_clearance:
                required[side].append(lo)
                continue
        solve_leg(rig,side,hi,orig)
        assert positions(mesh)[ids,2].min()+OFFSET>=target_clearance,f'{side} cannot reach requested clearance with 65mm lift'
        for _ in range(14):
            mid=(lo+hi)/2
            solve_leg(rig,side,mid,orig)
            if positions(mesh)[ids,2].min()+OFFSET<target_clearance:lo=mid
            else:hi=mid
        required[side].append(hi)
        raw_solve.append(solve_leg(rig,side,hi,orig))
smooth={};padding={}
for side in masks:
    raw=np.asarray(required[side])
    smoothed=periodic_smooth(raw,2) # 0.25 source frame / 8.33ms sigma.
    deficit=np.maximum(raw-smoothed,0)
    if local_padding:
        grid=np.arange(len(raw));distance=np.abs(grid[:,None]-grid[None,:]);distance=np.minimum(distance,len(raw)-distance)
        envelope=np.max(deficit[None,:]*np.exp(-.5*(distance/4)**2),axis=1)
        smooth[side]=smoothed+envelope+.00025
        padding[side]={'maximumLocalEnvelope':float(envelope.max()),'constantMargin':.00025,'sigmaFrames':.5}
    else:
        padding[side]=float(deficit.max()+.00025)
        smooth[side]=smoothed+padding[side]
    # Periodic endpoints are identical, and between samples are evaluated linearly.
    required[side]=np.r_[raw,raw[0]]
    smooth[side]=np.r_[smooth[side],smooth[side][0]]
frames=np.r_[frames,32.]
summary={'counterfactuals':counterfactual,'legLengths':bone_lengths,
    'method':'Per-foot vertical ankle targets solved analytically through two leg bones; original bend plane, limb lengths, foot world rotations and hips retained. Periodic Gaussian smoothing with minimal per-foot numerical clearance padding.',
    'gaussianSigmaFrames':.25,'padding':padding,'samplingStepFrames':.125,'contactAdjustment':contact_adjustment,'localPadding':local_padding,'reachLimitedLoweringIterations':reach_limited,'samples':[]}
errors={side:[] for side in masks};stance={side:[] for side in masks};contacts={side:[] for side in masks}
lift_vel={side:np.gradient(smooth[side],(frames-1)/30) for side in masks}
max_upper=max_lower=max_knee=max_footrot=max_hip=0.
for index,frame in enumerate(frames):
    activate(rig,walk,frame);orig=original_world(rig)
    before=positions(mesh);before[:,2]+=OFFSET
    solves={}
    for side in masks:
        solves[side]=solve_leg(rig,side,smooth[side][index],orig)
        max_upper=max(max_upper,solves[side]['upperAngleChange']);max_lower=max(max_lower,solves[side]['lowerAngleChange']);max_knee=max(max_knee,solves[side]['kneeMovement'])
    after=positions(mesh);after[:,2]+=OFFSET
    current=original_world(rig)
    max_hip=max(max_hip,(current['mixamorig:Hips'].translation-orig['mixamorig:Hips'].translation).length)
    side_report={}
    for side,ids in masks.items():
        low=float(after[ids,2].min());errors[side].append(low)
        native_sample=DIAGNOSIS['samples'][index]['boots'][side]
        contact=native_sample['ankleVelocity'][1]>.08 and native_sample['toeGround']<.02
        if native_sample['phase']=='stance':stance[side].append(low)
        if contact:contacts[side].append(low)
        max_footrot=max(max_footrot,angle(current['mixamorig:'+side+'Foot'],orig['mixamorig:'+side+'Foot']))
        side_report[side]={'lift':float(smooth[side][index]),'clearanceBefore':float(before[ids,2].min()),'clearanceAfter':low,
            'nativeInferredContact':contact,'inferredPhase':native_sample['phase'],'solve':solves[side]}
    summary['samples'].append({'frame':float(frame),'boots':side_report})
summary['metrics']={'maximumLift':{s:float(smooth[s].max()) for s in masks},'meanLift':{s:float(smooth[s].mean()) for s in masks},
    'minimumLift':{s:float(smooth[s].min()) for s in masks},
    'maximumLiftVelocity':{s:float(np.abs(lift_vel[s]).max()) for s in masks},
    'minimumBootClearance':{s:min(errors[s]) for s in masks},'maximumFloatingDuringKinematicContact':{s:max(contacts[s]) for s in masks},
    'maximumFloatingDuringBroadBackwardStance':{s:max(stance[s]) for s in masks},
    'maximumUpperLegAngleChangeDegrees':max_upper,'maximumLowerLegAngleChangeDegrees':max_lower,
    'maximumKneePositionChange':max_knee,'maximumFootWorldRotationChangeDegrees':max_footrot,'maximumHipChange':max_hip}
summary['inputsUnchanged']=hashes()==DIAGNOSIS['inputs']
write(trial_name,summary)
np.savez_compressed(HERE/curve_name,frames=frames,left=smooth['Left'],right=smooth['Right'],leftRaw=required['Left'],rightRaw=required['Right'])
assert summary['inputsUnchanged']
print('TRIAL',json.dumps({k:v for k,v in summary.items() if k!='samples'}),flush=True)
