import bpy, numpy as np, os, sys
args=sys.argv[sys.argv.index("--")+1:]; root=os.path.abspath(args[0]); out=os.path.abspath(args[1]); rows=[r.split(",") for r in args[2:]]
def load(p):
    i=bpy.data.images.load(p); w,h=i.size; a=np.array(i.pixels[:],dtype=np.float32).reshape(h,w,4); bpy.data.images.remove(i); return a
R=[]
for row in rows:
    t=[load(os.path.join(root,f)) for f in row]; hmax=max(x.shape[0] for x in t)
    t=[np.concatenate([np.ones((hmax-x.shape[0],x.shape[1],4),np.float32),x],0) if x.shape[0]<hmax else x for x in t]
    g=np.ones((hmax,8,4),np.float32); R.append(np.concatenate(sum([[x,g] for x in t],[])[:-1],1))
W=max(r.shape[1] for r in R); R=[np.concatenate([r,np.ones((r.shape[0],W-r.shape[1],4),np.float32)],1) for r in R]
img=np.concatenate(sum([[r,np.ones((8,W,4),np.float32)] for r in R],[])[:-1][::-1],0)
o=bpy.data.images.new("g",img.shape[1],img.shape[0],alpha=True); o.pixels=img.ravel(); o.filepath_raw=out; o.file_format="PNG"; o.save(); print("GRID_OK")
