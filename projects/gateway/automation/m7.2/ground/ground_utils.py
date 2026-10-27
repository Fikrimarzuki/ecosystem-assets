"""Rest-aware, length-preserving two-bone leg correction in a temporary scene."""
import sys,pathlib,json,hashlib,math
import bpy,numpy as np
from mathutils import Vector,Matrix,Quaternion
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent/'export'))
from asset_utils import open_source,activate,positions,bones,stats,render_setup
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'astronaut'
OUTPUT=ROOT/'animated/m7.2/astronaut-ground-corrected.blend'
DIAGNOSIS=json.loads((HERE/'diagnosis.json').read_text())
OFFSET=DIAGNOSIS['idleReferenceOffset']

def hashes():return {p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in DIAGNOSIS['inputs']}
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def curves(action):return [fc for l in action.layers for s in l.strips for bag in s.channelbags for fc in bag.fcurves]
def action_hash(action):return hashlib.sha256(repr([(f.data_path,f.array_index,[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in f.keyframe_points]) for f in curves(action)]).encode()).hexdigest()
def bone_action_hash(action,exclude=()):return hashlib.sha256(repr([(f.data_path,f.array_index,[(tuple(k.co),k.interpolation,tuple(k.handle_left),tuple(k.handle_right)) for k in f.keyframe_points]) for f in curves(action) if not any(f'pose.bones["{n}"]' in f.data_path for n in exclude)]).encode()).hexdigest()
def boot_masks(mesh,rig):
    rest=np.asarray([mesh.matrix_world@v.co for v in mesh.data.vertices])
    return {side:np.flatnonzero((rest[:,2]<=(rig.matrix_world@rig.data.bones['mixamorig:'+side+'Foot'].head_local).z+.12)&(sign*rest[:,0]>0)) for side,sign in [('Left',1),('Right',-1)]}

def original_world(rig):return {b.name:rig.matrix_world@b.matrix for b in rig.pose.bones}
def set_world(rig,name,desired,parents):
    bone=rig.pose.bones[name]
    inverse=rig.matrix_world.inverted()
    kwargs={'matrix':inverse@desired,'matrix_local':bone.bone.matrix_local,'invert':True}
    if bone.parent:
        kwargs.update(parent_matrix=inverse@parents[bone.parent.name],parent_matrix_local=bone.parent.bone.matrix_local)
    scale=bone.scale.copy()
    basis=bone.bone.convert_local_to_pose(**kwargs)
    loc,q,_=basis.decompose()
    bone.location=loc;bone.rotation_quaternion=q;bone.scale=scale
    parents[name]=desired

def solve_leg(rig,side,lift,original):
    upper='mixamorig:'+side+'UpLeg';lower='mixamorig:'+side+'Leg';foot='mixamorig:'+side+'Foot'
    a=original[upper].translation.copy();b=original[lower].translation.copy();c=original[foot].translation.copy()
    target=c+Vector((0,0,float(lift)))
    l1=(b-a).length;l2=(c-b).length
    distance=(target-a).length
    assert abs(l1-l2)+1e-6<distance<l1+l2-1e-6, f'Unreachable {side} ankle target at lift {lift}'
    direction=(target-a).normalized()
    bend=(b-a)-direction*(b-a).dot(direction)
    assert bend.length>1e-6,'Ambiguous knee plane'
    bend.normalize()
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    radius=math.sqrt(max(0,l1*l1-along*along))
    knee=a+direction*along+bend*radius
    delta1=(b-a).normalized().rotation_difference((knee-a).normalized())
    delta2=(c-b).normalized().rotation_difference((target-knee).normalized())
    m1=delta1.to_matrix().to_4x4()@original[upper];m1.translation=a
    m2=delta2.to_matrix().to_4x4()@original[lower];m2.translation=knee
    mf=original[foot].copy();mf.translation=target
    parents=dict(original)
    for name,matrix in [(upper,m1),(lower,m2),(foot,mf)]:set_world(rig,name,matrix,parents)
    bpy.context.view_layer.update()
    actual=rig.matrix_world@rig.pose.bones[foot].matrix
    return {'targetError':(actual.translation-target).length,'upperLength':l1,'lowerLength':l2,
            'upperAngleChange':math.degrees(delta1.angle),'lowerAngleChange':math.degrees(delta2.angle),
            'kneeMovement':(knee-b).length}

def angle(a,b):
    d=a.to_quaternion().normalized().rotation_difference(b.to_quaternion().normalized())
    return math.degrees(2*math.atan2(math.sqrt(d.x*d.x+d.y*d.y+d.z*d.z),abs(d.w)))

def periodic_smooth(values,sigma_samples=2):
    values=np.asarray(values)
    count=len(values)
    radius=int(math.ceil(4*sigma_samples))
    offsets=np.arange(-radius,radius+1)
    weights=np.exp(-.5*(offsets/sigma_samples)**2);weights/=weights.sum()
    return sum(w*np.roll(values,int(o)) for o,w in zip(offsets,weights))
