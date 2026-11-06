"""Regenerate descriptive tables, flags, figures and predeclared example IDs."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torso_line_corrections.core import manifest, write_csv

EXAMPLE_RULES = {
    'byte_encoding_only': 'Unchanged classes and no decoded raw value changes',
    'palette_only': 'Unchanged classes, but raw values changed',
    'small_edit': 'Positive semantic edit at most 0.5 percent',
    'medium_edit': 'More than 0.5 through 2 percent semantic edit',
    'large_edit': 'More than 2 percent semantic edit',
    'new_line': 'No original line pixels, reviewed has line pixels',
    'removed_line': 'Original has line pixels, reviewed has none',
    'ambiguous_original': 'Original has unresolved low gray values'
}


def read(p):
    with p.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def encode(p,result):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')


def describe(x):
    x=np.array(list(x),dtype=float)
    return {'defined':len(x),'mean':float(x.mean()) if len(x) else None,
            'p05_p25_p50_p75_p95':np.quantile(x,[.05,.25,.5,.75,.95]).tolist() if len(x) else None}


def picks(rows):
    samples=defaultdict(list)
    for r in rows:
        if r['original_ambiguous_pixels']!='0':
            samples['ambiguous_original'].append(r)
            continue
        pct=float(r['changed_percent'])
        cat=('palette_only' if int(r['raw_value_changed_pixels']) else 'byte_encoding_only') if pct==0 else (
            'small_edit' if pct<=.5 else 'medium_edit' if pct<=2 else 'large_edit')
        samples[cat].append(r)
        if r['line_before']=='0' and r['line_after']!='0':
            samples['new_line'].append(r)
        if r['line_before']!='0' and r['line_after']=='0':
            samples['removed_line'].append(r)
    used=set();result=[]
    for cat in EXAMPLE_RULES:
        options=[r for r in samples[cat] if r['id'] not in used]
        if options:
            row=min(options,key=lambda r:hashlib.sha256(('examples-v1:'+cat+':'+r['id']).encode()).digest())
            used.add(row['id'])
            result.append(dict(category=cat,rule=EXAMPLE_RULES[cat],id=row['id'],pool_count=len(samples[cat])))
    return {'scope':'Change illustrations, no reviewer or quality selection; RGB is rendered locally only',
            'selection':'Category order above, deterministic hash rank with disjoint examples',
            'examples':result}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release',type=Path,required=True)
    p.add_argument('--geometry',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.output.mkdir(exist_ok=False,parents=True)
    r=manifest(a.release)
    m={x['id']:x for x in read(a.geometry)}
    if set(m)!={x['id'] for x in r}:
        raise ValueError('geometry inventory differs from release')
    flags=[]
    for row in r:
        g=m[row['id']]
        width=g['width_p50_px_after']
        scale=min(int(row['height']),int(row['width']))
        area=int(row['height'])*int(row['width'])
        flags.append(dict(id=row['id'],original_noncanonical_palette=int(row['original_off_palette_pixels'])>0,
                          original_ambiguous=int(row['original_ambiguous_pixels'])>0,
                          original_empty_line=int(row['line_before'])==0,reviewed_empty_line=int(row['line_after'])==0,
                          reviewed_empty_field_union=int(row['field_union_after'])==0,
                          reviewed_line_without_exclusive_field=int(row['line_after'])>0 and int(row['field_after'])==0,
                          reviewed_dense_line=int(row['line_after'])/area>.10,
                          reviewed_fragmented=(int(g['components_after'])>20 if g['components_after'] else None),
                          reviewed_many_tiny_components=(int(g['tiny_components_le4_after'])>=10 if g['tiny_components_le4_after'] else None),
                          reviewed_thin_width_flag=(float(width)<2 if width else None),
                          reviewed_wide_width_flag=(float(width)>max(20,.06*scale) if width else None),
                          field_union_delta_flag=int(row['field_union_changed_pixels'])>0))
    write_csv(a.output/'validation_flags.csv',flags)
    encode(a.output/'selection.json',picks(r))
    groups=defaultdict(list)
    for x in r:
        groups[x['group_id']].append(x)
    group_rows=[dict(group_id=k,reviewed=len(v),modified=sum(x['review_status']=='reviewed_modified' for x in v),
                     train=sum(x['original_image_path'].startswith('train/') for x in v),
                     test=sum(x['original_image_path'].startswith('test/') for x in v),
                     median_changed_percent=float(np.median([float(x['changed_percent']) for x in v])))
                for k,v in sorted(groups.items())]
    write_csv(a.output/'group_summary.csv',group_rows)
    mod=[x for x in r if x['review_status']=='reviewed_modified']
    def dup(key):
        counts=Counter(x[key] for x in r if x[key])
        return dict(repeated_groups=sum(n>1 for n in counts.values()),rows_in_repeated_groups=sum(n for n in counts.values() if n>1))
    result=dict(records=len(r),modified=len(mod),unchanged=len(r)-len(mod),groups=len(groups),
                stages=Counter(x['historical_annotation_stage'] for x in r),actions=Counter(x['review_action'] for x in r),
                split=Counter(x['original_image_path'].split('/')[0] for x in r),
                crosses_upstream_split=sum(g['train']>0 and g['test']>0 for g in group_rows),
                duplicate_source_image_bytes=dup('original_image_sha256'),duplicate_original_mask_bytes=dup('original_mask_sha256'),
                duplicate_reviewed_mask_bytes=dup('corrected_mask_sha256'),
                repeated_sequence_keys=dup('sequence_id'),
                bytes_identical=sum(x['byte_identical']=='True' for x in r),
                raw_grid_identical=sum(int(x['raw_value_changed_pixels'])==0 for x in r),
                all_change=describe(float(x['changed_percent']) for x in r),
                modified_change=describe(float(x['changed_percent']) for x in mod),
                count_sums={k:sum(int(x[k]) for x in r) for k in ('line_before','line_after','field_before','field_after',
                            'changed_pixels','raw_value_changed_pixels','comparable_pixels','field_union_changed_pixels')},
                flags={k:{'count':sum(f[k] is True for f in flags),'defined':sum(f[k] is not None for f in flags)}
                       for k in flags[0] if k!='id'},
                geometry_all={k:describe(float(x[k]) for x in m.values() if x[k]!='') for k in next(iter(m.values())) if k not in ('id','geometry_comparable')},
                geometry_modified={k:describe(float(m[x['id']][k]) for x in mod if m[x['id']][k]!='')
                                   for k in next(iter(m.values())) if k not in ('id','geometry_comparable')},
                empty_line_transition=Counter(f"{int(x['line_before'])>0}_to_{int(x['line_after'])>0}" for x in r))
    encode(a.output/'summary.json',result)
    plt.rcParams.update({'svg.hashsalt':'torso21-edit-v1','font.size':10})
    fig,axs=plt.subplots(1,3,figsize=(13,4.0),layout='constrained')
    vals=[float(x['changed_percent']) for x in mod]
    bins=[0,.1,.25,.5,1,2,4,8,16,32]
    hist,_=np.histogram(vals,bins)
    axs[0].bar(range(len(hist)),hist,color='#326a85')
    axs[0].set_xticks(range(len(hist)),[f'{a:g}–{b:g}' for a,b in zip(bins,bins[1:])],rotation=40,ha='right')
    axs[0].set(xlabel='Changed pixels per mask (%)',ylabel='Masks',title=f'Semantic edits (n={len(mod):,})')
    d=[float(m[x['id']]['line_dice']) for x in mod if m[x['id']]['line_dice']]
    axs[1].hist(d,bins=np.linspace(0,1,16),color='#477b66',edgecolor='white')
    axs[1].set(xlabel='Original vs. reviewed line Dice',ylabel='Masks',title=f'Line overlap (n={len(d):,})')
    widths=[[float(x[f'width_p50_px_{s}']) for x in m.values() if x[f'width_p50_px_{s}']] for s in ('before','after')]
    axs[2].boxplot(widths,tick_labels=['Original','Reviewed'],showfliers=False)
    axs[2].set(ylabel='Per-mask median width proxy (px)',title='Line width (nonempty masks)')
    axs[2].set_xticks([1,2],[f'Original\n(n={len(widths[0]):,})',f'Reviewed\n(n={len(widths[1]):,})'])
    fig.suptitle('TORSO-21 reviewed masks — description of changes, not annotation accuracy',fontsize=13)
    fig.savefig(a.output/'edit_distributions.png',dpi=160,metadata={'Software':'TORSO-21 overlay analysis'})
    fig.savefig(a.output/'edit_distributions.svg',metadata={'Date':None})
    plt.close(fig)


if __name__=='__main__':
    main()
