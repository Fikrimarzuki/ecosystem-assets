"""Bake in memory, validate at 960 Hz, and render before/after. No blend save."""
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from bake_utils import *
refined='--loop-refined' in sys.argv
report_name='final-correction-validation.json' if refined else 'correction-validation.json'
assert not (HERE/report_name).exists()
before=hashes();assert before==DIAGNOSIS['inputs']
scene,rig,mesh=open_source()
scene.render.fps=30;scene.render.fps_base=1
walk=bpy.data.actions['Walk'];idle=bpy.data.actions['Idle']
idle_hash=action_hash(idle)
skin_signature=skin_hash(mesh,rig)
keys=dict(np.load(HERE/'baked-leg-loop-keys.npz')) if refined else gather_keys(rig,walk)
corrected=make_action(rig,walk,keys)
masks=boot_masks(mesh,rig)
names=[b.name for b in rig.pose.bones]
index_of={n:i for i,n in enumerate(names)}
affected_names=set(CHANGED)
for name in CHANGED:affected_names.update(b.name for b in rig.pose.bones[name].children_recursive)
unchanged_vertices=np.flatnonzero([not any(mesh.vertex_groups[g.group].name in affected_names and g.weight>0 for g in v.groups) for v in mesh.data.vertices])
rest=np.asarray([mesh.matrix_world@v.co for v in mesh.data.vertices])
rest_joints={n:np.asarray(rig.matrix_world@rig.data.bones[n].head_local) for n in names}
regions={'boots':np.r_[masks['Left'],masks['Right']],
    'knees':np.flatnonzero(np.minimum(np.linalg.norm(rest-rest_joints['mixamorig:LeftLeg'],axis=1),np.linalg.norm(rest-rest_joints['mixamorig:RightLeg'],axis=1))<.14),
    'ankles':np.flatnonzero(np.minimum(np.linalg.norm(rest-rest_joints['mixamorig:LeftFoot'],axis=1),np.linalg.norm(rest-rest_joints['mixamorig:RightFoot'],axis=1))<.14),
    'hips':np.flatnonzero(np.minimum(np.linalg.norm(rest-rest_joints['mixamorig:LeftUpLeg'],axis=1),np.linalg.norm(rest-rest_joints['mixamorig:RightUpLeg'],axis=1))<.28)}
edges=np.asarray([tuple(e.vertices) for e in mesh.data.edges])
region_edges={r:edges[np.isin(edges[:,0],ids)&np.isin(edges[:,1],ids)] for r,ids in regions.items()}
frames=np.arange(1,32+.001,.03125)
boot_before={s:[] for s in masks};boot_after={s:[] for s in masks}
foot_before={s:[] for s in masks};foot_after={s:[] for s in masks}
toe_before={s:[] for s in masks}
hip_errors=[];foot_rotations=[];ankle_horizontal=[];leg_changes=[];knee_changes=[];upper_body_errors=[];mesh_errors=[]
deform={r:[] for r in regions};edge_deltas={r:[] for r in regions};length_errors=[]
root_before=[];root_after=[];source_seam=[];corrected_seam=[]
for frame_index,frame in enumerate(frames):
    activate(rig,walk,frame)
    orig=original_world(rig);co0=positions(mesh);co0[:,2]+=OFFSET
    activate(rig,corrected,frame)
    current=original_world(rig);co1=positions(mesh);co1[:,2]+=OFFSET
    if frame_index in [0,len(frames)-1]:
        source_seam.append(np.asarray([orig[n] for n in names]));corrected_seam.append(np.asarray([current[n] for n in names]))
    root_before.append(np.asarray(orig['mixamorig:Hips'].translation));root_after.append(np.asarray(current['mixamorig:Hips'].translation))
    hip_errors.append((current['mixamorig:Hips'].translation-orig['mixamorig:Hips'].translation).length)
    upper_body_errors.append(float(np.linalg.norm(co1[unchanged_vertices]-co0[unchanged_vertices],axis=1).max()))
    mesh_errors.append(np.linalg.norm(co1-co0,axis=1))
    for side,ids in masks.items():
        foot='mixamorig:'+side+'Foot';leg='mixamorig:'+side+'Leg';upper='mixamorig:'+side+'UpLeg';toe='mixamorig:'+side+'ToeBase'
        boot_before[side].append(float(co0[ids,2].min()));boot_after[side].append(float(co1[ids,2].min()))
        foot_before[side].append(np.asarray(orig[foot].translation));foot_after[side].append(np.asarray(current[foot].translation))
        toe_before[side].append(float(orig[toe].translation.z+OFFSET))
        foot_rotations.append(angle(orig[foot],current[foot]))
        ankle_horizontal.append(float(np.linalg.norm(np.asarray(orig[foot].translation)[:2]-np.asarray(current[foot].translation)[:2])))
        leg_changes.append((float(frame),side,angle(orig[upper],current[upper]),angle(orig[leg],current[leg])))
        knee_changes.append((float(frame),side,(current[leg].translation-orig[leg].translation).length))
        for a,b in [(upper,leg),(leg,foot)]:length_errors.append(abs((current[a].translation-current[b].translation).length-(orig[a].translation-orig[b].translation).length))
    for region,es in region_edges.items():
        length0=np.linalg.norm(co0[es[:,0]]-co0[es[:,1]],axis=1)
        length1=np.linalg.norm(co1[es[:,0]]-co1[es[:,1]],axis=1)
        keep=length0>.003
        deform[region].extend(length1[keep]/length0[keep]);edge_deltas[region].extend(np.abs(length1[keep]-length0[keep]))
    if frame_index%200==0:print('DENSE_VALIDATION',frame_index,len(frames),flush=True)

