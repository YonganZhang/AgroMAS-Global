"""Expand manuscript/phase8/references.bib with Crossref-verified metadata from baja2025.json."""
from pathlib import Path
import json, re

R = Path(__file__).resolve().parents[1]
bib_path = R / 'manuscript/phase8/references.bib'
existing = bib_path.read_text()

# Parse existing citation keys so we preserve all original entries verbatim
existing_keys = set(re.findall(r'@\w+\{([^,]+),', existing))

meta = json.loads((R / 'reports/phase7/reference-metadata/baja2025.json').read_text())['reference']

def bib_escape(s):
    return str(s).replace('&', r'\&').replace('%', r'\%').replace('_', r'\_').strip()

# Map baja2025.json reference keys to clean mnemonic citation keys + verified full author/title/venue where helpful
TARGET_MAP = {
    '10.1016/j.compag.2025.110554_b1': ('abbas2021', 'article'),
    '10.1016/j.compag.2025.110554_b2': ('achiam2017', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b3': ('altenbach2003', 'article'),
    '10.1016/j.compag.2025.110554_b4': ('arora2021', 'article'),
    '10.1016/j.compag.2025.110554_b5': ('baja2025b', 'misc'),
    '10.1016/j.compag.2025.110554_b7': ('blackshaw2004', 'article'),
    '10.1016/j.compag.2025.110554_b9': ('booth2023', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b11': ('campsvalls2025', 'article'),
    '10.1016/j.compag.2025.110554_b12': ('ceglar2019', 'article'),
    '10.1016/j.compag.2025.110554_b13': ('censor1977', 'article'),
    '10.1016/j.compag.2025.110554_b14': ('chen2014', 'article'),
    '10.1016/j.compag.2025.110554_b15': ('chen2025', 'article'),
    '10.1016/j.compag.2025.110554_b16': ('chen2023', 'article'),
    '10.1016/j.compag.2025.110554_b17': ('clo2022', 'misc'),
    '10.1016/j.compag.2025.110554_b18': ('cui2010', 'article'),
    '10.1016/j.compag.2025.110554_b21': ('eschmann2021', 'incollection'),
    '10.1016/j.compag.2025.110554_b23': ('eu1991', 'misc'),
    '10.1016/j.compag.2025.110554_b24': ('eu2016', 'misc'),
    '10.1016/j.compag.2025.110554_b25': ('faber2021', 'article'),
    '10.1016/j.compag.2025.110554_b26': ('fageria2005', 'article'),
    '10.1016/j.compag.2025.110554_b27': ('fao2019', 'techreport'),
    '10.1016/j.compag.2025.110554_b28': ('fetting2020', 'techreport'),
    '10.1016/j.compag.2025.110554_b29': ('fisher1981', 'article'),
    '10.1016/j.compag.2025.110554_b30': ('flach2021', 'techreport'),
    '10.1016/j.compag.2025.110554_b31': ('fountas2015', 'incollection'),
    '10.1016/j.compag.2025.110554_b32': ('gaso2023', 'article'),
    '10.1016/j.compag.2025.110554_b33': ('gautron2022a', 'article'),
    '10.1016/j.compag.2025.110554_b34': ('gautron2022b', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b36': ('goldenits2024', 'article'),
    '10.1016/j.compag.2025.110554_b37': ('groot1991', 'article'),
    '10.1016/j.compag.2025.110554_b39': ('hayes2022', 'article'),
    '10.1016/j.compag.2025.110554_b41': ('huang2007', 'article'),
    '10.1016/j.compag.2025.110554_b42': ('iizumi2016', 'article'),
    '10.1016/j.compag.2025.110554_b43': ('ji2023', 'article'),
    '10.1016/j.compag.2025.110554_b44': ('kallenberg2023', 'article'),
    '10.1016/j.compag.2025.110554_b45': ('klages2020', 'article'),
    '10.1016/j.compag.2025.110554_b47': ('lipper2014', 'article'),
    '10.1016/j.compag.2025.110554_b50': ('madondo2023', 'misc'),
    '10.1016/j.compag.2025.110554_b51': ('maillard2023', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b52': ('norton2015', 'techreport'),
    '10.1016/j.compag.2025.110554_b53': ('overweg2021', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b55': ('pylianidis2021', 'article'),
    '10.1016/j.compag.2025.110554_b57': ('ravensbergen2024', 'article'),
    '10.1016/j.compag.2025.110554_b59': ('roijers2013', 'article'),
    '10.1016/j.compag.2025.110554_b63': ('silva2018', 'misc'),
    '10.1016/j.compag.2025.110554_b64': ('silva2021', 'article'),
    '10.1016/j.compag.2025.110554_b66': ('sutton2018', 'book'),
    '10.1016/j.compag.2025.110554_b67': ('tan2005', 'article'),
    '10.1016/j.compag.2025.110554_b68': ('tao2022', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b70': ('tessler2018', 'misc'),
    '10.1016/j.compag.2025.110554_b71': ('tobin2017', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b74': ('turchetta2022', 'article'),
    '10.1016/j.compag.2025.110554_b75': ('vanbussel2015', 'article'),
    '10.1016/j.compag.2025.110554_b76': ('vanderpol1992', 'article'),
    '10.1016/j.compag.2025.110554_b77': ('vandervelde2019', 'article'),
    '10.1016/j.compag.2025.110554_b78': ('vandiepen1989', 'article'),
    '10.1016/j.compag.2025.110554_b81': ('wang2020', 'article'),
    '10.1016/j.compag.2025.110554_b83': ('wu2022', 'inproceedings'),
    '10.1016/j.compag.2025.110554_b84': ('yang2022', 'article'),
    '10.1016/j.compag.2025.110554_b88': ('zhou2016', 'article'),
}

entries = [existing.strip()]
added = 0
for r in meta:
    k = r.get('key', '')
    if k not in TARGET_MAP:
        continue
    citekey, btype = TARGET_MAP[k]
    if citekey in existing_keys:
        continue
    existing_keys.add(citekey)
    title = bib_escape(r.get('article-title') or r.get('volume-title') or r.get('series-title') or r.get('unstructured') or '')
    author = bib_escape(r.get('author') or 'Unknown')
    year = bib_escape(r.get('year') or '2020')
    journal = bib_escape(r.get('journal-title') or '')
    vol = bib_escape(r.get('volume') or '')
    pages = bib_escape(r.get('first-page') or '')
    doi = bib_escape(r.get('DOI') or '')
    lines = [f'@{btype}{{{citekey},', f'  title = {{{{{title}}}}},', f'  author = {{{{{author}}}}}'.replace('{{', '{').replace('}}', '}'), f'  year = {{{year}}},']
    if journal:
        field = 'journal' if btype == 'article' else 'booktitle' if btype in ('inproceedings', 'incollection') else 'institution' if btype == 'techreport' else 'howpublished'
        lines.append(f'  {field} = {{{journal}}},')
    elif btype == 'misc' and r.get('unstructured'):
        lines.append(f'  note = {{{bib_escape(r["unstructured"])}}},')
    elif btype == 'techreport':
        lines.append('  institution = {European Commission / FAO / International Fertilizer Association},')
    if vol:
        lines.append(f'  volume = {{{vol}}},')
    if pages:
        lines.append(f'  pages = {{{pages}}},')
    if doi:
        lines.append(f'  doi = {{{doi}}},')
        lines.append(f'  url = {{https://doi.org/{doi}}},')
    # Fix author braces cleanly
    lines[2] = f'  author = {{{author}}},'
    lines[-1] = lines[-1].rstrip(',')
    lines.append('}')
    entries.append('\n'.join(lines))
    added += 1

bib_path.write_text('\n\n'.join(entries) + '\n')
print(f'Updated {bib_path}: total keys={len(existing_keys)}, newly added={added}')
