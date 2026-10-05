#!/usr/bin/env python3
"""
Download the research papers and reference documents cited in this repository.

Reads research/papers.csv and, for each row:
  * article  - looks the paper up in Europe PMC (by DOI, PMID or PMCID) and saves
               <key>.json (metadata), <key>.md (citation, abstract, access links) and,
               when a legal open-access copy exists, <key>.pdf
  * document - downloads the URL as-is (PDF or an HTML snapshot)
It then writes index.md and manifest.csv in the output folder.

Subscription-only papers are NOT downloaded; their .md file gives the DOI link
so you can get them through a library. Standard library only (Python 3.8+).

Examples:
  python3 scripts/download_papers.py                      # everything -> data/papers
  python3 scripts/download_papers.py --out ~/papers --keys shouval-2015-jco
  python3 scripts/download_papers.py --no-pdf             # metadata and abstracts only
"""
import argparse, csv, datetime, html, json, os, re, sys, time, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPMC = os.environ.get('EUROPEPMC_BASE', 'https://www.ebi.ac.uk/europepmc/webservices/rest')  # override only for tests
UA = 'Mozilla/5.0 (research-paper-downloader; +https://europepmc.org)'


def fetch(url, timeout=60, retries=3):
    last = None
    for i in range(retries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout)
            return r.read(), r.headers.get('Content-Type', ''), r.geturl()
        except Exception as e:
            last = e; time.sleep(2 ** i)
    raise last


def epmc_lookup(identifier):
    kind, _, value = identifier.partition(':')
    kind = kind.upper()
    if kind not in ('DOI', 'PMID', 'PMCID', 'EXT_ID'):
        raise ValueError(f'identifier must be DOI:, PMID: or PMCID: (got {identifier!r})')
    q = f'{kind}:"{value}"' if kind == 'DOI' else f'{kind}:{value}'
    url = f'{EPMC}/search?' + urllib.parse.urlencode({'query': q, 'format': 'json', 'resultType': 'core', 'pageSize': 25})
    data = json.loads(fetch(url)[0])
    for r in data.get('resultList', {}).get('result', []):
        if (kind == 'DOI' and (r.get('doi') or '').lower() == value.lower()) or \
           (kind == 'PMID' and r.get('pmid') == value) or (kind == 'PMCID' and r.get('pmcid') == value.upper()):
            return r
    return None


def oa_links(rec):
    links = (rec.get('fullTextUrlList') or {}).get('fullTextUrl', [])
    oa = [l for l in links if (l.get('availability') or '').lower().startswith('open access')]
    rank = lambda l: (l.get('documentStyle') != 'pdf', l.get('site') != 'Europe_PMC')
    return sorted(oa, key=rank), [l for l in links if l not in oa]


def citation(rec):
    j = rec.get('journalInfo') or {}
    jn = (j.get('journal') or {}).get('isoabbreviation') or (j.get('journal') or {}).get('title') or ''
    vol = j.get('volume') or ''; iss = f"({j['issue']})" if j.get('issue') else ''
    return f"{rec.get('authorString', '')} {rec.get('title', '')} *{jn}*. {j.get('yearOfPublication', '')};{vol}{iss}:{rec.get('pageInfo', '')}."


def strip_tags(s): return html.unescape(re.sub(r'<[^>]+>', ' ', s or '')).replace('  ', ' ').strip()


