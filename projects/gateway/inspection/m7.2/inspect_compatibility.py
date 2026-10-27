import bpy,json,pathlib,re,hashlib,math
from mathutils import Vector
root=pathlib.Path('D:/Code/porto-projects/gateway-assets/astronaut')
bpy.ops.wm.open_mainfile(filepath=str(root/'animated/m7.2/astronaut-working.blend'),load_ui=False,use_scripts=False)
sc=bpy.context.scene;rig=next(o for o in sc.objects if o.type=='ARMATURE');mesh=next(o for o in sc.objects if o.type=='MESH')
saved_idle=rig.animation_data.action
known=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(root/'animated/m7.2/astronaut-walk.fbx'))
walk=next(o for o in bpy.data.objects if o not in known and o.type=='ARMATURE');a=walk.animation_data.action
cs=[fc for l in a.layers for s in l.strips for bag in getattr(s,'channelbags',[]) for fc in bag.fcurves]
animated=set(re.match(r'pose.bones\["(.*?)"\]',fc.data_path).group(1) for fc in cs if fc.data_path.startswith('pose.bones['))
differences=[]
for b in rig.data.bones:
    wb=walk.data.bones[b.name];delta=max(abs(b.matrix_local[i][j]-wb.matrix_local[i][j]) for i in range(4) for j in range(4))
    if delta>1e-5:differences.append({'bone':b.name,'animated':b.name in animated,'weighted':b.name in mesh.vertex_groups,'matrixDelta':delta,'headDelta':(b.head_local-wb.head_local).length,'lengths':[b.length,wb.length]})
rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
samples=[]
for f in [1,8,16,24,32]:
    sc.frame_set(f);bpy.context.view_layer.update()
    samples.append({'frame':f,'maxAnimatedWorldPoseDelta':max(abs((rig.matrix_world@rig.pose.bones[n].matrix)[i][j]-(walk.matrix_world@walk.pose.bones[n].matrix)[i][j]) for n in animated for i in range(4) for j in range(4))})
def mesh_scan(action,slot):
    rig.animation_data.action=action;rig.animation_data.action_slot=slot
    lo,hi=action.frame_range;sample=[]
    for f in range(int(lo),int(hi)+1):
        sc.frame_set(f);bpy.context.view_layer.update();evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());pts=[evaluated.matrix_world@v.co for v in evaluated.data.vertices]
        hips=rig.matrix_world@rig.pose.bones['mixamorig:Hips'].head
        sample.append({'frame':f,'minimumZ':min(p.z for p in pts),'maximumZ':max(p.z for p in pts),'hips':list(hips)})
    first,last=sample[0],sample[-1]
    return {'name':action.name,'range':[lo,hi],'durationSeconds':(hi-lo)/30,'groundMinMax':[min(s['minimumZ'] for s in sample),max(s['minimumZ'] for s in sample)],
        'heightMax':max(s['maximumZ'] for s in sample),'hipsWorldRange':[[min(s['hips'][i] for s in sample),max(s['hips'][i] for s in sample)] for i in range(3)],
        'hipsFirstLastDelta':[last['hips'][i]-first['hips'][i] for i in range(3)],
        'first':first,'last':last}
scans=[mesh_scan(saved_idle,saved_idle.slots[0]),mesh_scan(a,a.slots[0])]
weighted_counts=[len([g for g in v.groups if g.weight>1e-8]) for v in mesh.data.vertices]
tails=sorted((sum(sorted([g.weight for g in v.groups],reverse=True)[4:]) for v in mesh.data.vertices),reverse=True)
def signature(m):
    uv=m.data.uv_layers.active.data
    faces=sorted(tuple(sorted(tuple(round(c,5) for c in (m.matrix_world@m.data.vertices[m.data.loops[l].vertex_index].co))+tuple(round(c,5) for c in uv[l].uv) for l in p.loop_indices)) for p in m.data.polygons)
    return hashlib.sha256(json.dumps(faces).encode()).hexdigest()
bind_sig=signature(mesh)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(root/'prepared/m7.1/astronaut-meshy-textures-1024.glb'))
source=next(o for o in bpy.data.objects if o not in before and o.type=='MESH')
props=[]
for p in bpy.ops.export_scene.gltf.get_rna_type().properties:
    if p.identifier in ['export_format','use_selection','export_yup','export_animations','export_animation_mode','export_nla_strips','export_force_sampling','export_frame_range','export_frame_step','export_skins','export_all_influences','export_influence_nb','export_rest_position_armature','export_armature_object_remove','export_reset_pose_bones','export_morph','export_apply','export_optimize_animation_size','export_anim_slide_to_zero','export_anim_scene_split_object']:
        row={'name':p.identifier,'default':getattr(p,'default',None),'description':p.description}
        if p.type=='ENUM':row['choices']=[{'id':x.identifier,'description':x.description} for x in p.enum_items]
        props.append(row)
print('COMPATIBILITY_JSON '+json.dumps({'restDifferences':differences,'animatedBones':len(animated),'poseComparison':samples,'animationScans':scans,
    'weights':{'verticesOverFourInfluences':sum(n>4 for n in weighted_counts),'maxDroppedTailWeightForFour':tails[0],'meanDroppedTailWeightForFour':sum(tails)/len(tails)},
    'bindGeometryUvSignatures':{'rigged':bind_sig,'original':signature(source),'equal':bind_sig==signature(source)},'exportProperties':props}))
