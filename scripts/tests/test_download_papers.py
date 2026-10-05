"""Offline test for download_papers.py against a local mock of the Europe PMC API,
built from a real captured search response (tests/europepmc_fixture.json)."""
import csv, json, os, re, shutil, subprocess, sys, tempfile, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
HERE = os.path.dirname(os.path.abspath(__file__))
FX = json.load(open(os.path.join(HERE, 'europepmc_fixture.json')))
PORT = None

def localize(rec):
    rec = json.loads(json.dumps(rec))
    for l in rec.get('fullTextUrlList', {}).get('fullTextUrl', []):
        l['url'] = f'http://127.0.0.1:{PORT}/file/' + urllib.parse.quote(l['url'], safe='')
    return rec

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, body, ctype, code=200):
        self.send_response(code); self.send_header('Content-Type', ctype); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path.endswith('/search'):
            q = urllib.parse.parse_qs(u.query)['query'][0]
            kind, val = q.split(':', 1); val = val.strip('"').lower()
            hits = [localize(r) for r in FX['resultList']['result']
                    if (r.get({'DOI': 'doi', 'PMID': 'pmid', 'PMCID': 'pmcid'}[kind]) or '').lower() == val]
            return self.send(json.dumps({'hitCount': len(hits), 'resultList': {'result': hits}}).encode(), 'application/json')
        if u.path.startswith('/file/'):
            orig = urllib.parse.unquote(u.path[len('/file/'):])
            if 'pdf' in orig or 'printable' in orig: return self.send(b'%PDF-1.4 fake', 'application/pdf')
            return self.send(b'<html>landing page</html>', 'text/html')
        if u.path == '/doc.pdf': return self.send(b'%PDF-1.7 terms', 'application/pdf')
        if u.path == '/page': return self.send(b'<html>page</html>', 'text/html; charset=utf-8')
        self.send(b'not found', 'text/plain', 404)

srv = ThreadingHTTPServer(('127.0.0.1', 0), H); PORT = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
tmp = tempfile.mkdtemp(); out = os.path.join(tmp, 'papers'); lst = os.path.join(tmp, 'papers.csv')
with open(lst, 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['key', 'type', 'identifier', 'url', 'description'])
    w.writerow(['mussetti', 'article', 'DOI:10.1038/s41409-023-02147-5', '', 'paywalled'])
    w.writerow(['shouval2015', 'article', 'DOI:10.1200/JCO.2014.59.1339', '', 'green OA html'])
    w.writerow(['shouval2016', 'article', 'PMCID:PMC4778768', '', 'gold OA pdf'])
    w.writerow(['terms', 'document', '', f'http://127.0.0.1:{PORT}/doc.pdf', 'terms'])
    w.writerow(['page', 'document', '', f'http://127.0.0.1:{PORT}/page', 'a page'])
    w.writerow(['missing', 'article', 'PMID:1', '', 'not in fixture'])
env = dict(os.environ, EUROPEPMC_BASE=f'http://127.0.0.1:{PORT}/rest')
script = os.path.join(os.path.dirname(HERE), 'download_papers.py')
r = subprocess.run([sys.executable, script, '--out', out, '--list', lst], env=env, capture_output=True, text=True)
print(r.stdout, r.stderr)
files = sorted(os.listdir(out)); print(files)
assert r.returncode == 1, 'one row is expected to fail'
assert {'mussetti.md', 'mussetti.json', 'shouval2015.md', 'shouval2016.pdf', 'terms.pdf', 'page.html', 'index.md', 'manifest.csv'} <= set(files)
assert 'mussetti.pdf' not in files and 'shouval2015.pdf' not in files
md = open(os.path.join(out, 'mussetti.md')).read()
assert 'https://doi.org/10.1038/s41409-023-02147-5' in md and 'Open access | no' in md and '## Abstract' in md
assert 'HTML only' in open(os.path.join(out, 'shouval2015.md')).read()
assert 'downloaded from Europe_PMC' in open(os.path.join(out, 'shouval2016.md')).read()
man = {m['key']: m for m in csv.DictReader(open(os.path.join(out, 'manifest.csv')))}
assert man['missing']['status'].startswith('failed: not found')
r2 = subprocess.run([sys.executable, script, '--out', out, '--list', lst, '--keys', 'shouval2016', '--no-pdf'], env=env, capture_output=True, text=True)
assert 'skipped (--no-pdf)' in r2.stdout, r2.stdout
srv.shutdown(); shutil.rmtree(tmp); print('ALL TESTS PASSED')
