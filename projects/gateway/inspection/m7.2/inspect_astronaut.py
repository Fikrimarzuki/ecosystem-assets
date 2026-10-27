"""Read-only source inspection. Only in-memory scenes/actions are changed; never saves/exports."""
import bpy, json, pathlib, hashlib, math, statistics
from mathutils import Vector

root = pathlib.Path('D:/Code/porto-projects/gateway-assets/astronaut')
paths = {
    'working': root / 'animated/m7.2/astronaut-working.blend',
    'idle': root / 'animated/m7.2/astronaut-idle.fbx',
    'walk': root / 'animated/m7.2/astronaut-walk.fbx',
    'original': root / 'prepared/m7.1/astronaut-meshy-textures-1024.glb',
}
def hashes(): return {k: hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}
before = hashes()
def mat(m): return [[round(v,8) for v in row] for row in m]
def vec(v): return [round(x,7) for x in v]
def curves(action):
    if hasattr(action, 'fcurves'): return list(action.fcurves)
    return [fc for layer in action.layers for strip in layer.strips
            for bag in getattr(strip,'channelbags',[]) for fc in bag.fcurves]
def actions():
    results=[]
    for a in bpy.data.actions:
        cs=curves(a)
        motion=[]
        for c in cs:
            if c.data_path.endswith('location') and ('Hips' in c.data_path or c.data_path=='location'):
                vals=[k.co.y for k in c.keyframe_points]
                motion.append({'path':c.data_path,'axis':c.array_index,'keys':len(vals),
                    'min':min(vals) if vals else None,'max':max(vals) if vals else None,
                    'first':vals[0] if vals else None,'last':vals[-1] if vals else None})
        results.append({'name':a.name,'range':vec(a.frame_range),'curves':len(cs),
            'slots':[{'identifier':s.identifier,'target_id_type':s.target_id_type} for s in getattr(a,'slots',[])],
            'layers':[l.name for l in getattr(a,'layers',[])],
            'paths':sorted(set(c.data_path for c in cs)),'rootMotion':motion,
            'nonBonePaths':sorted(set(c.data_path for c in cs if not c.data_path.startswith('pose.bones['))),
            'interpolation':sorted(set(k.interpolation for c in cs for k in c.keyframe_points))})
    return results
def bounds(mesh, evaluated=False):
    obj=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else mesh
    pts=[obj.matrix_world@v.co for v in obj.data.vertices]
    return {'min':[round(min(p[i] for p in pts),7) for i in range(3)],
            'max':[round(max(p[i] for p in pts),7) for i in range(3)]}
def uv_digest(mesh):
    if not mesh.data.uv_layers.active:return None
    uv=mesh.data.uv_layers.active.data
    values=sorted((round(x.uv.x,5),round(x.uv.y,5)) for x in uv)
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()
def material(m):
    result={'name':m.name,'nodes':[]}
    if m.node_tree:
        for n in m.node_tree.nodes:
            row={'type':n.bl_idname,'name':n.name}
            if n.type=='TEX_IMAGE' and n.image:
                im=n.image;row['image']={'name':im.name,'size':list(im.size),'filepath':im.filepath,
                    'packed':bool(im.packed_file),'source':im.source,'colorSpace':im.colorspace_settings.name}
            if n.type=='BSDF_PRINCIPLED':
                row['inputs']={s.name:(list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value)
                    for s in n.inputs if s.name in ['Base Color','Metallic','Roughness','Alpha']}
            result['nodes'].append(row)
        result['links']=[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links]
    return result
