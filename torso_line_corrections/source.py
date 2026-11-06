"""Extract only exact audited members from officially obtained TORSO ZIPs."""
import zipfile
from pathlib import Path
from .core import safe,sha


def extract(records,train_zip,test_zip,out):
    out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=False)
    for split,archive in [('train',train_zip),('test',test_zip)]:
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            if len(names)!=len(set(names)):
                raise ValueError('duplicate archive member')
            for r in records:
                for stem in ('image','mask'):
                    path=r[f'original_{stem}_path']
                    if not path.startswith(split+'/'):
                        continue
                    # Archive member is an opaque key. Only the manifest's safe
                    # local path is ever used as an extraction destination.
                    info=z.getinfo(r[f'upstream_{stem}_member'])
                    if info.file_size!=int(r[f'original_{stem}_bytes']):
                        raise ValueError(f'archive member size mismatch: {path}')
                    data=z.read(info)
                    if sha(data)!=r[f'original_{stem}_sha256']:
                        raise ValueError(f'archive member SHA-256 mismatch: {path}')
                    p=safe(out,path)
                    p.parent.mkdir(parents=True,exist_ok=True)
                    with p.open('xb') as f:
                        f.write(data)
