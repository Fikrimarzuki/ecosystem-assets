"""Semantic binary comparison; report expected animation changes separately."""
import pathlib,struct,json,hashlib
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
ASSETS=HERE.parents[2]/'astronaut/animated/m7.2'
def read(name):
    blob=(ASSETS/name).read_bytes()
    size=struct.unpack_from('<I',blob,12)[0]
    return json.loads(blob[20:20+size]),blob[28+size:],len(blob)
old,ob,os=read('astronaut-animated-candidate.glb')
new,nb,ns=read('astronaut-animated.glb')
def access(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    item=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],cols),dtype=dtype,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',cols*item),item)).copy()
def image_hashes(g,b):
    return [hashlib.sha256(b[g['bufferViews'][i['bufferView']].get('byteOffset',0):g['bufferViews'][i['bufferView']].get('byteOffset',0)+g['bufferViews'][i['bufferView']]['byteLength']]).hexdigest() for i in g['images']]
op=old['meshes'][0]['primitives'][0];np_=new['meshes'][0]['primitives'][0]
checks={}
for attr in op['attributes']:
    a=access(old,ob,op['attributes'][attr]);b=access(new,nb,np_['attributes'][attr])
    checks[attr]={'exact':np.array_equal(a,b),'maxAbsoluteDifference':float(np.abs(a.astype(float)-b).max())}
checks['indices']={'exact':np.array_equal(access(old,ob,op['indices']),access(new,nb,np_['indices']))}
checks['inverseBinds']={'exact':np.array_equal(access(old,ob,old['skins'][0]['inverseBindMatrices']),access(new,nb,new['skins'][0]['inverseBindMatrices']))}
checks['jointHierarchy']={'exact':old['nodes']==new['nodes']}
checks['materials']={'exact':old['materials']==new['materials']}
checks['texturePayloads']={'exact':image_hashes(old,ob)==image_hashes(new,nb)}
checks['textureSamplers']={'exact':old.get('samplers')==new.get('samplers')}
def clips(g,b):
    return {a['name']:{'channels':len(a['channels']),'maxKeys':max(g['accessors'][s['input']]['count'] for s in a['samplers']),
                       'duration':max(float(access(g,b,s['input']).max()) for s in a['samplers']),
                       'samplerBytes':sum(access(g,b,s['input']).nbytes+access(g,b,s['output']).nbytes for s in a['samplers'])}
            for a in g['animations']}
report={'oldBytes':os,'finalBytes':ns,'increaseBytes':ns-os,'increasePercent':100*(ns/os-1),'structuralChecks':checks,'previousClips':clips(old,ob),'finalClips':clips(new,nb),
        'expectedDifferences':['Corrected Walk leg transforms instead of original penetrating Walk','240 Hz animation sampling instead of 30 Hz to preserve subframe clearance','Animation data and buffer offsets/file size increase'],
        'unexpectedDifferences':[k for k,v in checks.items() if not v['exact']]}
report['animationCommonKeyComparison']={}
for name in ['Idle','Walk']:
    oa=next(a for a in old['animations'] if a['name']==name)
    na=next(a for a in new['animations'] if a['name']==name)
    errors=[];changed=[]
    for ch in oa['channels']:
        node=old['nodes'][ch['target']['node']]['name']; path=ch['target']['path']
        nc=next(c for c in na['channels'] if new['nodes'][c['target']['node']]['name']==node and c['target']['path']==path)
        s=oa['samplers'][ch['sampler']]; t=na['samplers'][nc['sampler']]
        times=access(old,ob,s['input']).ravel(); nt=access(new,nb,t['input']).ravel()
        ov=access(old,ob,s['output']); nv=access(new,nb,t['output'])
        matches=np.abs(times[:,None]-nt).argmin(axis=1)
        assert np.abs(times-nt[matches]).max()<1e-6
        d=np.linalg.norm(ov-nv[matches],axis=1)
        if path=='rotation':d=np.minimum(d,np.linalg.norm(ov+nv[matches],axis=1))
        maximum=float(d.max());errors.append(maximum)
        if maximum>1e-5:changed.append({'bone':node,'path':path,'maxValueDifference':maximum})
    report['animationCommonKeyComparison'][name]={'maxValueDifference':max(errors),'changedChannelsOver1e-5':changed}
    expected={'mixamorig:'+side+part for side in ['Left','Right'] for part in ['UpLeg','Leg','Foot']}
    if name=='Idle' and changed:report['unexpectedDifferences'].append('Idle common-key transforms changed')
    if name=='Walk' and any(c['bone'] not in expected for c in changed):report['unexpectedDifferences'].append('Walk non-leg common-key transforms changed')
(HERE/'previous-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
