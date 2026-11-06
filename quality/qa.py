"""Freeze a stratified sample, make blind reviewer packets and score references."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import hmac
import html
import io
import json
from pathlib import Path
import secrets
import sys

import numpy as np
from PIL import Image
from torso_line_corrections.core import manifest, sha, load_pair, checked, safe, write_csv

SEED='qa-selection-v1-20261106'


def read(p):
    with Path(p).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def rank(r):
    return hashlib.sha256((SEED+':'+r['id']).encode()).digest()


def choose(rows,geometry,n=240):
    groups=defaultdict(list)
    bins=defaultdict(list)
    for r in sorted(rows,key=rank):
        if int(r['original_ambiguous_pixels']):
            continue
        g=geometry[r['id']]
        area=int(r['line_before'])/(int(r['width'])*int(r['height']))
        prevalence='empty' if area==0 else 'thin' if area<.01 else 'visible'
        pct=float(r['changed_percent'])
        change='zero' if pct==0 else 'small' if pct<=.5 else 'medium' if pct<=2 else 'large'
        anomaly=int(r['original_off_palette_pixels'])>0 or int(g['tiny_components_le4_before'])>=3
        d=dict(id=r['id'],group_id=r['group_id'],tier=change,line_prevalence=prevalence,original_anomaly=anomaly)
        groups[r['group_id']].append(d)
        bins[(change,prevalence,anomaly)].append(d)
    chosen={rs[0]['id']:rs[0] for _,rs in sorted(groups.items())}
    if not len(chosen)<=n<=sum(map(len,groups.values())):
        raise ValueError('sample size incompatible with group coverage')
    group_counts=Counter(r['group_id'] for r in chosen.values())
    while len(chosen)<n:
        for _,members in sorted(bins.items()):
            avail=[r for r in members if r['id'] not in chosen]
            if avail:
                row=min(avail,key=lambda r:(group_counts[r['group_id']],rank(r)))
                chosen[row['id']]=row
                group_counts[row['group_id']]+=1
                if len(chosen)==n:
                    break
    return sorted(chosen.values(),key=rank)


def html_index(path, blocks, title):
    path.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+html.escape(title)+
                    '</title><style>body{font:16px system-ui;max-width:1350px;margin:2rem auto}section{border-top:1px solid #888;padding:1rem 0}img{width:32%;height:auto}figure{display:inline;margin:0}</style>'+
                    '<h1>'+html.escape(title)+'</h1>'+''.join(blocks)+'</html>',encoding='utf-8')


def ref_packet(a, byid, selected):
    # Deliberately store reviewer packet and private key in distinct directories.
    a.output.mkdir(exist_ok=False)
    a.operator.mkdir(exist_ok=False)
    salt=secrets.token_bytes(32)
    key=[]
    blocks=[]
    for s in selected:
        r=byid[s['id']]
        opaque=hmac.new(salt,r['id'].encode(),'sha256').hexdigest()[:16]
        side='A' if hmac.new(salt,('side:'+r['id']).encode(),'sha256').digest()[0]&1 else 'B'
        data=checked(safe(a.torso_root,r['original_image_path']),r['original_image_sha256'])
        with Image.open(io.BytesIO(data)) as source:
            source.convert('RGB').save(a.output/f'{opaque}.png')
        key.append(dict(opaque=opaque,reviewed_side=side,**s))
        blocks.append(f'<section><h2>{opaque}</h2><a href="{opaque}.png"><img loading="lazy" src="{opaque}.png" alt="Reference image"></a></section>')
    write_csv(a.operator/'BLIND_KEY.csv',key)
    (a.operator/'SESSION.json').write_text(json.dumps({'mode':a.mode,'selection_sha256':sha(a.selection.read_bytes()),
        'manifest_sha256':sha((a.release_root/'manifests/reviewed_masks_manifest.csv').read_bytes()),
        'blind_key_sha256':sha((a.operator/'BLIND_KEY.csv').read_bytes())},indent=2),encoding='utf-8')
    write_csv(a.output/'reference_review_template.csv',[dict(opaque=r['opaque'],reviewer_id='',independent='',confidence='',status='',reason='') for r in key])
    html_index(a.output/'index.html',blocks,'Reference images only — click to open native image')


def candidate_packet(a,byid):
    key=read(a.operator/'BLIND_KEY.csv')
    receipt=json.loads((a.operator/'REFERENCE_FREEZE.json').read_text())
    if receipt['masks']!=ref_digests(key,a.reference) or receipt['key_sha256']!=sha((a.operator/'BLIND_KEY.csv').read_bytes()):
        raise ValueError('reference masks changed since freeze')
    a.output.mkdir(exist_ok=False)
    blocks=[]
    for x in key:
        opaque=x['opaque'];r=byid[x['id']]
        image,old,new=load_pair(a.release_root,a.torso_root,r)
        with Image.open(image) as p:
            rgb=np.array(p.convert('RGB'))
        labels=[old,new] if x['reviewed_side']=='B' else [new,old]
        for suffix,ar in zip(('RGB','A','B'),[None,*labels]):
            view=rgb.copy()
            if ar is not None:
                view[ar==127]=(view[ar==127]*.45+[0,140,140]).astype(np.uint8)
            Image.fromarray(view).save(a.output/f'{opaque}_{suffix}.png')
        gallery=''.join(f'<figure><a href="{opaque}_{s}.png"><img loading="lazy" src="{opaque}_{s}.png" alt="{s}"></a></figure>' for s in ('RGB','A','B'))
        blocks.append(f'<section><h2>{opaque}: RGB / A / B</h2>{gallery}</section>')
    write_csv(a.output/'candidate_review_template.csv',[dict(opaque=r['opaque'],preference='',reason='',reviewer_id='') for r in key])
    html_index(a.output/'index.html',blocks,'Blinded candidates — RGB / A / B')


def ref_digests(key,root):
    return {x['opaque']:sha((root/f'{x["opaque"]}.png').read_bytes()) for x in key}


def summarize(rows):
    groups=defaultdict(list)
    for r in rows:
        if r['primary_delta'] is not None:
            groups[r['group_id']].append(r['primary_delta'])
    g=np.array([np.mean(rs) for _,rs in sorted(groups.items())])
    if len(g)<2:
        raise ValueError('at least two scored groups required')
    boot=np.random.default_rng(20261106).choice(g,(10000,len(g)),replace=True).mean(axis=1)
    return dict(scored_pairs=sum(map(len,groups.values())),scored_groups=len(g),estimate=float(g.mean()),
                ci95=np.quantile(boot,[.025,.975]).tolist())


def score(a,byid):
    from torso_line_corrections.geometry import measure
    key=read(a.operator/'BLIND_KEY.csv')
    receipt=json.loads((a.operator/'REFERENCE_FREEZE.json').read_text())
    if receipt['masks']!=ref_digests(key,a.reference) or receipt['key_sha256']!=sha((a.operator/'BLIND_KEY.csv').read_bytes()):
        raise ValueError('reference masks changed since freeze')
    rows=[]
    for x in key:
        r=byid[x['id']]
        _,old,new=load_pair(a.release_root,a.torso_root,r)
        with Image.open(a.reference/f'{x["opaque"]}.png') as p:
            ref=np.array(p)
        if ref.shape!=old.shape or not set(np.unique(ref))<={0,126,127,255}:
            raise ValueError(f'invalid adjudicated reference: {x["opaque"]}')
        valid=ref!=126
        if not valid.any():
            rows.append(dict(opaque=x['opaque'],group_id=x['group_id'],ignored_pixels=int(ref.size),
                             original={},reviewed={},primary_delta=None,reference_line_present=False))
            continue
        ref=np.where(valid,ref,0).astype(np.uint8)
        old=np.where(valid,old,0).astype(np.uint8);new=np.where(valid,new,0).astype(np.uint8)
        o,m=measure(old,ref),measure(new,ref)
        p,q=o['centerline_f1_at3px'],m['centerline_f1_at3px']
        delta=None if p is None and q is None else (1 if q is None else q)-(1 if p is None else p)
        rows.append(dict(opaque=x['opaque'],group_id=x['group_id'],ignored_pixels=int((~valid).sum()),
                         original=o,reviewed=m,primary_delta=delta,reference_line_present=bool((ref==127).any())))
    s=summarize(rows)
    s['independent_attested']=receipt['mode']=='INDEPENDENT'
    s['passes_primary_gate']=bool(s['independent_attested'] and s['scored_pairs']>=200 and s['scored_groups']>=30
                                    and s['estimate']>=.02 and s['ci95'][0]>0)
    secondary={}
    for metric in ('line_dice','line_iou','cldice','line_boundary_mean_px','line_boundary_hd95_px'):
        paired=[]
        for row in rows:
            o=row['original'].get(metric);m=row['reviewed'].get(metric)
            if o is not None and m is not None:
                paired.append(dict(group_id=row['group_id'],primary_delta=m-o))
        if len({r['group_id'] for r in paired})>=2:
            secondary[metric]=summarize(paired)
    present=[r for r in rows if r['reference_line_present'] and r['primary_delta'] is not None]
    if len({r['group_id'] for r in present})>=2:
        secondary['centerline_f1_at3px_reference_line_present']=summarize(present)
    if a.judgments:
        decisions=read(a.judgments)
        mapping={r['opaque']:r['reviewed_side'] for r in key}
        if len({r['opaque'] for r in decisions})!=len(decisions) or any(
            r['opaque'] not in mapping or r['preference'] not in ('A','B','tie','uncertain') for r in decisions
        ):
            raise ValueError('invalid or repeated candidate judgment')
        secondary['preference']=dict(Counter(r['preference'] if r['preference'] in ('tie','uncertain') else (
            'reviewed' if r['preference']==mapping[r['opaque']] else 'original') for r in decisions))
        secondary['missing_preferences']=len(key)-len(decisions)
    with a.output.open('x',encoding='utf-8') as f:
        json.dump({'primary':s,'secondary':secondary,'rows':rows,'reference_freeze_sha256':sha((a.operator/'REFERENCE_FREEZE.json').read_bytes())},f,indent=2)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['select','reference-packet','freeze-reference','candidate-packet','score'])
    p.add_argument('--release-root',type=Path,default=Path.cwd())
    for name in ('geometry','selection','torso-root','operator','reference','output','attestation','reviews','judgments'):
        p.add_argument('--'+name,type=Path)
    p.add_argument('--mode',choices=['INDEPENDENT','REPEAT_AUDIT'])
    a=p.parse_args()
    m=manifest(a.release_root);byid={r['id']:r for r in m}
    if a.command=='select':
        selection=choose(m,{r['id']:r for r in read(a.geometry)})
        write_csv(a.output,selection)
        with a.output.with_suffix('.freeze.json').open('x',encoding='utf-8') as f:
            json.dump(dict(selection_sha256=sha(a.output.read_bytes()),geometry_sha256=sha(a.geometry.read_bytes()),
                           manifest_sha256=sha((a.release_root/'manifests/reviewed_masks_manifest.csv').read_bytes()),
                           selection_code_sha256=sha(Path(__file__).read_bytes()),size=len(selection),status='NO_HUMAN_RESULTS'),f,indent=2)
    elif a.command=='reference-packet':
        if not a.mode:
            raise ValueError('predeclare INDEPENDENT or REPEAT_AUDIT before showing any image')
        lock=json.loads(a.selection.with_suffix('.freeze.json').read_text())
        if lock['selection_sha256']!=sha(a.selection.read_bytes()) or lock['manifest_sha256']!=sha((a.release_root/'manifests/reviewed_masks_manifest.csv').read_bytes()):
            raise ValueError('selection freeze mismatch')
        ref_packet(a,byid,read(a.selection))
    elif a.command=='freeze-reference':
        session=json.loads((a.operator/'SESSION.json').read_text())
        if not a.attestation or not a.attestation.read_text(encoding='utf-8').strip() or not a.reviews:
            raise ValueError('completed reviews and review/adjudication attestation required')
        key=read(a.operator/'BLIND_KEY.csv')
        if session['blind_key_sha256']!=sha((a.operator/'BLIND_KEY.csv').read_bytes()):
            raise ValueError('unblinding key changed')
        reports=read(a.reviews)
        if len(reports)!=len(key) or {r['opaque'] for r in reports}!={r['opaque'] for r in key} or any(
            r['status']!='adjudicated' or not r['reviewer_id'].strip() or
            (session['mode']=='INDEPENDENT' and r['independent'].strip().lower()!='yes') for r in reports
        ):
            raise ValueError('require one attested adjudicated review record per opaque ID')
        with (a.operator/'REFERENCE_FREEZE.json').open('x',encoding='utf-8') as f:
            json.dump(dict(mode=session['mode'],masks=ref_digests(key,a.reference),attestation_sha256=sha(a.attestation.read_bytes()),
                           reviews_sha256=sha(a.reviews.read_bytes()),key_sha256=session['blind_key_sha256']),f,indent=2)
    elif a.command=='candidate-packet':
        candidate_packet(a,byid)
    else:
        score(a,byid)


if __name__=='__main__':
    main()