report={'inputs':before,'fps':30,'samplingStepFrames':.03125,'sampleCount':len(frames),'effectiveSamplingHz':960,
    'method':'Independent periodic smoothed foot-clearance/contact targets, analytical two-bone leg solve baked at 240Hz; no constraints, pelvis lift, scale changes or added bones',
    'idleReferenceOffsetForMeasurements':OFFSET,'savedSceneGroundReferenceZ':-OFFSET,'legsChanged':CHANGED,
    'idleActionUnchanged':action_hash(idle)==idle_hash,'skinGeometryUvRestTransformsTexturesUnchanged':skin_hash(mesh,rig)==skin_signature,
    'otherWalkChannelsUnchanged':bone_action_hash(walk,CHANGED)==bone_action_hash(corrected,CHANGED),
    'durationSeconds':(corrected.frame_range[1]-corrected.frame_range[0])/30,'frameRange':list(corrected.frame_range),
    'hipDisplacement':stats(hip_errors),'maximumSkinMovementOutsideAffectedLegHierarchy':max(upper_body_errors),
    'footWorldRotationChangeDegrees':stats(foot_rotations),'horizontalAnkleChange':stats(ankle_horizontal),
    'maximumUpperLegAngleChangeDegrees':max(s[2] for s in leg_changes),'maximumLowerLegAngleChangeDegrees':max(s[3] for s in leg_changes),
    'maximumKneeChange':max(knee_changes,key=lambda v:v[2]),'maximumSegmentLengthChange':max(length_errors),
    'wholeMeshPositionChanges':stats(mesh_errors),'boots':{},'deformation':{}}
times=(frames-1)/30
for side in masks:
    b0=np.asarray(boot_before[side]);b1=np.asarray(boot_after[side]);p0=np.asarray(foot_before[side]);p1=np.asarray(foot_after[side])
    velocity0=np.gradient(p0,times,axis=0);velocity1=np.gradient(p1,times,axis=0)
    contact=(velocity0[:,1]>.08)&(np.asarray(toe_before[side])<.02)
    report['boots'][side]={'regionVertexCount':len(masks[side]),'beforeMinimum':float(b0.min()),'afterMinimum':float(b1.min()),
        'remainingPenetration':max(0.,float(-b1.min())),'contactSampleCount':int(contact.sum()),
        'beforeMaximumContactFloating':float(b0[contact].max()),'afterMaximumContactFloating':float(b1[contact].max()),
        'afterMeanContactClearance':float(b1[contact].mean()),'afterP95ContactClearance':float(np.percentile(b1[contact],95)),
        'maximumAnkleVerticalChange':float((p1-p0)[:,2].max()),'minimumAnkleVerticalChange':float((p1-p0)[:,2].min()),
        'maximumAnkleVelocityChange':float(np.linalg.norm(velocity1-velocity0,axis=1).max()),
        'sourceAnkleVelocitySeam':float(np.linalg.norm(velocity0[-1]-velocity0[0])),
        'correctedAnkleVelocitySeam':float(np.linalg.norm(velocity1[-1]-velocity1[0])),
        'addedCorrectionVelocitySeam':float(np.linalg.norm((velocity1-velocity0)[-1]-(velocity1-velocity0)[0])),
        'sourceAnkleEndpointDelta':float(np.linalg.norm(p0[-1]-p0[0])), 'correctedAnkleEndpointDelta':float(np.linalg.norm(p1[-1]-p1[0]))}
for region in deform:
    report['deformation'][region]={'vertices':len(regions[region]),'qualifyingEdgeSamples':len(deform[region]),
        'edgeLengthRatioVsSameSourcePose':stats(deform[region]) if deform[region] else None,
        'absoluteEdgeLengthChange':stats(edge_deltas[region]) if edge_deltas[region] else None,'minimumSourceEdgeLengthForRatio':.003}
