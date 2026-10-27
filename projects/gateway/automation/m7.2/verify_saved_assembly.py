"""Independent saved-file preservation and embedded-image verification; no saves."""
import bpy,pathlib,json,hashlib,struct
HERE=pathlib.Path(__file__).parent;ROOT=HERE.parents[1]/'astronaut'
def curves(a):return [fc for l in a.layers for s in l.strips for bag in getattr(s,'channelbags',[]) for fc in bag.fcurves]
def fingerprint(a):
    return hashlib.sha256(repr([(f.data_path,f.array_index,[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in f.keyframe_points]) for f in curves(a)]).encode()).hexdigest()
def skin(m):
    return hashlib.sha256(repr(([tuple(v.co) for v in m.data.vertices],[l.vertex_index for l in m.data.loops],
        [tuple(v.uv) for v in m.data.uv_layers.active.data],[g.name for g in m.vertex_groups],
        [[(g.group,g.weight) for g in v.groups] for v in m.data.vertices])).encode()).hexdigest()
source=ROOT/'animated/m7.2/astronaut-working.blend';assembled=ROOT/'animated/m7.2/astronaut-assembled.blend'
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,assembled,ROOT/'animated/m7.2/astronaut-walk.fbx',ROOT/'prepared/m7.1/astronaut-meshy-textures-1024.glb']}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=next(o for o in bpy.context.scene.objects if o.type=='MESH')
idle_fingerprint=fingerprint(r.animation_data.action);skin_fingerprint=skin(m)
rests={b.name:[[x for x in row] for row in b.matrix_local] for b in r.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(assembled),load_ui=False,use_scripts=False)
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=next(o for o in bpy.context.scene.objects if o.type=='MESH')
assert fingerprint(bpy.data.actions['Idle'])==idle_fingerprint
assert skin(m)==skin_fingerprint
assert rests=={b.name:[[x for x in row] for row in b.matrix_local] for b in r.data.bones}
b=(ROOT/'prepared/m7.1/astronaut-meshy-textures-1024.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);binary=b[28+n:]
expected={}
for im in g['images']:
    v=g['bufferViews'][im['bufferView']];expected[im['name']]=hashlib.sha256(binary[v['byteOffset']:v['byteOffset']+v['byteLength']]).hexdigest()
actual={im.name.split('.')[0]:hashlib.sha256(im.packed_file.data).hexdigest() for im in [n.image for n in m.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE']}
assert actual==expected
assert {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in map(pathlib.Path,hashes)}==hashes
result={'savedIdleCurvesIdentical':True,'savedSkinGeometryUvWeightsIdentical':True,'savedBoneRestMatricesIdentical':True,
    'savedTextureBytesIdentical':True,'textureSha256':actual,'fileHashesUnchanged':True}
(HERE/'saved-file-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print('SAVED_FILE_VALIDATION '+json.dumps(result))
