from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json
import sys
from .core import checked, load_pair, manifest, original_pair, overlay, read_meta, safe, sha, write_csv, MANIFEST


def main():
    ap=ArgumentParser(description='Verify and use the TORSO-21 reviewed mask overlay.')
    ap.add_argument('--release-root',type=Path,default=Path.cwd())
    sub=ap.add_subparsers(dest='command',required=True)
    for name in ('verify','stats','materialize','compare','examples','extract-source'):
        c=sub.add_parser(name)
        if name=='verify':
            c.add_argument('--torso-root',type=Path)
        if name in ('materialize','compare','examples'):
            c.add_argument('--torso-root',type=Path,required=(name!='examples'))
            c.add_argument('--output',type=Path,required=(name!='examples'))
        if name=='extract-source':
            c.add_argument('--train-zip',type=Path,required=True)
            c.add_argument('--test-zip',type=Path,required=True)
            c.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    root=a.release_root.resolve()
    records=manifest(root)
    meta=read_meta(root)
    if sha(safe(root,MANIFEST).read_bytes())!=meta['manifest_sha256'] or len(records)!=meta['row_count']:
        raise ValueError('manifest digest or row count mismatch')
    if a.command=='stats':
        print(json.dumps({'records':len(records),'review_status':Counter(r['review_status'] for r in records),
                          'groups':len({r['group_id'] for r in records}),
                          'changed_pixels':sum(int(r['changed_pixels']) for r in records),
                          'independent_audit':'NOT_RUN'},indent=2))
    elif a.command=='verify':
        actual={p.relative_to(root).as_posix() for p in (root/'annotations').glob('*.png')}
        if actual!={r['corrected_mask_path'] for r in records}:
            raise ValueError('missing or extra annotation payloads')
        for r in records:
            if a.torso_root:
                load_pair(root,a.torso_root,r)
            else:
                overlay(root,r)
        print(json.dumps({'status':'PASS','reviewed_masks':len(records),'source_pairs_checked':len(records) if a.torso_root else 0}))
    elif a.command=='materialize':
        # Preflight all sources and output paths before creating anything.
        destination=a.output.resolve()
        source=a.torso_root.resolve()
        if destination.is_relative_to(source) or destination.is_relative_to(root):
            raise ValueError('output must be outside the original and release roots')
        for r in records:
            original_pair(source,r)
            overlay(root,r)
        destination.mkdir(parents=True,exist_ok=False)
        for r in records:
            out=safe(destination,r['original_mask_path'])
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(checked(safe(root,r['corrected_mask_path']),r['corrected_mask_sha256']))
        write_csv(destination/'overlay_index.csv',[
            {'id':r['id'],'image_relative_to_torso_root':r['original_image_path'],
             'reviewed_mask_relative_to_output':r['original_mask_path'],'reviewed_mask_sha256':r['corrected_mask_sha256']}
            for r in records])
        print(f'Materialized {len(records)} masks. Images remain under the supplied TORSO root.')
    elif a.command=='compare':
        from .geometry import measure
        if a.output.exists() or a.output.resolve().is_relative_to(a.torso_root.resolve()):
            raise ValueError('comparison output exists or is inside original data')
        empty_fields=measure(__import__('numpy').zeros((3,3),dtype='uint8'),__import__('numpy').zeros((3,3),dtype='uint8'))
        def table():
            for r in records:
                _,old,new=load_pair(root,a.torso_root,r)
                eligible=not int(r['original_ambiguous_pixels'])
                yield {'id':r['id'],'geometry_comparable':eligible,
                       **(measure(old,new) if eligible else dict.fromkeys(empty_fields))}
        write_csv(a.output,list(table()))
        print(f'Wrote paired change statistics for {len(records)} pairs.')
    elif a.command=='examples':
        from .examples import examples
        examples(root,records,a.torso_root,a.output)
    elif a.command=='extract-source':
        from .source import extract
        extract(records,a.train_zip,a.test_zip,a.output)


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,KeyError) as e:
        sys.exit(str(e))
