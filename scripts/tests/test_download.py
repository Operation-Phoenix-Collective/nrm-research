"""Offline test: a local mock of cibmtr.org built from a real captured page + AJAX response."""
import io, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, threading, urllib.parse, zipfile, csv
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
    hits = []
    def log_message(self, *a): pass
    def send(self, body, ctype):
        self.send_response(200); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        H.hits.append(self.path)
        if self.path.startswith('/CIBMTR/Resources/Publicly-Available-Datasets'):
            return self.send(fx['page_html'].encode(), 'text/html')
        m = re.search(r'/Documents/(P-\d+)[^/]*\.zip$', self.path)
        if m: return self.send(fake_zip(m.group(1)), 'application/zip')
        if '/DataDictionaryFiles/' in self.path:
            if 'P-4040' in self.path:
                self.send_response(404); self.end_headers(); return
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

spec = importlib.util.spec_from_file_location('download_cibmtr', script)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
spaced = 'https://cibmtr.org/ReferenceCenter/PubList/PubDsDownload/Documents/DataDictionaryFiles/P-5581/RT18-03 - data dictionary pub data.xlsx'
encoded = 'https://cibmtr.org/ReferenceCenter/PubList/PubDsDownload/Documents/DataDictionaryFiles/P-5581/RT18-03%20-%20data%20dictionary%20pub%20data.xlsx'
assert mod.request_url(spaced) == encoded
assert mod.request_url(encoded) == encoded
zd = tempfile.mkdtemp()
with zipfile.ZipFile(os.path.join(zd, 'z.zip'), 'w') as z:
    z.writestr('P-5181/dictionary_rt1402.rtf', b'a')
    z.writestr('dictionary_rt1402.rtf', b'a')
assert len(mod.dictionary_from_zip(os.path.join(zd, 'z.zip'), 'P-5181', zd)) == 1

extra = tempfile.mkdtemp()
host = f'http://127.0.0.1:{srv.server_port}'
cat_path = os.path.join(extra, 'in.csv')
fields = ['study_id', 'title', 'first_author', 'start_year', 'publication_url', 'dataset_zip_url', 'data_dictionary_url']
with open(cat_path, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fields); w.writeheader()
    w.writerow({'study_id': 'P-5581', 'title': 'space', 'first_author': '', 'start_year': '', 'publication_url': '',
                'dataset_zip_url': f'{host}/Documents/P-5581.zip',
                'data_dictionary_url': f'{host}/DataDictionaryFiles/P-5581/RT18-03 - data dictionary.xlsx'})
    w.writerow({'study_id': 'P-4040', 'title': 'missing', 'first_author': '', 'start_year': '', 'publication_url': '',
                'dataset_zip_url': f'{host}/Documents/P-4040.zip',
                'data_dictionary_url': f'{host}/DataDictionaryFiles/P-4040/missing.xlsx'})
r = subprocess.run([sys.executable, script, '--out', extra, '--delay', '0', '--catalog', cat_path], env=env, capture_output=True, text=True)
print(r.stdout[-700:], r.stderr[-400:], r.returncode)
assert r.returncode == 0, r.stdout
assert "'failed': 0" in r.stdout and "'recovered': 1" in r.stdout, r.stdout
assert any('%20' in h and 'RT18-03' in urllib.parse.unquote(h) for h in H.hits), H.hits
man = list(csv.DictReader(open(os.path.join(extra, 'manifest.csv'))))
assert sum(1 for m in man if m['study_id'] == 'P-4040' and m['status'] == 'extracted') == 1
assert any(m['study_id'] == 'P-5581' and m['kind'] == 'dictionary' and m['status'] == 'downloaded' for m in man)
shutil.rmtree(zd); shutil.rmtree(extra)

shutil.rmtree(out); srv.shutdown(); print('ALL TESTS PASSED')
