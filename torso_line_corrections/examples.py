"""Generate local illustrations chosen before visual inspection."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from .core import load_pair, safe


def examples(root,records,torso_root,output):
    picks=json.loads(safe(root,'examples/selection.json').read_text(encoding='utf-8'))
    if torso_root is None and output is None:
        print(json.dumps(picks,indent=2));return
    if torso_root is None or output is None:
        raise ValueError('supply both --torso-root and --output to render examples')
    out=Path(output).resolve()
    if out.is_relative_to(root) or out.is_relative_to(Path(torso_root).resolve()):
        raise ValueError('example output must be outside source and release directories')
    out.mkdir(exist_ok=False,parents=True)
    byid={r['id']:r for r in records}
    for p in picks['examples']:
        r=byid[p['id']]
        image,old,new=load_pair(root,torso_root,r)
        with Image.open(image) as im:
            raw=im.convert('RGB')
        rgb=np.asarray(raw).copy()
        frames=[raw]
        for labels in (old,new):
            view=rgb.copy()
            view[labels==127]=(rgb[labels==127].astype(np.float32)*.4+[0,153,153]).astype(np.uint8)
            view[labels==126]=[249,183,39]
            frames.append(Image.fromarray(view))
        for frame in frames:
            frame.thumbnail((480,360))
        w,h=frames[0].size
        canvas=Image.new('RGB',(3*w,h+48),'white')
        d=ImageDraw.Draw(canvas)
        for i,(label,frame) in enumerate(zip(('Source RGB','Original line','Reviewed line'),frames)):
            canvas.paste(frame,(i*w,26))
            d.text((i*w+4,5),label,fill='black')
        d.text((4,h+31),f"{p['category']} | {r['id']} | visual changes, not accuracy",fill='black')
        canvas.save(out/f"{p['category']}.png")
