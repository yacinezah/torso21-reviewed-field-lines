"""Hash and path checks shared by the command line and programmatic loader."""
from pathlib import Path, PurePosixPath
import csv
import hashlib
import io
import json
import re
import numpy as np
from PIL import Image

MANIFEST='manifests/reviewed_masks_manifest.csv'
DIGEST=re.compile(r'^[0-9a-f]{64}$')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe(root, rel):
    root=Path(root).resolve()
    if not rel or any(x in rel for x in ('\\',':','\0')) or any(x in ('','.','..') for x in rel.split('/')):
        raise ValueError(f'unsafe relative path: {rel!r}')
    path=(root/PurePosixPath(rel)).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'path escapes supplied root: {rel!r}')
    return path


def checked(path, digest):
    data=path.read_bytes()
    if not DIGEST.fullmatch(digest) or sha(data)!=digest:
        raise ValueError(f'SHA-256 mismatch: {path}')
    return data


def mask(data, *, source=False):
    with Image.open(io.BytesIO(data)) as image:
        if image.format!='PNG':
            raise ValueError('expected PNG mask')
        array=np.array(image)
    if source and array.ndim==3 and array.shape[2]==3:
        if np.array_equal(array[:,:,0],array[:,:,1]) and np.array_equal(array[:,:,0],array[:,:,2]):
            array=array[:,:,0]
    if array.ndim!=2 or array.dtype!=np.uint8:
        raise ValueError('expected an 8-bit single-channel mask')
    if source:
        # Official field fix, plus a distinct ignore value for unresolved low shades.
        return np.where(array>127,255,np.where((array>0)&(array<127),126,array)).astype(np.uint8,copy=False)
    if np.any((array!=0)&(array!=127)&(array!=255)):
        raise ValueError('unsupported reviewed class values')
    return array


def manifest(release_root):
    with safe(release_root,MANIFEST).open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    ids=[r['id'] for r in rows]
    if len(ids)!=len(set(ids)) or any(not re.fullmatch('[0-9a-f]{16}',x) for x in ids):
        raise ValueError('duplicate or invalid row IDs')
    for key in ('original_image_path','original_mask_path'):
        paths=[r[key].casefold() for r in rows]
        if len(paths)!=len(set(paths)):
            raise ValueError(f'duplicate path: {key}')
    for r in rows:
        for key in ('original_image_path','original_mask_path','corrected_mask_path'):
            safe(release_root,r[key])
        if r['corrected_mask_path']!=f"annotations/{r['id']}.png":
            raise ValueError('invalid overlay path')
        if r['review_status'] not in ('reviewed_unchanged','reviewed_modified'):
            raise ValueError('invalid review status')
        if (int(r['changed_pixels'])>0)!=(r['review_status']=='reviewed_modified'):
            raise ValueError('inconsistent change flag')
        if r['byte_identical']=='True' and (r['original_mask_sha256']!=r['corrected_mask_sha256'] or int(r['changed_pixels'])!=0):
            raise ValueError('inconsistent identical flag')
    return rows


def original_pair(torso_root,r):
    image=safe(torso_root,r['original_image_path'])
    im=checked(image,r['original_image_sha256'])
    om=checked(safe(torso_root,r['original_mask_path']),r['original_mask_sha256'])
    with Image.open(io.BytesIO(im)) as source:
        source.load()
        if source.size!=(int(r['width']),int(r['height'])):
            raise ValueError(f'image dimensions differ: {r["id"]}')
    old=mask(om,source=True)
    if old.shape!=(int(r['height']),int(r['width'])):
        raise ValueError(f'original mask dimensions differ: {r["id"]}')
    if int(np.count_nonzero(old==126))!=int(r['original_ambiguous_pixels']):
        raise ValueError(f'original ambiguity count differs: {r["id"]}')
    return image,old


def overlay(release_root,r):
    reviewed=checked(safe(release_root,r['corrected_mask_path']),r['corrected_mask_sha256'])
    decoded=mask(reviewed)
    if decoded.shape!=(int(r['height']),int(r['width'])):
        raise ValueError(f'reviewed mask dimensions differ: {r["id"]}')
    return reviewed,decoded


def load_pair(release_root,torso_root,r):
    """Return verified source image path, original class grid, and reviewed class grid."""
    image,orig=original_pair(torso_root,r)
    _,new=overlay(release_root,r)
    if int(np.count_nonzero((orig!=new)&(orig!=126)))!=int(r['changed_pixels']):
        raise ValueError(f'changed pixel count differs: {r["id"]}')
    return image,orig,new


def write_csv(path,rows):
    if not rows:
        raise ValueError('cannot write empty table')
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]),lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def read_meta(release_root):
    return json.loads(safe(release_root,'metadata.json').read_text(encoding='utf-8'))
