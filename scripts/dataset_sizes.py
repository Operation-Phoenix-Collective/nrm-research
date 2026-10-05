"""Count patients (rows) and crude TRM events in each downloaded CIBMTR dataset zip.

Usage:
    python3 scripts/dataset_sizes.py <download-folder> [output.csv]

<download-folder> is the --out folder of download_cibmtr.py (it must contain
datasets/ and manifest.csv). Output defaults to data/dataset_sizes.csv.
Only aggregate counts are written; no patient-level data leaves the zips.

Per study, the largest .sas7bdat file is treated as the primary analysis file.
trm_events / trm_rate use a variable named exactly `trm` coded 0/1, so the rate
is a crude proportion of patients with a TRM event, not a cumulative incidence.
Requires: pandas
"""
import csv, os, sys, tempfile, zipfile
import pandas as pd

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = os.path.abspath(os.path.expanduser(sys.argv[1]))
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(repo, 'data', 'dataset_sizes.csv')
    zip_to_sid = {os.path.basename(r['path']): r['study_id']
                  for r in csv.DictReader(open(os.path.join(src, 'manifest.csv'))) if r['kind'] == 'dataset'}
    rows = []
    for zf in sorted(os.listdir(os.path.join(src, 'datasets'))):
        if not zf.lower().endswith('.zip'): continue
        rec = {'study_id': zip_to_sid.get(zf, zf.split('.')[0].split('__')[0]), 'dataset_zip': zf,
               'sas_files': 0, 'n_patients_rows': 0, 'n_columns': '', 'trm_events': '', 'trm_nonmissing': '',
               'trm_rate': '', 'other_sas_files': '', 'note': ''}
        try:
            z = zipfile.ZipFile(os.path.join(src, 'datasets', zf))
            sas = [n for n in z.namelist() if n.lower().endswith('.sas7bdat') and not os.path.basename(n).startswith('~$')]
            rec['sas_files'] = len(sas)
            if not sas:
                rec['note'] = 'no data file in zip'
            frames = []
            for s in sas:
                with tempfile.NamedTemporaryFile(suffix='.sas7bdat') as t:
                    t.write(z.read(s)); t.flush()
                    frames.append((s, pd.read_sas(t.name, format='sas7bdat', encoding='latin-1')))
            if frames:
                frames.sort(key=lambda x: -len(x[1]))
                name, df = frames[0]
                rec['n_patients_rows'], rec['n_columns'] = len(df), df.shape[1]
                rec['other_sas_files'] = '; '.join(f'{os.path.basename(n)} ({len(d)} rows)' for n, d in frames[1:])
                cols = {c.lower(): c for c in df.columns}
                if 'trm' in cols:
                    v = df[cols['trm']]; nonmiss = int(v.isin([0, 1]).sum())
                    rec['trm_events'], rec['trm_nonmissing'] = int((v == 1).sum()), nonmiss
                    rec['trm_rate'] = round(rec['trm_events'] / nonmiss, 3) if nonmiss else ''
        except Exception as e:
            rec['note'] = f'error: {e}'[:200]
        rows.append(rec)
    rows.sort(key=lambda r: r['study_id'])
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f'{len(rows)} datasets, {sum(r["n_patients_rows"] for r in rows):,} rows -> {out}')

if __name__ == '__main__':
    main()
