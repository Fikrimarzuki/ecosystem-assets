import bpy,json,pathlib,math
root=pathlib.Path('D:/Code/porto-projects/gateway-assets/astronaut')
bpy.ops.wm.open_mainfile(filepath=str(root/'animated/m7.2/astronaut-working.blend'),load_ui=False,use_scripts=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.data.objects if o.type=='MESH');idle=rig.animation_data.action
known=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(root/'animated/m7.2/astronaut-walk.fbx'))
walk=next(o for o in bpy.data.objects if o not in known and o.type=='ARMATURE');action=walk.animation_data.action
rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
names=['mixamorig:Hips','mixamorig:Head','mixamorig:LeftArm','mixamorig:LeftForeArm','mixamorig:LeftHand','mixamorig:LeftFoot']
details=[]
for name in names:
    b=rig.data.bones[name];w=walk.data.bones[name]
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    tm=rig.matrix_world@rig.pose.bones[name].matrix;sm=walk.matrix_world@walk.pose.bones[name].matrix
    details.append({'bone':name,'restHeadDeltaWorld':(rig.matrix_world@b.head_local-walk.matrix_world@w.head_local).length,
        'restRotationDifferenceDegrees':math.degrees(b.matrix_local.to_quaternion().rotation_difference(w.matrix_local.to_quaternion()).angle),
        'directTransferHeadDeltaWorld':(tm.translation-sm.translation).length,
        'directTransferRotationDifferenceDegrees':math.degrees(tm.to_quaternion().rotation_difference(sm.to_quaternion()).angle),
        'nativeWalkHeadWorld':list(sm.translation),'directHeadWorld':list(tm.translation)})
# Compare source geometry in its unposed data to the rigged unposed data. Do not
# evaluate/bake the armature or replace the skinned mesh.
known=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(root/'prepared/m7.1/astronaut-meshy-textures-1024.glb'))
source=next(o for o in bpy.data.objects if o not in known and o.type=='MESH')
uv_a=mesh.data.uv_layers.active.data;uv_b=source.data.uv_layers.active.data
same_loop_indices=all(a.vertex_index==b.vertex_index for a,b in zip(mesh.data.loops,source.data.loops))
uv_delta=max((a.uv-b.uv).length for a,b in zip(uv_a,uv_b))
position_delta=max((mesh.matrix_world@a.co-source.matrix_world@b.co).length for a,b in zip(mesh.data.vertices,source.data.vertices))
images=[]
for image in bpy.data.images:
    if image.source=='FILE':images.append({'name':image.name,'size':list(image.size),'path':image.filepath,'packed':bool(image.packed_file),
        'fileExists':pathlib.Path(bpy.path.abspath(image.filepath)).is_file() if image.filepath else None})
keys=[]
for item in bpy.ops.export_scene.gltf.get_rna_type().properties:
    if 'slot' in item.identifier or 'nla' in item.identifier or 'image' in item.identifier or 'texture' in item.identifier:
        keys.append({'name':item.identifier,'description':item.description})
print('DETAILS_JSON '+json.dumps({'boneDetails':details,'geometryCompare':{'matchingLoopVertexIndices':same_loop_indices,'maxUvDelta':uv_delta,
    'maxUnposedWorldPositionDelta':position_delta},'images':images,'exportOptions':keys}))
