"""Check distribution metadata and both manifests without upstream data."""
from collections import Counter
from pathlib import Path
from importlib.metadata import version
import pyarrow as pa
import pyarrow.parquet as pq
from torso_line_corrections.core import manifest, read_meta, sha


def from_csv(text, kind):
    if pa.types.is_string(kind):
        return text
    if not text:
        return None
    if pa.types.is_boolean(kind):
        return {'True': True, 'False': False}[text]
    if pa.types.is_integer(kind):
        return int(text)
    if pa.types.is_floating(kind):
        return float(text)
    raise ValueError(f'Unsupported Parquet field type: {kind}')


def main():
    root = Path(__file__).resolve().parents[1]
    meta = read_meta(root)
    path = root / 'manifests/reviewed_masks_manifest.parquet'
    if sha(path.read_bytes()) != meta['parquet_sha256']:
        raise ValueError('Parquet checksum mismatch')
    data = pq.read_table(path)
    rows = manifest(root)
    if set(data.column_names) != set(rows[0]):
        raise ValueError('CSV and Parquet column sets differ')
    decoded = [{f.name: from_csv(row[f.name], f.type) for f in data.schema} for row in rows]
    if decoded != data.to_pylist():
        raise ValueError('CSV and Parquet rows differ')
    counts = Counter(r['review_status'] for r in rows)
    if (len(rows), counts['reviewed_modified'], counts['reviewed_unchanged']) != (
        meta['row_count'], meta['modified'], meta['unchanged']
    ):
        raise ValueError('Metadata counts differ from the manifest')
    if version('torso-line-corrections') != meta['version']:
        raise ValueError('Installed package version differs from metadata')
    print(f'PASS: CSV and Parquet agree on {len(rows)} rows: '
          f'{counts["reviewed_modified"]} modified, {counts["reviewed_unchanged"]} unchanged.')


if __name__ == '__main__':
    main()
