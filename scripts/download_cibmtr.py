#!/usr/bin/env python3
"""
Download CIBMTR "Publicly Available Datasets" (dataset zips and/or data dictionaries).

Source page: https://cibmtr.org/CIBMTR/Resources/Publicly-Available-Datasets
Use of the data is governed by CIBMTR's Terms and Conditions (a copy ships inside
every dataset zip):
  https://cibmtr.org/Files/Publicly-Available-Datasets/TermsAndConditions.pdf

Standard library only (Python 3.8+). Examples:

  # everything (datasets + dictionaries) into ~/Data/cibmtr
  python3 download_cibmtr.py --out ~/Data/cibmtr

  # only the data dictionaries
  python3 download_cibmtr.py --out ~/Data/cibmtr --what dictionaries

  # just a few studies, and unzip the datasets
  python3 download_cibmtr.py --out ~/Data/cibmtr --ids P-5370 P-5702 P-5300 --extract

  # only the studies listed in a CSV (any CSV with a study_id column, e.g. the
  # nrm_candidate_ranking.csv, optionally filtered by its "tier" column)
  python3 download_cibmtr.py --out ~/Data/cibmtr --ids-from nrm_candidate_ranking.csv --tier A B

  # just refresh the catalog (no downloads)
  python3 download_cibmtr.py --out ~/Data/cibmtr --list-only

Output layout (inside --out):
  catalog.csv                 every study found on the site, with URLs
  manifest.csv                one row per file attempted: status, bytes, sha256
  datasets/P-XXXX.zip         dataset zips (SAS .sas7bdat + dictionary + T&C)
  datasets_extracted/P-XXXX/  (with --extract)
  dictionaries/P-XXXX__<original name>
  dictionaries/_broken_site_links/   pages the site served instead of a file
"""
import argparse, csv, datetime, hashlib, html, http.cookiejar, json, os, re, sys, time
import urllib.error, urllib.parse, urllib.request, zipfile
from html.parser import HTMLParser

BASE = os.environ.get('CIBMTR_BASE', 'https://cibmtr.org')   # override only for testing
PAGE = BASE + '/CIBMTR/Resources/Publicly-Available-Datasets'
AJAX = BASE + '/DataAjax/GetDataListResults'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 cibmtr-downloader'


def request_url(url):
    """Percent-encode a site href. The listing page leaves spaces in some dictionary links."""
    if not url:
        return url
    p = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(p.path), safe='/:@')
    query = urllib.parse.quote(urllib.parse.unquote(p.query), safe='=&?/:@,+')
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path, query, p.fragment))


# ---------------------------------------------------------------- HTTP
class Http:
    def __init__(self, retries=3, timeout=120, delay=0.5):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.retries, self.timeout, self.delay = retries, timeout, delay

    def _req(self, url, data=None, headers=None):
        url = request_url(url)
        h = {'User-Agent': UA, 'Referer': PAGE}
        h.update(headers or {})
        last = None
        for attempt in range(1, self.retries + 1):
            try:
                r = self.op.open(urllib.request.Request(url, data=data, headers=h), timeout=self.timeout)
                return r
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last = e
                if isinstance(e, urllib.error.HTTPError) and e.code in (403, 404):
                    raise
                time.sleep(min(2 ** attempt, 20))
        raise last

    def text(self, url, data=None, headers=None):
        with self._req(url, data, headers) as r:
            return r.read().decode(r.headers.get_content_charset() or 'utf-8', 'replace')

    def download(self, url, dest):
        """Stream url to dest (via .part). Returns (bytes, sha256, content_type)."""
        tmp = dest + '.part'
        h = hashlib.sha256(); n = 0
        with self._req(url) as r, open(tmp, 'wb') as fh:
            ctype = r.headers.get('Content-Type', '')
            while True:
                b = r.read(1 << 16)
                if not b: break
                fh.write(b); h.update(b); n += len(b)
        os.replace(tmp, dest)
        time.sleep(self.delay)
        return n, h.hexdigest(), ctype


