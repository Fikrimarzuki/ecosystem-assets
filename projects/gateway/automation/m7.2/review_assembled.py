"""Reopen verification and temporary PBR inspection renders; never saves the scene."""
import bpy,pathlib,json,hashlib,math
from mathutils import Vector
HERE=pathlib.Path(__file__).parent
ROOT=HERE.parents[1]/'astronaut'
file=ROOT/'animated/m7.2/astronaut-assembled.blend'
report=json.loads((HERE/'assembly-validation.json').read_text())
before=hashlib.sha256(file.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(file),load_ui=False,use_scripts=False)
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH')
assert len(scene.objects)==2 and len(bpy.data.actions)==2
assert sorted(a.name for a in bpy.data.actions)==['Idle','Walk']
assert len(mesh.data.vertices)==11181
mesh.data.calc_loop_triangles();assert len(mesh.data.loop_triangles)==10357
assert mesh.parent==rig and any(m.type=='ARMATURE' and m.object==rig for m in mesh.modifiers)
assert len(mesh.vertex_groups)==34
assert len(rig.data.bones)==41
for action in bpy.data.actions:
    assert action.use_fake_user
    assert tuple(action.frame_range)==((1,251) if action.name=='Idle' else (1,32))
material=mesh.data.materials[0]
asset_images=[n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE']
print('REOPEN_IMAGES '+json.dumps([{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images]))
assert len(asset_images)==3 and all(im.packed_file and list(im.size)==[1024,1024] for im in asset_images)
assert len([n for n in material.node_tree.nodes if n.type=='TEX_IMAGE'])==3
original=ROOT/'animated/m7.2/astronaut-working.blend'
assert hashlib.sha256(original.read_bytes()).hexdigest()==report['inputs']['working']
print('REOPEN_VALIDATION PASS: two objects, 41 bones, skin retained, Idle/Walk, three packed 1K maps')

# Camera, lights and ground are added only to this render process after reopen
# checks; they are never written into the assembled .blend.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x=320;scene.render.resolution_y=384;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.18,.21,.28,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
camera_data=bpy.data.cameras.new('InspectionCamera');camera=bpy.data.objects.new('InspectionCamera',camera_data)
scene.collection.objects.link(camera);scene.camera=camera;camera_data.lens=55
def aim(obj,point):obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,position,power,size in [('Key',(3,-4,5),550,4),('Fill',(-3,-2,3),350,3),('Rim',(1,3,4),450,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=position;aim(light,(0,0,1))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0))
floor=bpy.context.object;floor.name='InspectionGroundOnly'
ground=bpy.data.materials.new('InspectionGroundOnly');ground.diffuse_color=(.12,.15,.19,1);floor.data.materials.append(ground)
captures=[('Idle',1,'front'),('Walk',1,'front'),('Walk',8,'front'),('Walk',16,'front'),('Walk',24,'front'),('Walk',16,'back')]
for index,(name,frame,view) in enumerate(captures):
    action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    scene.frame_set(frame);bpy.context.view_layer.update()
    camera.location=(2.5,-4,2.1) if view=='front' else (-2.5,4,2.1)
    aim(camera,(0,0,.9))
    scene.render.filepath=str(HERE/f'review-{index+1}-{name.lower()}-{frame}-{view}.png')
    bpy.ops.render.render(write_still=True)
    print('REVIEW_RENDER '+scene.render.filepath,flush=True)
assert hashlib.sha256(file.read_bytes()).hexdigest()==before
print('ASSEMBLED_HASH_UNCHANGED '+before)
