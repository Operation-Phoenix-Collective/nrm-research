"""Parse the CIBMTR public-dataset data dictionaries (xlsx/xls/docx/rtf/pdf)
into one long table: study_id, variable, description, type, value, label."""
import csv, glob, os, re, sys
import openpyxl, xlrd, docx, pdfplumber
from striprtf.striprtf import rtf_to_text

# Data folder: first CLI argument, else $CIBMTR_DATA_DIR, else <repo>/data
ROOT = os.path.abspath(os.path.expanduser(
    (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None)
    or os.environ.get('CIBMTR_DATA_DIR')
    or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')))
DD = os.path.join(ROOT, 'dictionaries')

def rows_xlsx(f):
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            yield [('' if c is None else str(c)).strip() for c in r]

def rows_xls(f):
    head = open(f, 'rb').read(200)
    if head.lstrip().startswith(b'<?xml'):          # Excel 2003 XML Spreadsheet
        import xml.etree.ElementTree as ET
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        root = ET.parse(f).getroot()
        for row in root.iter('{urn:schemas-microsoft-com:office:spreadsheet}Row'):
            out = []
            for c in row.findall('ss:Cell', ns):
                idx = c.get('{urn:schemas-microsoft-com:office:spreadsheet}Index')
                if idx:
                    while len(out) < int(idx) - 1: out.append('')
                d = c.find('ss:Data', ns)
                out.append(''.join(d.itertext()).strip() if d is not None else '')
            yield out
        return
    wb = xlrd.open_workbook(f)
    for sh in wb.sheets():
        for i in range(sh.nrows):
            yield [str(c).strip() for c in sh.row_values(i)]

def rows_docx(f):
    d = docx.Document(f)
    for t in d.tables:
        for r in t.rows:
            cells, last = [], None
            for c in r.cells:            # merged cells repeat; de-dup by identity
                if c._tc is last: continue
                last = c._tc; cells.append(c.text.strip())
            yield cells

def rows_rtf(f):
    txt = rtf_to_text(open(f, encoding='latin-1').read(), errors='ignore')
    for line in txt.splitlines():
        if '|' in line:
            yield [c.strip() for c in line.split('|')]

def rows_pdf(f):
    with pdfplumber.open(f) as pdf:
        tables = [r for p in pdf.pages for t in p.extract_tables() for r in t]
        if len(tables) >= 10:
            for r in tables:
                yield [('' if c is None else str(c)).strip().replace('\n', ' ') for c in r]
            return
        # text-layout fallback: "var description Num|Char [value label]" + "value label" lines
        yield ['Variable', 'Description', 'Type', 'Value', 'Label']
        for p in pdf.pages:
            for line in (p.extract_text() or '').splitlines():
                m = re.match(r'^([a-z_][a-z0-9_]*) (.+?) (Num|Char)(?: (\S+) (.+))?$', line.strip())
                if m:
                    yield [m.group(1), m.group(2), m.group(3), m.group(4) or '', m.group(5) or '']; continue
                m = re.match(r'^(-?\d+(?:\.\d+)?) (.+)$', line.strip())
                if m: yield ['', '', '', m.group(1), m.group(2)]

READERS = {'xlsx': rows_xlsx, 'xls': rows_xls, 'docx': rows_docx, 'rtf': rows_rtf, 'pdf': rows_pdf}

def norm(h): return re.sub(r'[^a-z]', '', h.lower())

def parse(f):
    ext = f.rsplit('.', 1)[-1].lower()
    cols, out, cur = None, [], None
    for r in READERS[ext](f):
        if not any(r): continue
        n = [norm(c) for c in r]
        if any(x in ('variable', 'variablename', 'varname', 'name', 'variablecode', 'sasvariable', 'sasname') for x in n) and \
           any(x.startswith('descr') or x.startswith('defin') or x == 'label' or x == 'variablelabel' for x in n):
            cols = {}
            for i, x in enumerate(n):
                if x in ('variable', 'variablename', 'varname', 'name', 'variablecode', 'sasvariable', 'sasname') and 'var' not in cols: cols['var'] = i
                elif (x.startswith('descr') or x.startswith('defin') or x in ('variablelabel',)) and 'desc' not in cols: cols['desc'] = i
                elif x in ('type', 'format', 'datatype') and 'type' not in cols: cols['type'] = i
                elif x in ('value', 'values', 'code', 'codes') and 'val' not in cols: cols['val'] = i
                elif x in ('label', 'valuelabel', 'valuelabels', 'labels', 'formatlabel') and 'lab' not in cols: cols['lab'] = i
            if 'desc' not in cols and 'lab' in cols: cols['desc'] = cols.pop('lab')
            continue
        if not cols:
            ne = [c for c in r if c]
            if len(ne) >= 2 and re.match(r'^[a-z_][a-z0-9_]*$', ne[1]) and not re.match(r'^[a-z_][a-z0-9_]*$', ne[0]):
                cols = {'desc': r.index(ne[0]), 'var': r.index(ne[1])}
                cols['val'] = cols['var'] + 1; cols['lab'] = cols['var'] + 2
            else:
                continue
        g = lambda k: r[cols[k]] if k in cols and cols[k] < len(r) else ''
        v = g('var')
        if v and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', v):
            cur = {'variable': v, 'description': g('desc'), 'type': g('type')}
        if cur is None: continue
        out.append({**cur, 'value': g('val'), 'label': g('lab')})
    return out

def main():
    long_rows, summary = [], []
    for f in sorted([f for f in glob.glob(os.path.join(DD, '*')) if os.path.isfile(f)]):
        sid = os.path.basename(f).split('__')[0]
        try: rows = parse(f)
        except Exception as e:
            print('FAIL', sid, e, file=sys.stderr); rows = []
        nvars = len({r['variable'] for r in rows})
        summary.append({'study_id': sid, 'file': os.path.basename(f), 'n_variables_parsed': nvars})
        for r in rows: long_rows.append({'study_id': sid, **r})
    with open(os.path.join(ROOT, 'variables_long.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, ['study_id', 'variable', 'description', 'type', 'value', 'label']); w.writeheader(); w.writerows(long_rows)
    with open(os.path.join(ROOT, 'parse_summary.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, ['study_id', 'file', 'n_variables_parsed']); w.writeheader(); w.writerows(summary)
    z = [s for s in summary if s['n_variables_parsed'] == 0]
    print(len(long_rows), 'rows;', len(summary), 'files;', len(z), 'with 0 vars:', [s['study_id'] for s in z])

if __name__ == '__main__': main()
