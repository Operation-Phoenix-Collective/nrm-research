"""Offline test: a local mock of cibmtr.org built from a real captured page + AJAX response."""
import io, json, os, re, shutil, subprocess, sys, tempfile, threading, zipfile, csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
HERE = os.path.dirname(os.path.abspath(__file__))
fx = json.load(open(os.path.join(HERE, 'cibmtr_fixture.json')))
BROKEN = 'P-6309'   # pretend its dictionary link is broken

def fake_zip(sid):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr(f'{sid}/data.sas7bdat', b'SAS' * 10)
        z.writestr(f'{sid}/{sid} data dictionary.xlsx', b'PK-fake-xlsx-' + sid.encode())
        z.writestr(f'{sid}/Publicly Available Dataset Terms and Conditions.pdf', b'%PDF')
    return b.getvalue()

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, body, ctype):
        self.send_response(200); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path.startswith('/CIBMTR/Resources/Publicly-Available-Datasets'):
            return self.send(fx['page_html'].encode(), 'text/html')
        m = re.search(r'/Documents/(P-\d+)[^/]*\.zip$', self.path)
        if m: return self.send(fake_zip(m.group(1)), 'application/zip')
        if '/DataDictionaryFiles/' in self.path:
            if BROKEN in self.path: return self.send(b'<!DOCTYPE html><html>not a file</html>', 'text/html')
            return self.send(b'PK-dict', 'application/octet-stream')
        self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(n).decode()
        assert '__RequestVerificationToken=' in body and 'queryData.userRanges' in body, body
        return self.send(fx['ajax_page8'].encode(), 'application/json')

srv = ThreadingHTTPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
env = dict(os.environ, CIBMTR_BASE=f'http://127.0.0.1:{srv.server_port}')
script = os.path.join(os.path.dirname(HERE), 'download_cibmtr.py')
out = tempfile.mkdtemp()
run = lambda *a: subprocess.run([sys.executable, script, '--out', out, '--delay', '0', *a], env=env, capture_output=True, text=True)

r = run('--list-only'); print(r.stdout[-300:], r.stderr[-500:])
cat = list(csv.DictReader(open(os.path.join(out, 'catalog.csv'))))
assert len(cat) == 40, len(cat)                       # page 1 (20) + page 8 (20); pages 2-7 are the same fixture, de-duplicated
assert all(c['study_id'].startswith('P-') and c['dataset_zip_url'] and c['title'] for c in cat)
assert cat[0]['study_id'] == 'P-5051' and cat[0]['start_year'] == '1990' and cat[0]['first_author'] == 'Deepak Kilari', cat[0]

r = run('--ids', 'P-5051', BROKEN, 'P-9999', '--extract'); print(r.stdout[-900:], r.stderr[-500:])
files = sorted(os.path.relpath(os.path.join(d, f), out) for d, _, fs in os.walk(out) for f in fs)
print('\n'.join(files))
assert 'datasets/P-50512.zip' in files or any(f.startswith('datasets/P-5051') for f in files)
assert any(f.startswith(f'dictionaries/{BROKEN}__from-dataset-zip__') for f in files), 'fallback dictionary missing'
assert any(f.startswith('dictionaries/_broken_site_links/') for f in files)
assert any(f.startswith('datasets_extracted/P-5051/') for f in files)
assert 'not in catalog: P-9999' in r.stdout

r = run('--ids', 'P-5051', '--what', 'dictionaries'); assert "'skipped': 1" in r.stdout, r.stdout
man = list(csv.DictReader(open(os.path.join(out, 'manifest.csv')))); assert man[0]['status'].startswith('skipped')
shutil.rmtree(out); srv.shutdown(); print('ALL TESTS PASSED')
