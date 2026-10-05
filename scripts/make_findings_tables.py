"""Emit the Markdown tables used in research/04-findings.md from data/*.csv."""
import csv, os, sys
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
rank = list(csv.DictReader(open(os.path.join(ROOT, 'nrm_candidate_ranking.csv'))))
Y = lambda r, k: '✓' if r[k] else '–'
def num(x):
    try: return f'{int(float(x)):,}'
    except: return '–'
def rate(x):
    try: return f'{float(x):.0%}'
    except: return '–'
def table(rows):
    print('| Study | Patients | TRM events (crude %) | NRM outcome | Age | KPS | HCT-CI | DRI | Disease status | Cytogenetics | Conditioning | Donor | Cause of death | Title |')
    print('|---|---:|---:|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|')
    for r in rows:
        ev = f"{num(r['trm_events'])} ({rate(r['trm_rate'])})" if r['trm_events'] else '–'
        nrm = {'explicit variable': 'variable'}.get(r['nrm_outcome'], r['nrm_outcome'].split(' (')[0])
        print(f"| [{r['study_id']}]({r['publication_url']}) | {num(r['n_patients'])} | {ev} | {nrm} | {Y(r,'p_age')} | {Y(r,'p_KPS')} | {Y(r,'p_HCT_CI')} | {Y(r,'p_DRI')} | {Y(r,'p_disease_status')} | {Y(r,'p_cytogenetics')} | {Y(r,'p_conditioning')} | {Y(r,'p_donor_type')} | {Y(r,'out_cause_death')} | {r['title'][:90]}{'…' if len(r['title'])>90 else ''} |")
which = sys.argv[1] if len(sys.argv) > 1 else 'A'
rows = [r for r in rank if r['tier'].startswith(which + ' ')]
rows.sort(key=lambda r: -int(r['n_patients'] or 0))
table(rows)