# ---------------------------------------------------------------- listing parser
class ItemParser(HTMLParser):
    """Parses the <div class="item"> cards of the dataset list."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items, self.cur, self.depth = [], None, 0
        self.in_teaser = self.in_label = False
        self.p_text, self.a_href, self.a_text = None, None, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = (a.get('class') or '').split()
        if tag == 'div':
            if 'item' in cls and self.cur is None:
                self.cur = {'title': '', 'start_year': '', 'first_author': '', 'publication_url': '',
                            'dataset_zip_url': '', 'data_dictionary_url': ''}
                self.depth = 1; return
            if self.cur is not None: self.depth += 1
        if self.cur is None: return
        if tag == 'p' and 'teaser' in cls: self.in_teaser = True
        elif tag == 'p' and 'Authors' in cls: self.p_text = ''
        elif tag == 'span' and 'label' in cls and self.p_text is not None: self.in_label = True
        elif tag == 'a': self.a_href, self.a_text = a.get('href'), ''

    def handle_endtag(self, tag):
        if self.cur is None: return
        if tag == 'p':
            if self.in_teaser: self.in_teaser = False
            if self.p_text is not None:
                t = re.sub(r'\s+', ' ', self.p_text).strip()
                m = re.match(r'(Start Year of Infusion|First Author):\s*(.*)', t)
                if m: self.cur['start_year' if m.group(1).startswith('Start') else 'first_author'] = m.group(2)
                self.p_text = None
        elif tag == 'span': self.in_label = False
        elif tag == 'a' and self.a_href:
            label = self.a_text.strip().lower(); url = request_url(urllib.parse.urljoin(BASE, self.a_href))
            if label.startswith('view'): self.cur['publication_url'] = url
            elif label == 'dataset': self.cur['dataset_zip_url'] = url
            elif label.startswith('data dictionary'): self.cur['data_dictionary_url'] = url
            self.a_href = None
        elif tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                self.cur['title'] = re.sub(r'\s+', ' ', self.cur['title']).strip()
                self.items.append(self.cur); self.cur = None

    def handle_data(self, d):
        if self.cur is None: return
        if self.in_teaser: self.cur['title'] += d
        if self.p_text is not None: self.p_text += d
        if self.a_href is not None: self.a_text += d


def parse_items(fragment):
    p = ItemParser(); p.feed(fragment); p.close()
    for it in p.items:
        m = re.search(r'(P-\d+)', it['publication_url']) or re.search(r'(P-\d+)', it['dataset_zip_url'])
        it['study_id'] = m.group(1) if m else ''
    return p.items


def total_pages(fragment):
    m = re.search(r'Page\s+\d+\s+of\s+(\d+)', fragment)
    return int(m.group(1)) if m else 1


def fetch_catalog(http_, log):
    page = http_.text(PAGE)
    tok = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', page)
    doc = re.search(r"<meta name='DocID' content='(\d+)'", page) or re.search(r'_DocID" value="(\d+)"', page)
    blk = re.search(r'blockID="(\d+)"', page)
    items = parse_items(page)
    pages = total_pages(page)
    log(f'catalog: page 1/{pages} -> {len(items)} studies')
    if not (tok and doc and blk):
        raise RuntimeError('could not find the paging token on the page (site layout changed?)')
    for n in range(2, pages + 1):
        form = {
            '__RequestVerificationToken': tok.group(1), 'docID': doc.group(1), 'blockID': blk.group(1),
            'queryData.pageNumber': str(n), 'queryData.sortKey': 'Priority', 'queryData.sortDirection': '',
            'queryData.keyword': '', 'queryData.classifications': '', 'queryData.startDate': '',
            'queryData.endDate': '', 'queryData.widgetDate': '', 'queryData.latitude': 'NaN',
            'queryData.longitude': 'NaN', 'queryData.radius': 'NaN',
            'queryData.userRanges[0].dataField': '120', 'queryData.userRanges[0].rangeType': 'Text',
            'queryData.userRanges[0].minValue': '', 'queryData.userRanges[0].maxValue': '',
            'queryData.userRanges[0].betweenMinValue': '1900', 'queryData.userRanges[0].betweenMaxValue': '2100',
            'queryData.userRanges[0].containsValue': '',
        }
        body = urllib.parse.urlencode(form).encode()
        js = json.loads(http_.text(AJAX, body, {'X-Requested-With': 'XMLHttpRequest',
                                               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}))
        got = parse_items(js['htmlData'])
        log(f'catalog: page {n}/{pages} -> {len(got)} studies')
        items += got
        time.sleep(http_.delay)
    seen, out = set(), []
    for it in items:                       # de-duplicate (site occasionally repeats a card)
        k = it['dataset_zip_url'] or it['title']
        if k not in seen: seen.add(k); out.append(it)
    return out


CAT_FIELDS = ['study_id', 'title', 'first_author', 'start_year', 'publication_url', 'dataset_zip_url', 'data_dictionary_url']


def read_catalog(path):
    with open(path, newline='', encoding='utf-8') as fh:
        return [{k: r.get(k, '') for k in CAT_FIELDS} for r in csv.DictReader(fh)]


def write_csv(path, rows, fields):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)


# ---------------------------------------------------------------- helpers
def looks_like_html(path):
    with open(path, 'rb') as fh: head = fh.read(512).lstrip().lower()
    return head.startswith(b'<!doctype html') or head.startswith(b'<html')


def safe_name(s): return re.sub(r'[\\/:*?"<>|]+', '_', s).strip()


DICT_RX = re.compile(r'dict|data[_ -]?dic', re.I)


def dictionary_from_zip(zpath, sid, dest_dir):
    """Fallback: pull the data dictionary out of the dataset zip."""
    out, seen = [], set()
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            base = os.path.basename(n)
            if not base or base.lower().endswith(('.sas7bdat', '.sas7bcat')) or 'terms' in base.lower(): continue
            if DICT_RX.search(base) or base.lower().endswith(('.xlsx', '.xls')):
                dest = os.path.join(dest_dir, f'{sid}__from-dataset-zip__{safe_name(base)}')
                if dest in seen: continue
                seen.add(dest)
                if not os.path.exists(dest):
                    with z.open(n) as src, open(dest, 'wb') as fh: fh.write(src.read())
                out.append(dest)
    return out


def extract(zpath, dest):
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        for m in z.infolist():
            target = os.path.realpath(os.path.join(dest, m.filename))
            if not target.startswith(os.path.realpath(dest) + os.sep): continue   # zip-slip guard
            z.extract(m, dest)


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description='Download CIBMTR publicly available datasets and data dictionaries.',
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('-o', '--out', required=True, help='download folder (created if missing)')
    ap.add_argument('-w', '--what', choices=['all', 'datasets', 'dictionaries'], default='all', help='what to download (default: all)')
    ap.add_argument('--ids', nargs='+', metavar='P-XXXX', help='only these study IDs')
    ap.add_argument('--ids-from', metavar='CSV', help='only study IDs in this CSV (needs a study_id column)')
    ap.add_argument('--tier', nargs='+', metavar='T', help='with --ids-from: keep rows whose "tier" column starts with one of these (e.g. A B)')
    ap.add_argument('--catalog', metavar='CSV', help="use this catalog CSV instead of reading the website's list")
    ap.add_argument('--list-only', action='store_true', help='only write catalog.csv; download nothing')
    ap.add_argument('--extract', action='store_true', help='unzip each dataset into datasets_extracted/<study>/')
    ap.add_argument('--overwrite', action='store_true', help='re-download files that already exist')
    ap.add_argument('--delay', type=float, default=0.5, help='seconds to pause between downloads (default 0.5)')
    ap.add_argument('--retries', type=int, default=3, help='attempts per file (default 3)')
    ap.add_argument('--timeout', type=int, default=120, help='per-request timeout in seconds (default 120)')
    ap.add_argument('-q', '--quiet', action='store_true')
    a = ap.parse_args(argv)

    log = (lambda *x: None) if a.quiet else (lambda *x: print(*x, flush=True))
    out = os.path.abspath(os.path.expanduser(a.out))
    os.makedirs(out, exist_ok=True)
    http_ = Http(a.retries, a.timeout, a.delay)

    # 1. catalog
    if a.catalog:
        cat = read_catalog(a.catalog); log(f'catalog: {len(cat)} studies from {a.catalog}')
    else:
        try:
            cat = fetch_catalog(http_, log)
        except Exception as e:
            fallback = os.path.join(out, 'catalog.csv')
            if os.path.exists(fallback):
                log(f'WARNING: could not read the website list ({e}); using existing {fallback}')
                cat = read_catalog(fallback)
            else:
                sys.exit(f'ERROR: could not read the website list: {e}\n'
                         f'       pass --catalog <csv> to use a saved catalog instead.')
        else:
            write_csv(os.path.join(out, 'catalog.csv'), cat, CAT_FIELDS)
            log(f'catalog: {len(cat)} studies -> {os.path.join(out, "catalog.csv")}')
    if a.list_only: return 0

    # 2. selection
    want = set(i.upper() for i in (a.ids or []))
    if a.ids_from:
        with open(a.ids_from, newline='', encoding='utf-8') as fh:
            for r in csv.DictReader(fh):
                if a.tier and not any((r.get('tier') or '').upper().startswith(t.upper()) for t in a.tier): continue
                if r.get('study_id'): want.add(r['study_id'].upper())
    sel = [c for c in cat if not want or c['study_id'].upper() in want]
    missing = want - {c['study_id'].upper() for c in cat}
    if missing: log('WARNING: not in catalog:', ' '.join(sorted(missing)))
    log(f'selected {len(sel)} studies; downloading: {a.what}')

    dd_dir, ds_dir = os.path.join(out, 'dictionaries'), os.path.join(out, 'datasets')
    bad_dir, ex_dir = os.path.join(dd_dir, '_broken_site_links'), os.path.join(out, 'datasets_extracted')
    for d in ([dd_dir] if a.what != 'datasets' else []) + ([ds_dir] if a.what != 'dictionaries' else []):
        os.makedirs(d, exist_ok=True)

    manifest, stats = [], {'downloaded': 0, 'skipped': 0, 'failed': 0, 'broken_link': 0, 'recovered': 0}
    now = lambda: datetime.datetime.now().isoformat(timespec='seconds')

    def get(sid, kind, url, dest):
        rec = {'study_id': sid, 'kind': kind, 'url': url, 'path': os.path.relpath(dest, out), 'status': '', 'bytes': '', 'sha256': '', 'when': now()}
        if not url:
            rec['status'] = 'no link on site'; stats['failed'] += 1; manifest.append(rec); return None
        if os.path.exists(dest) and os.path.getsize(dest) > 0 and not a.overwrite:
            rec.update(status='skipped (exists)', bytes=os.path.getsize(dest)); stats['skipped'] += 1; manifest.append(rec); return dest
        try:
            n, sha, ctype = http_.download(url, dest)
        except Exception as e:
            rec['status'] = f'failed: {e}'; stats['failed'] += 1; manifest.append(rec); log(f'  FAIL {sid} {kind}: {e}'); return None
        rec.update(bytes=n, sha256=sha)
        if looks_like_html(dest):      # site sometimes serves its HTML page instead of the file
            os.makedirs(bad_dir, exist_ok=True)
            moved = os.path.join(bad_dir, os.path.basename(dest) + '.html'); os.replace(dest, moved)
            rec.update(status='broken link (site returned a web page)', path=os.path.relpath(moved, out))
            stats['broken_link'] += 1; manifest.append(rec); log(f'  BROKEN {sid} {kind}: site returned HTML'); return None
        rec['status'] = 'downloaded'; stats['downloaded'] += 1; manifest.append(rec); return dest

    for i, c in enumerate(sel, 1):
        sid = c['study_id'] or f'row{i}'
        log(f'[{i}/{len(sel)}] {sid}  {c["title"][:70]}')
        zpath = None
        if a.what in ('all', 'datasets'):
            zname = safe_name(os.path.basename(urllib.parse.urlparse(c['dataset_zip_url']).path)) or f'{sid}.zip'
            if not zname.upper().startswith(sid.upper()): zname = f'{sid}__{zname}'
            zpath = get(sid, 'dataset', c['dataset_zip_url'], os.path.join(ds_dir, zname))
            if zpath and a.extract:
                try: extract(zpath, os.path.join(ex_dir, sid))
                except zipfile.BadZipFile: log(f'  WARN {sid}: dataset is not a valid zip')
        if a.what in ('all', 'dictionaries'):
            dname = safe_name(urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(c['data_dictionary_url']).path)))
            failed_before = stats['failed']
            got = get(sid, 'dictionary', c['data_dictionary_url'], os.path.join(dd_dir, f'{sid}__{dname}')) if dname else None
            if not got:
                # fall back to the dictionary inside the dataset zip (download the zip if needed)
                recovered = []
                if not zpath:
                    tmpz = os.path.join(out, '.tmp_' + sid + '.zip')
                    try: http_.download(c['dataset_zip_url'], tmpz); zpath = tmpz
                    except Exception: zpath = None
                if zpath:
                    try:
                        recovered = dictionary_from_zip(zpath, sid, dd_dir)
                        for p in recovered:
                            manifest.append({'study_id': sid, 'kind': 'dictionary (from dataset zip)', 'url': c['dataset_zip_url'],
                                             'path': os.path.relpath(p, out), 'status': 'extracted', 'bytes': os.path.getsize(p), 'sha256': '', 'when': now()})
                            log(f'  recovered dictionary from dataset zip: {os.path.basename(p)}')
                    except zipfile.BadZipFile: pass
                    if os.path.basename(zpath).startswith('.tmp_'): os.remove(zpath)
                if recovered:
                    if stats['failed'] > failed_before: stats['failed'] -= 1
                    stats['recovered'] += 1

    write_csv(os.path.join(out, 'manifest.csv'), manifest, ['study_id', 'kind', 'url', 'path', 'status', 'bytes', 'sha256', 'when'])
    log(f'done: {stats}  ->  {out}')
    log('Reminder: use is subject to the CIBMTR Terms and Conditions included in each dataset zip.')
    return 1 if stats['failed'] else 0


if __name__ == '__main__':
    sys.exit(main())