def write_article(rec, key, desc, out, want_pdf):
    json.dump(rec, open(os.path.join(out, f'{key}.json'), 'w'), indent=1)
    oa, other = oa_links(rec)
    pdf_status = 'no open-access copy'
    if want_pdf:
        for l in [l for l in oa if l.get('documentStyle') == 'pdf']:
            try:
                body, ctype, _ = fetch(l['url'])
                if body[:5] == b'%PDF-':
                    open(os.path.join(out, f'{key}.pdf'), 'wb').write(body)
                    pdf_status = f"downloaded from {l.get('site')}"; break
                pdf_status = f"{l.get('site')} did not return a PDF"
            except Exception as e:
                pdf_status = f"PDF download failed: {e}"
        else:
            if oa and pdf_status == 'no open-access copy':
                pdf_status = 'open-access copy is HTML only (see links)'
    elif oa:
        pdf_status = 'skipped (--no-pdf)'
    doi = rec.get('doi')
    lines = [f"# {strip_tags(rec.get('title'))}", '', f'_{desc}_', '', citation(rec), '',
             '| | |', '|---|---|',
             f"| DOI | {'[' + doi + '](https://doi.org/' + doi + ')' if doi else '–'} |",
             f"| PMID | {'[' + rec['pmid'] + '](https://pubmed.ncbi.nlm.nih.gov/' + rec['pmid'] + '/)' if rec.get('pmid') else '–'} |",
             f"| PMCID | {rec.get('pmcid') or '–'} |",
             f"| Open access | {'yes' if rec.get('isOpenAccess') == 'Y' else 'no'}{' (' + rec['license'] + ')' if rec.get('license') else ''} |",
             f"| Local PDF | {pdf_status} |", '', '## Access links', '']
    for l in oa + other:
        lines.append(f"- {l.get('availability')} ({l.get('documentStyle')}, {l.get('site')}): <{l.get('url')}>")
    lines += ['', '## Abstract', '', strip_tags(rec.get('abstractText')) or '_No abstract available._', '',
              f"_Metadata from Europe PMC, retrieved {datetime.date.today().isoformat()}._"]
    open(os.path.join(out, f'{key}.md'), 'w').write('\n'.join(lines) + '\n')
    return pdf_status


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--out', default=os.path.join(REPO, 'data', 'papers'), help='output folder (default: data/papers)')
    ap.add_argument('-l', '--list', default=os.path.join(REPO, 'research', 'papers.csv'), help='paper list CSV (default: research/papers.csv)')
    ap.add_argument('-k', '--keys', nargs='+', help='only these keys from the list')
    ap.add_argument('--no-pdf', action='store_true', help='skip PDF downloads (metadata and abstracts only)')
    ap.add_argument('--no-documents', action='store_true', help='skip rows of type "document"')
    a = ap.parse_args(argv)
    out = os.path.abspath(os.path.expanduser(a.out)); os.makedirs(out, exist_ok=True)
    rows = list(csv.DictReader(open(a.list, encoding='utf-8')))
    if a.keys: rows = [r for r in rows if r['key'] in a.keys]
    manifest, failed = [], 0
    for r in rows:
        key, typ = r['key'], r['type'].strip().lower()
        rec_out = {'key': key, 'type': typ, 'status': '', 'files': ''}
        try:
            if typ == 'article':
                rec = epmc_lookup(r['identifier'])
                if not rec: raise LookupError(f"not found in Europe PMC: {r['identifier']}")
                st = write_article(rec, key, r['description'], out, not a.no_pdf)
                rec_out.update(status=f'metadata saved; PDF: {st}', title=rec.get('title', ''), doi=rec.get('doi', ''),
                               files=' '.join(f for f in (f'{key}.md', f'{key}.json', f'{key}.pdf') if os.path.exists(os.path.join(out, f))))
            elif typ == 'document':
                if a.no_documents: rec_out['status'] = 'skipped'; manifest.append(rec_out); continue
                body, ctype, _ = fetch(r['url'])
                ext = '.pdf' if body[:5] == b'%PDF-' else '.html' if 'html' in ctype else os.path.splitext(urllib.parse.urlparse(r['url']).path)[1] or '.bin'
                open(os.path.join(out, key + ext), 'wb').write(body)
                rec_out.update(status='downloaded', title=r['description'], files=key + ext)
            else:
                raise ValueError(f'unknown type {typ!r}')
        except Exception as e:
            rec_out['status'] = f'failed: {e}'; failed += 1
        print(f"{key:24} {rec_out['status']}")
        manifest.append(rec_out)
    with open(os.path.join(out, 'manifest.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, ['key', 'type', 'title', 'doi', 'status', 'files'], extrasaction='ignore'); w.writeheader(); w.writerows(manifest)
    idx = ['# Research papers and documents', '', '| Key | Type | Title | Status | Files |', '|---|---|---|---|---|']
    for m in manifest:
        files = ', '.join(f'[{f}]({f})' for f in m['files'].split())
        idx.append(f"| {m['key']} | {m['type']} | {strip_tags(m.get('title', ''))[:100]} | {m['status']} | {files} |")
    open(os.path.join(out, 'index.md'), 'w').write('\n'.join(idx) + '\n')
    print(f'done: {len(manifest) - failed} ok, {failed} failed -> {out}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
