"""Paired geometry change statistics; neither input is treated as ground truth."""
import cv2
import numpy as np
from skimage.morphology import skeletonize

cv2.setNumThreads(1)


def overlap(a, b):
    na, nb = int(a.sum()), int(b.sum())
    hit = int(np.count_nonzero(a & b))
    return ((2*hit/(na+nb), hit/(na+nb-hit)) if na+nb else (None, None))


def crop_pair(a,b):
    """Common support box, with a zero rim for erosion and distance transforms."""
    y,x = np.where(a|b)
    if not len(x):
        return a[:0,:0],b[:0,:0]
    s=np.s_[y.min():y.max()+1,x.min():x.max()+1]
    return np.pad(a[s],1),np.pad(b[s],1)


def dist(a):
    return cv2.distanceTransform(a.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)


def distances(a,b):
    if not (a.any() and b.any()):
        return None,None
    return dist(~b)[a],dist(~a)[b]


def boundary(a):
    e=cv2.erode(a.astype(np.uint8),np.ones((3,3),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)
    return a & ~e.astype(bool)


def surface(a,b):
    if not (a.any() and b.any()):
        return None,None
    a,b=crop_pair(a,b)
    x,y=distances(boundary(a),boundary(b))
    return (float((x.mean()+y.mean())/2),float(max(np.quantile(x,.95),np.quantile(y,.95))))


def components(a):
    if not a.any():
        return 0,0,None
    _,_,stats,_=cv2.connectedComponentsWithStats(a.astype(np.uint8),connectivity=8)
    sizes=stats[1:,cv2.CC_STAT_AREA]
    return len(sizes),int(np.count_nonzero(sizes<=4)),float(sizes.max()/sizes.sum())


def skeleton_length(s):
    # Prune a diagonal link when an orthogonal two-step path exists.
    sides=np.count_nonzero(s[1:] & s[:-1])+np.count_nonzero(s[:,1:] & s[:,:-1])
    diag=np.count_nonzero(s[1:,1:] & s[:-1,:-1] & ~s[1:,:-1] & ~s[:-1,1:])
    diag+=np.count_nonzero(s[1:,:-1] & s[:-1,1:] & ~s[1:,1:] & ~s[:-1,:-1])
    return float(sides+np.sqrt(2)*diag)


def tangents(s):
    yy,xx=np.nonzero(s)
    if not len(xx):
        return None,0
    offsets=np.array([(dy,dx) for dy in (-1,0,1) for dx in (-1,0,1) if dy or dx])
    nbr=s[yy[:,None]+offsets[:,0],xx[:,None]+offsets[:,1]]
    indices=np.where(nbr[nbr.sum(axis=1)==2])[1].reshape(-1,2)
    v,w=offsets[indices[:,0]],offsets[indices[:,1]]
    # Degree-two points with neighbor directions separated by at least 135 degrees.
    good=(v*w).sum(axis=1)<=-(np.linalg.norm(v,axis=1)*np.linalg.norm(w,axis=1))/np.sqrt(2)+1e-9
    d=v[good]-w[good]
    count=len(d)
    if count<32:
        return None,count
    # Four undirected orientation classes: H, diagonal, V, other diagonal.
    angle=np.mod(np.arctan2(d[:,0],d[:,1]),np.pi)
    hist=np.bincount(np.floor(angle/(np.pi/4)+.5).astype(int)%4,minlength=4)
    return hist/count,count


def harmon(a,b):
    return float(2*a*b/(a+b)) if a+b else 0.


def measure(original, reviewed):
    if original.shape!=reviewed.shape or original.ndim!=2:
        raise ValueError('mask grids differ')
    r={}
    for name,val in [('background',0),('line',127),('field',255),('field_union',None)]:
        a=original==val if val is not None else original!=0
        b=reviewed==val if val is not None else reviewed!=0
        r[f'{name}_dice'],r[f'{name}_iou']=overlap(a,b)
        if name in ('line','field_union'):
            r[f'{name}_boundary_mean_px'],r[f'{name}_boundary_hd95_px']=surface(a,b)
    a,b=crop_pair(original==127,reviewed==127)
    sa=skeletonize(a) if a.any() else np.zeros_like(a)
    sb=skeletonize(b) if b.any() else np.zeros_like(b)
    orientations=[]
    for lab,mask,sk in [('before',a,sa),('after',b,sb)]:
        c,t,m=components(mask)
        r.update({f'components_{lab}':c,f'tiny_components_le4_{lab}':t,f'largest_component_fraction_{lab}':m,
                  f'skeleton_pixels_{lab}':int(sk.sum()),f'skeleton_length_px_{lab}':skeleton_length(sk)})
        width=2*dist(mask)[sk]-1 if sk.any() else []
        for q in (10,50,90):
            r[f'width_p{q}_px_{lab}']=float(np.percentile(width,q)) if len(width) else None
        hist,count=tangents(sk)
        r[f'tangent_samples_{lab}']=count
        orientations.append(hist)
        for i in range(4):
            r[f'tangent_bin{i}_{lab}']=float(hist[i]) if hist is not None else None
    r['tangent_histogram_tv']=float(np.abs(orientations[0]-orientations[1]).sum()/2) if all(h is not None for h in orientations) else None
    x,y=distances(sa,sb)
    for k in (1,2,3):
        r[f'centerline_f1_at{k}px']=(harmon(np.mean(x<=k+1e-6),np.mean(y<=k+1e-6)) if x is not None
                                   else 0. if sa.any() or sb.any() else None)
    r['cldice']=(harmon(b[sa].mean(),a[sb].mean()) if sa.any() and sb.any()
                 else 0. if a.any() or b.any() else None)
    return r
