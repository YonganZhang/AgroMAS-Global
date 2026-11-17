"""OKLCh helpers adapted verbatim from share-sci-plot fpv_v16_muted_style.py; map-only dependencies omitted."""
import numpy as np
from matplotlib.colors import to_rgb
QUANT_COLORS=["#6A90B0","#A4BED1","#FFF0C4","#F4C8AE","#D67E7D","#B8525A"]
from matplotlib.colors import ListedColormap as _LCM, FuncNorm, to_hex as _to_hex

_M1=np.array([[0.4122214708,0.5363325363,0.0514459929],[0.2119034982,0.6806995451,0.1073969566],[0.0883024619,0.2817188376,0.6299787005]])
_M2=np.array([[0.2104542553,0.7936177850,-0.0040720468],[1.9779984951,-2.4285922050,0.4505937099],[0.0259040371,0.7827717662,-0.8086757660]])

def _lin(c):
    c=np.asarray(c,float);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def _gam(c):
    c=np.asarray(c,float);return np.where(c<=.0031308,12.92*c,1.055*np.clip(c,0,None)**(1/2.4)-.055)
def srgb_to_oklab(rgb):
    lms=_lin(rgb)@_M1.T;return np.cbrt(lms)@_M2.T
def oklab_to_srgb(lab):
    lms=(np.asarray(lab)@np.linalg.inv(_M2).T)**3;return _gam(lms@np.linalg.inv(_M1).T)
def oklch(c):
    L,a,b=srgb_to_oklab(to_rgb(c));return np.array([L,np.hypot(a,b),np.degrees(np.arctan2(b,a))%360])

def interp_oklch(c0,c1,t):
    """OKLCh interpolation along the shortest hue arc; returns sRGB rows (clipped to gamut)."""
    p,q=oklch(c0),oklch(c1);t=np.atleast_1d(t)[:,None]
    dh=((q[2]-p[2]+180)%360)-180
    L=p[0]+(q[0]-p[0])*t[:,0];C=p[1]+(q[1]-p[1])*t[:,0];h=np.radians(p[2]+dh*t[:,0])
    rgb=oklab_to_srgb(np.c_[L,C*np.cos(h),C*np.sin(h)])
    return np.clip(rgb,0,1)

def piecewise_norm(bounds):
    b=np.asarray(bounds,float)
    assert np.all(np.diff(b)>0)
    pos=np.linspace(0.,1.,len(b))
    # masked (no-data) values must stay masked: map them to NaN, which FuncNorm masks again.
    fwd=lambda v: np.interp(np.ma.filled(np.ma.asarray(v,dtype=float),np.nan),b,pos)
    inv=lambda u: np.interp(np.ma.filled(np.ma.asarray(u,dtype=float),np.nan),pos,b)
    return FuncNorm((fwd,inv),vmin=b[0],vmax=b[-1],clip=True)


def continuous_scale(bounds, anchors=None, below=None, name='v8_continuous', space='oklch', n=2048):
    """Colormap + norm. anchors[i] pinned at bounds[i]; last bin(s) uniform.
    below=(k, colours): first k bins form their own segment (colours pinned at bounds[0..k]) with a hard
    step at bounds[k]; the regular anchors start at bounds[k]. space: 'oklch' (v8) or 'srgb' (v7, for comparison).
    Returns (cmap, norm, stops) where stops lists (position, value, left colour, right colour)."""
    b=list(map(float,bounds));nb=len(b)-1
    anchors=list(QUANT_COLORS if anchors is None else anchors)
    pos=np.linspace(0.,1.,nb+1)
    segs=[]  # (p0,p1,c0,c1)
    start=0
    if below is not None:
        k,cols=below;assert len(cols)==k+1
        for i in range(k):segs.append((pos[i],pos[i+1],cols[i],cols[i+1]))
        start=k
    for j in range(len(anchors)-1):
        i=start+j
        if i>=nb:break
        segs.append((pos[i],pos[i+1],anchors[j],anchors[j+1]))
    last_i=start+len(anchors)-1
    if last_i<nb:segs.append((pos[last_i],1.,anchors[-1],anchors[-1]))
    x=(np.arange(n)+.5)/n
    rgb=np.zeros((n,3))
    for p0,p1,c0,c1 in segs:
        m=(x>=p0)&(x<p1+1e-12)
        t=(x[m]-p0)/(p1-p0)
        if space=='oklch':rgb[m]=interp_oklch(c0,c1,t)
        else:
            A=np.array(to_rgb(c0));B=np.array(to_rgb(c1));rgb[m]=A*(1-t[:,None])+B*t[:,None]
    cmap=_LCM(rgb,name=name)
    cmap.set_bad((0,0,0,0))
    stops=[{'position':float(p0),'value':float(np.interp(p0,pos,b)),'colour_from':c0,'position_end':float(p1),'colour_to':c1} for p0,p1,c0,c1 in segs]
    cmap._v8_segments=segs
    return cmap,piecewise_norm(b),stops


def smooth_colorbar(fig,cax,cmap,norm,bounds,labels=None,label=None,fontsize=8):
    """Gradient colour bar with ticks at the (equally spaced) bin boundaries."""
    import matplotlib.pyplot as _plt
    sm=_plt.cm.ScalarMappable(norm=norm,cmap=cmap)
    cb=fig.colorbar(sm,cax=cax,orientation='horizontal',ticks=list(bounds))
    cb.set_ticklabels(labels if labels is not None else [f'{v:g}'.replace('-','−') for v in bounds])
    cb.ax.tick_params(labelsize=fontsize,length=2.5,width=.4,pad=2)
    cb.outline.set_linewidth(.4);cb.outline.set_edgecolor('#8b969d')
    if label:cb.set_label(label,fontsize=fontsize,labelpad=3)
    return cb