root_before=np.asarray(root_before);root_after=np.asarray(root_after)
report['rootDrift']={'sourceHorizontalEndpointDelta':float(np.linalg.norm((root_before[-1]-root_before[0])[:2])),
    'correctedHorizontalEndpointDelta':float(np.linalg.norm((root_after[-1]-root_after[0])[:2])),
    'hipsVerticalTrajectoryBefore':[float(root_before[:,2].min()+OFFSET),float(root_before[:,2].max()+OFFSET)],
    'hipsVerticalTrajectoryAfter':[float(root_after[:,2].min()+OFFSET),float(root_after[:,2].max()+OFFSET)]}
report['loop']={'sourceMaximumJointEndpointDelta':float(np.linalg.norm(source_seam[-1][:,:3,3]-source_seam[0][:,:3,3],axis=1).max()),
    'correctedMaximumJointEndpointDelta':float(np.linalg.norm(corrected_seam[-1][:,:3,3]-corrected_seam[0][:,:3,3],axis=1).max()),
    'sourceMaximumBoneRotationSeamDegrees':max(angle(Matrix(a.tolist()),Matrix(b.tolist())) for a,b in zip(source_seam[0],source_seam[-1])),
    'correctedMaximumBoneRotationSeamDegrees':max(angle(Matrix(a.tolist()),Matrix(b.tolist())) for a,b in zip(corrected_seam[0],corrected_seam[-1]))}
report['numericSafetyChecks']={
    'clearance':all(v['remainingPenetration']==0 for v in report['boots'].values()),
    'contactGapUnder7mm':all(v['afterMaximumContactFloating']<.007 for v in report['boots'].values()),
    'hipsUnchanged':max(hip_errors)<1e-7,'footOrientationsWithinPoint1Degree':max(foot_rotations)<.1,
    'horizontalAnklesWithinPoint2mm':max(ankle_horizontal)<.0002,'segmentLengthsWithinPoint2mm':max(length_errors)<.0002,
    'noSignificantRootDrift':report['rootDrift']['correctedHorizontalEndpointDelta']<.0001,
    'loopPositionContinuity':report['loop']['correctedMaximumJointEndpointDelta']<.0001,
    'loopRotationContinuity':report['loop']['correctedMaximumBoneRotationSeamDegrees']<.01,
    'idlePreserved':report['idleActionUnchanged'],'skinPreserved':report['skinGeometryUvRestTransformsTexturesUnchanged'],
    'otherWalkChannelsPreserved':report['otherWalkChannelsUnchanged'],'durationPreserved':abs(report['durationSeconds']-31/30)<1e-6}
report['numericChecksPassed']=all(report['numericSafetyChecks'].values())
report['inputsUnchanged']=hashes()==before
write(report_name,report)
write('contact-samples-final.json' if refined else 'contact-samples.json',{'frames':frames.tolist(),'before':boot_before,'after':boot_after,'sourceHip':(root_before[:,2]+OFFSET).tolist(),'correctedHip':(root_after[:,2]+OFFSET).tolist(),
    'originalLeftFoot':np.asarray(foot_before['Left']).tolist(),'originalRightFoot':np.asarray(foot_before['Right']).tolist(),
    'correctedLeftFoot':np.asarray(foot_after['Left']).tolist(),'correctedRightFoot':np.asarray(foot_after['Right']).tolist()})
print('VALIDATION_REPORT',json.dumps({k:v for k,v in report.items() if k not in ['inputs','deformation']}),flush=True)
if '--no-renders' in sys.argv:
    assert hashes()==before
    print('VALIDATION_ONLY no .blend saved',flush=True)
    raise SystemExit(0)

# Render only in memory, with the exact source grounding reference. No camera,
# light or floor is ever written to the corrected asset scene.
camera=render_setup();bpy.context.object.location.z=-OFFSET
scene.render.resolution_x=448;scene.render.resolution_y=560
worst_frame,side,_=report['maximumKneeChange']
captures=[('left-heel',9.,'front'),('right-heel',23.75,'front'),('largest-knee',worst_frame,'side'),('right-heel-boots',23.75,'boots')]
for version,action in [('before',walk),('after',corrected)]:
    for name,frame,view in captures:
        activate(rig,action,frame)
        if view=='boots':
            camera.location=(-1.5,-2.5,.7);target=Vector((0,0,.15-OFFSET));camera.data.lens=100
        elif view=='side':
            camera.location=(-3,0,1.5);target=Vector((0,0,.9-OFFSET));camera.data.lens=55
        else:
            camera.location=(2.5,-4,2.1) if name=='left-heel' else (-2.5,-4,2.1);target=Vector((0,0,.9-OFFSET));camera.data.lens=55
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(HERE/f'{version}-{name}.png')
        bpy.ops.render.render(write_still=True)
assert hashes()==before
print('REVIEW_COMPLETE no .blend saved',flush=True)
