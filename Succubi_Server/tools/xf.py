import numpy as np, json
def Rx(a):
    a=np.radians(a); c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a):
    a=np.radians(a); c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a):
    a=np.radians(a); c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def R(rot):
    rx,ry,rz=rot; return Rz(-rz)@Ry(ry)@Rx(-rx)
def bone_mats(bones, anim=None):
    """returns name -> (A 3x3, t) mapping model-space point to posed space. anim: name->{rotation,position,scale}"""
    anim=anim or {}
    by={b['name']:b for b in bones}; out={}
    def get(n):
        if n in out: return out[n]
        b=by[n]; piv=np.array(b.get('pivot',[0,0,0]),float)
        rot=np.array(b.get('rotation',[0,0,0]),float)
        a=anim.get(n,{})
        rot=rot+np.array(a.get('rotation',[0,0,0]),float)
        pos=np.array(a.get('position',[0,0,0]),float)
        sc=a.get('scale',1); sc=np.array(sc if isinstance(sc,list) else [sc]*3,float)
        M=R(rot)@np.diag(sc)
        # local: p -> piv + pos + M (p - piv)
        A=M; t=piv+pos-M@piv
        if b.get('parent') and b['parent'] in by:
            PA,Pt=get(b['parent']); A=PA@A; t=PA@t+Pt
        out[n]=(A,t); return out[n]
    for n in by: get(n)
    return out