def inspect(label):
    sc=bpy.context.scene
    rigs=[o for o in sc.objects if o.type=='ARMATURE'];meshes=[o for o in sc.objects if o.type=='MESH']
    objs=[]
    for o in rigs+meshes:
        d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,
            'location':vec(o.location),'rotationMode':o.rotation_mode,'rotationEuler':vec(o.rotation_euler),
            'scale':vec(o.scale),'matrixWorld':mat(o.matrix_world),'parentInverse':mat(o.matrix_parent_inverse),
            'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,
            'slot':getattr(getattr(o.animation_data,'action_slot',None),'identifier',None),
            'nla':[{'name':t.name,'strips':[{'name':s.name,'action':s.action.name if s.action else None,'range':[s.frame_start,s.frame_end],'scale':s.scale,'repeat':s.repeat} for s in t.strips]} for t in o.animation_data.nla_tracks] if o.animation_data else []}
        if o.type=='ARMATURE':
            d['boneCount']=len(o.data.bones);d['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'deform':b.use_deform,'head':vec(b.head_local),'tail':vec(b.tail_local)} for b in o.data.bones]
        else:
            o.data.calc_loop_triangles();weights=[[g.weight for g in v.groups if o.vertex_groups[g.group].name in (set(b.name for r in rigs for b in r.data.bones))] for v in o.data.vertices]
            d.update({'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'loops':len(o.data.loops),
                'uvLayers':[l.name for l in o.data.uv_layers],'uvDigest':uv_digest(o),'bounds':bounds(o),
                'evaluatedBounds':bounds(o,True),'vertexGroups':[g.name for g in o.vertex_groups],
                'weightStats':{'unweighted':sum(not x for x in weights),'maxInfluences':max(map(len,weights),default=0),
                    'minWeightSum':min(map(sum,weights),default=0),'maxWeightSum':max(map(sum,weights),default=0)},
                'modifiers':[{'type':m.type,'name':m.name,'object':m.object.name if m.type=='ARMATURE' and m.object else None} for m in o.modifiers],
                'materials':[s.material.name if s.material else None for s in o.material_slots]})
        objs.append(d)
    record={'label':label,'scene':{'fps':sc.render.fps,'fpsBase':sc.render.fps_base,'range':[sc.frame_start,sc.frame_end],'current':sc.frame_current,
        'units':sc.unit_settings.system,'unitScale':sc.unit_settings.scale_length},'objects':objs,'actions':actions(),
        'materials':[material(m) for m in bpy.data.materials]}
    print('INSPECTION_JSON '+json.dumps(record))
    return {'rigs':rigs,'meshes':meshes,'record':record}

print('BLENDER_VERSION '+bpy.app.version_string)
bpy.ops.wm.open_mainfile(filepath=str(paths['working']),load_ui=False,use_scripts=False)
working=inspect('working')
working_rig=working['rigs'][0]
working_rest={b.name:({'parent':b.parent.name if b.parent else None,'matrix':mat(b.matrix_local)}) for b in working_rig.data.bones}
working_matrix=working_rig.matrix_world.copy()

# Import the walk alongside the working rig into memory to compare and test binding.
known=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(paths['walk']))
walk_objs=[o for o in bpy.data.objects if o not in known]
walk_rig=next(o for o in walk_objs if o.type=='ARMATURE')
walk_rest={b.name:({'parent':b.parent.name if b.parent else None,'matrix':mat(b.matrix_local)}) for b in walk_rig.data.bones}
common=set(working_rest)&set(walk_rest)
delta=max(abs(working_rest[n]['matrix'][i][j]-walk_rest[n]['matrix'][i][j]) for n in common for i in range(4) for j in range(4))
walk_action=walk_rig.animation_data.action
walk_cs=curves(walk_action)
path_failures=[]
for fc in walk_cs:
    try: working_rig.path_resolve(fc.data_path)
    except (ValueError,TypeError): path_failures.append(fc.data_path)
comparison={'workingBones':len(working_rest),'walkBones':len(walk_rest),'missingFromWalk':sorted(set(working_rest)-set(walk_rest)),
    'extraInWalk':sorted(set(walk_rest)-set(working_rest)),
    'parentDifferences':[n for n in common if working_rest[n]['parent']!=walk_rest[n]['parent']],
    'maximumRestMatrixDelta':delta,'maximumObjectMatrixDelta':max(abs(working_matrix[i][j]-walk_rig.matrix_world[i][j]) for i in range(4) for j in range(4)),
    'unresolvablePaths':sorted(set(path_failures)),'walkAction':walk_action.name,
    'walkRange':vec(walk_action.frame_range),'walkSlots':[s.identifier for s in walk_action.slots]}
# Safe in-memory action/slot assignment; no source saves and no final export.
working_rig.animation_data.action=walk_action
if hasattr(working_rig.animation_data,'action_slot') and len(walk_action.slots):working_rig.animation_data.action_slot=walk_action.slots[0]
samples=[]
lo,hi=walk_action.frame_range
for frame in [lo,lo+(hi-lo)*.25,lo+(hi-lo)*.5,lo+(hi-lo)*.75,hi]:
    bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
    hips=next(b for b in working_rig.pose.bones if b.parent is None)
    samples.append({'frame':frame,'hipsHeadWorld':vec(working_rig.matrix_world@hips.head),
        'meshBounds':[bounds(m,True) for m in working['meshes']],
        'leftFootWorld':vec(working_rig.matrix_world@working_rig.pose.bones['mixamorig:LeftFoot'].head) if 'mixamorig:LeftFoot' in working_rig.pose.bones else None})
comparison['transferSamples']=samples
print('TRANSFER_JSON '+json.dumps(comparison))

for label,operator in [('idle','fbx'),('walk','fbx'),('original','gltf')]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if operator=='fbx':bpy.ops.import_scene.fbx(filepath=str(paths[label]))
    else:bpy.ops.import_scene.gltf(filepath=str(paths[label]))
    inspect(label)
assert hashes()==before,'A source file changed'
print('SOURCE_HASHES_UNCHANGED '+json.dumps(before))
