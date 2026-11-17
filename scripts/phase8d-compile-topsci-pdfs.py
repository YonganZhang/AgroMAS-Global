"""Compile updated Top-SCI bilingual Markdown manuscripts and supplementary materials into PDFs."""
from pathlib import Path
import csv
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
M_DIR = ROOT / 'manuscript/phase8'
CAP_DIR = ROOT / 'reports/phase8/figures/captions-v12'
FIG_DIR = ROOT / 'reports/phase8/figures'

MAIN_FIG_MAP = {
    'm22-intro': ('fig1-architecture.pdf', 'fig1.txt', 'fig:1'),
    'r31-p3': ('fig2-g1.pdf', 'fig2.txt', 'fig:2'),
    'tbl-2': ('fig2-p1-regimes.pdf', 'fig3.txt', 'fig:3'),
    'r35-p2': ('fig3-p2-transfer.pdf', 'fig4.txt', 'fig:4'),
    's42-p1': ('fig4-factorial-stress.pdf', 'fig5.txt', 'fig:5'),
}

SUPP_FIGS = [
    ('figs2-g3-subsidy.pdf', 'figs1.txt', 'fig:S1'),
    ('fig5-deployment-closure.pdf', 'figs2.txt', 'fig:S2'),
    ('figs3-price-subsidy.pdf', 'figs3.txt', 'fig:S3'),
    ('figs4-policy-scorecard.pdf', 'figs4.txt', 'fig:S4'),
    ('figs5-p1-all-regimes.pdf', 'figs5.txt', 'fig:S5'),
    ('figs6-p2-admission-mse.pdf', 'figs6.txt', 'fig:S6'),
    ('figs7-stress-180cell-grid.pdf', 'figs7.txt', 'fig:S7'),
    ('figs8-closure-readout-audit.pdf', 'figs8.txt', 'fig:S8'),
]

AUTHOR_BLOCK_EN = (
    r'\author{'
    r'Yongan Zhang$^{a,b,c}$, Zhiling Guo$^{a,b,*}$\\'
    r'\footnotesize $^{a}$State Key Laboratory of Climate Resilience for Coastal Cities, '
    r'Department of Building Environment and Energy Engineering,\\'
    r'\footnotesize The Hong Kong Polytechnic University, Hong Kong SAR, China\\'
    r'\footnotesize $^{b}$International Centre of Urban Energy Nexus, '
    r'The Hong Kong Polytechnic University, Hong Kong SAR, China\\'
    r'\footnotesize $^{c}$Zhejiang Key Laboratory of Industrial Intelligence and Digital Twin, '
    r'Eastern Institute of Technology, Ningbo, China\\'
    r'\footnotesize First author: zhangyongan.polyu@arctura-labs.com; '
    r'$^{*}$Corresponding author: guozhiling.polyu@arctura-labs.com'
    r'}'
)

AUTHOR_BLOCK_ZH = (
    r'\author{'
    r'张永安$^{a,b,c}$，郭直灵$^{a,b,*}$\\'
    r'\footnotesize $^{a}$香港理工大学 建筑环境与能源工程学系 沿海城市气候韧性国家重点实验室，中国香港\\'
    r'\footnotesize $^{b}$香港理工大学 国际城市能源枢纽中心，中国香港\\'
    r'\footnotesize $^{c}$宁波东方理工大学 浙江省工业智能与数字孪生重点实验室，浙江宁波\\'
    r'\footnotesize 第一作者：zhangyongan.polyu@arctura-labs.com；'
    r'$^{*}$通讯作者：guozhiling.polyu@arctura-labs.com'
    r'}'
)


def parse_blocks(md_path: Path):
    """Parse id-tagged blocks from generated Markdown manuscripts."""
    raw = md_path.read_text()
    pattern = re.compile(r'<!-- id:([^\s]+) -->\n(.*?)(?=\n<!-- id:|\Z)', re.S)
    out = []
    for bid, body in pattern.findall(raw):
        lines = [ln for ln in body.strip().splitlines() if not ln.startswith('@fig ')]
        out.append((bid, '\n'.join(lines).strip()))
    return out


def escape_plain_text(txt: str) -> str:
    """Escape LaTeX special characters in plain prose outside math/citations."""
    txt = txt.replace('\\', r'\textbackslash{}')
    for ch in ['&', '%', '#', '_', '{', '}']:
        txt = txt.replace(ch, '\\' + ch)
    return txt


def md_to_latex_inline(text: str) -> str:
    """Convert inline math, display math, and bracketed citation groups to LaTeX."""
    tokens = []

    def stash(m):
        tokens.append(m.group(0))
        return f'@@TOK{len(tokens) - 1}@@'

    # Stash $$...$$ and $...$ first
    s = re.sub(r'\$\$.*?\$\$', stash, text, flags=re.S)
    s = re.sub(r'\$[^$]+\$', stash, s)

    # Stash URLs before escaping special chars
    url_tokens = []

    def stash_url(m):
        url_tokens.append(f'\\url{{{m.group(0)}}}')
        return f'@@URL{len(url_tokens) - 1}@@'

    s = re.sub(r'https?://[^\s\)\],。，；]+', stash_url, s)

    # Convert citation groups [k1, k2] to ~\citep{k1,k2}
    cite_tokens = []

    def stash_cite(m):
        keys = ','.join(k.strip() for k in m.group(1).split(','))
        # Avoid leading extra space before ~\citep
        cite_tokens.append(f'~\\citep{{{keys}}}')
        return f'@@CITE{len(cite_tokens) - 1}@@'

    s = re.sub(r'\s*\[([A-Za-z][\w-]*(?:,\s*[A-Za-z][\w-]*)*)\]', stash_cite, s)
    s = escape_plain_text(s)

    for idx, c in enumerate(cite_tokens):
        s = s.replace(f'@@CITE{idx}@@', c)
    for idx, u in enumerate(url_tokens):
        s = s.replace(f'@@URL{idx}@@', u)
    for idx, t in enumerate(tokens):
        s = s.replace(f'@@TOK{idx}@@', t)
    return s


def read_caption(cap_file: str, lang: str) -> str:
    """Read bilingual caption file (line 0 = EN, line 1 = ZH) and convert to LaTeX."""
    lines = [ln.strip() for ln in (CAP_DIR / cap_file).read_text().splitlines() if ln.strip()]
    raw = lines[0] if lang == 'en' else lines[1]
    return md_to_latex_inline(raw)


def format_table(tbl_md: str, bid: str, lang: str) -> str:
    """Convert Markdown pipe table + title line into a clean booktabs tabularx block."""
    lines = [ln.strip() for ln in tbl_md.splitlines() if ln.strip()]
    title_raw = lines[0]
    if lang == 'en':
        title_clean = re.sub(r'^Table\s+\d+\s*', '', title_raw)
    else:
        title_clean = re.sub(r'^表\s*\d+\s*', '', title_raw)
    caption = md_to_latex_inline(title_clean)
    rows = [ln.strip('|').split('|') for ln in lines[1:]]
    header = [c.strip() for c in rows[0]]
    align = [c.strip() for c in rows[1]]
    body = [[c.strip() for c in r] for r in rows[2:]]
    ncols = len(header)

    # Column widths tuned for crisp zero-overflow layout
    R_P1 = r'>{\raggedleft\arraybackslash}p{1.25cm}'
    R_P2 = r'>{\raggedleft\arraybackslash}p{1.65cm}'
    if bid == 'tbl-1':
        colspec = (
            r'l >{\raggedright\arraybackslash}p{2.3cm} >{\raggedright\arraybackslash}p{3.2cm} '
            + r'>{\raggedleft\arraybackslash}p{0.9cm} ' + R_P1 + ' ' + R_P1 + ' ' + R_P1
            + r' >{\raggedright\arraybackslash}X'
        )
    elif bid == 'tbl-2':
        colspec = (
            r'>{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}p{1.8cm} '
            + ' '.join([R_P2] * 5)
        )
    else:  # tbl-3
        colspec = (
            r'>{\raggedright\arraybackslash}p{2.1cm} >{\raggedright\arraybackslash}p{2.6cm} '
            r'>{\raggedright\arraybackslash}p{2.3cm} >{\raggedleft\arraybackslash}p{1.2cm} '
            r'>{\raggedleft\arraybackslash}p{1.2cm} >{\raggedright\arraybackslash}X'
        )

    tab_idx = bid.split('-')[-1]
    out = [
        r'\begin{table}[htbp]',
        r'\centering',
        r'\scriptsize',
        r'\setlength{\tabcolsep}{3.5pt}',
        f'\\caption{{{caption}}}\\label{{tab:{tab_idx}}}',
        f'\\begin{{tabularx}}{{\\textwidth}}{{{colspec}}}',
        r'\toprule',
        ' & '.join(md_to_latex_inline(h) for h in header) + r' \\',
        r'\midrule',
    ]
    for r in body:
        assert len(r) == ncols, (bid, r)
        out.append(' & '.join(md_to_latex_inline(c) for c in r) + r' \\')
    out.extend([r'\bottomrule', r'\end{tabularx}', r'\end{table}', r'\FloatBarrier'])
    return '\n'.join(out)


def format_figure(fig_pdf: str, cap_txt: str, label: str, lang: str) -> str:
    """Create a full-width cleanly floated figure block."""
    cap = read_caption(cap_txt, lang)
    return (
        f'\\begin{{figure}}[htbp]\n'
        f'\\centering\n'
        f'\\includegraphics[width=\\textwidth,height=.76\\textheight,keepaspectratio]'
        f'{{../../reports/phase8/figures/{fig_pdf}}}\n'
        f'\\caption{{{cap}}}\\label{{{label}}}\n'
        f'\\end{{figure}}\\FloatBarrier'
    )


def strip_heading_num(title: str) -> str:
    """Strip manual '1 ', '2.2.1 ', '附录 ' prefixes so LaTeX numbering stays clean."""
    title = re.sub(r'^\d+(?:\.\d+)*\s+', '', title)
    title = re.sub(r'^Appendix\s+', '', title)
    title = re.sub(r'^附录\s+', '', title)
    return md_to_latex_inline(title)


def build_main_tex(lang: str) -> str:
    """Generate en.tex or zh.tex directly from the updated Markdown manuscripts."""
    blocks = parse_blocks(M_DIR / f'{lang}.md')
    lines = [
        r'\documentclass[11pt,a4paper]{article}',
        r'\usepackage[margin=22mm]{geometry}',
        r'\usepackage{fontspec,xeCJK,graphicx,booktabs,tabularx,array,amsmath,amssymb,placeins,hyperref}',
        r'\usepackage[numbers,sort&compress]{natbib}',
        r'\setmainfont{Times New Roman}',
        r'\setCJKmainfont{Noto Serif CJK SC}',
        r'\hypersetup{colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue}',
        r'\setlength{\emergencystretch}{4em}',
        r'\setlength{\parskip}{5pt}',
        r'\begin{document}',
    ]
    if lang == 'zh':
        lines.append(
            r'\renewcommand{\abstractname}{摘要}'
            r'\renewcommand{\tablename}{表}'
            r'\renewcommand{\figurename}{图}'
            r'\renewcommand{\refname}{参考文献}'
            r'\renewcommand{\appendixname}{附录}'
        )

    title_raw = next(b for bid, b in blocks if bid == 'title').lstrip('# ').strip()
    lines.append(f'\\title{{{md_to_latex_inline(title_raw)}}}')
    lines.append(AUTHOR_BLOCK_EN if lang == 'en' else AUTHOR_BLOCK_ZH)
    lines.append(r'\date{}')
    lines.append(r'\maketitle')

    in_abstract = False
    in_appendix = False
    for bid, body in blocks:
        if bid in ('title', 'sec-abs'):
            if bid == 'sec-abs':
                lines.append(r'\begin{abstract}')
                in_abstract = True
            continue
        if in_abstract and bid == 'abs-body':
            for para in body.split('\n\n'):
                lines.append(md_to_latex_inline(para))
            lines.append(r'\end{abstract}')
            in_abstract = False
            continue
        if bid == 'sec-app':
            lines.append(r'\FloatBarrier\clearpage\appendix')
            in_appendix = True
        if body.startswith('## '):
            lines.append(r'\FloatBarrier')
            lines.append(f'\\section{{{strip_heading_num(body[3:].strip())}}}')
        elif body.startswith('### '):
            lines.append(f'\\subsection{{{strip_heading_num(body[4:].strip())}}}')
        elif body.startswith('#### '):
            lines.append(f'\\subsubsection{{{strip_heading_num(body[5:].strip())}}}')
        elif bid.startswith('tbl-'):
            lines.append(format_table(body, bid, lang))
        elif body.startswith('$$') and body.endswith('$$'):
            inner = body[2:-2].strip()
            if bid == 'm221-eq' and ', \\qquad ' in inner:
                parts = [p.strip() for p in inner.split(', \\qquad ')]
                aligned_body = ' \\\\\n'.join(f'&{p}' for p in parts)
                lines.append(f'\\begin{{equation}}\n\\begin{{aligned}}\n{aligned_body}\n\\end{{aligned}}\n\\end{{equation}}')
            else:
                lines.append(f'\\begin{{equation}}\n{inner}\n\\end{{equation}}')
        else:
            lines.append(md_to_latex_inline(body))

        if bid in MAIN_FIG_MAP:
            fig_pdf, cap_txt, label = MAIN_FIG_MAP[bid]
            lines.append(format_figure(fig_pdf, cap_txt, label, lang))

    if in_appendix:
        if lang == 'en':
            lines.append(
                'The accompanying Supplement provides all eight high-resolution supplementary figures '
                '(Supplementary Figs.~S1 to S8), complete 367-group equality-weighted performance tables '
                'across cohorts and validation schemes, full-family Holm inference records, and frozen '
                'physical-state decoding bounds. Open-source control software, configuration specifications, '
                'and reproducible analysis scripts are archived publicly at '
                '\\url{https://github.com/YonganZhang/AgroMAS-Global}.'
            )
        else:
            lines.append(
                '配套《补充材料》（Supplement）完整收录附图S1至S8高清矢量图版、跨越各测试队列与验证划分的'
                '全部367组五区等权绩效明细表、全家族Holm校正检验日志及物理隐状态解码完整边界。'
                '全套开源控制源码与可复现绘图脚本已公开托管于'
                '\\url{https://github.com/YonganZhang/AgroMAS-Global}。'
            )

    lines.append(r'\FloatBarrier\clearpage\bibliographystyle{unsrtnat}\bibliography{references}\end{document}')
    return '\n\n'.join(lines) + '\n'


def build_supplement_tex() -> str:
    """Generate supplement.tex with Supplementary Figs. S1-S8 and full 367 summary groups."""
    lines = [
        r'\documentclass[10pt,a4paper]{article}',
        r'\usepackage[margin=18mm]{geometry}',
        r'\usepackage{fontspec,graphicx,longtable,booktabs,pdflscape,placeins,amsmath,hyperref}',
        r'\setmainfont{Times New Roman}',
        r'\setlength{\emergencystretch}{4em}',
        r'\setlength{\parskip}{4pt}',
        r'\renewcommand{\figurename}{Supplementary Fig.}',
        r'\renewcommand{\thefigure}{S\arabic{figure}}',
        r'\renewcommand{\tablename}{Supplementary Table}',
        r'\renewcommand{\thetable}{S\arabic{table}}',
        r'\begin{document}',
        r'\title{Supplementary Material for: Coupling climate, watershed, market and satellite priors for wheat nitrogen management}',
        AUTHOR_BLOCK_EN,
        r'\date{}',
        r'\maketitle',
        r'\section{Supplementary Figures}',
        (
            r'Supplementary Figures~S1 to S8 expand the experimental diagnostics reported in the main manuscript, '
            r'covering counterfactual warming-cap ablations (Fig.~S1), 349-day organic-mineral nitrogen pool '
            r'balances (Fig.~S2), fertilizer price-shock and green-subsidy sensitivity trajectories (Fig.~S3), '
            r'nine-policy bootstrap scorecards (Fig.~S4), 32-year apparent efficiency distributions (Fig.~S5), '
            r'cross-regional satellite admission versus prediction error matrices (Fig.~S6), the complete 180-cell '
            r'factorial advantage surface (Fig.~S7), and 50-cell out-of-fold physical state decoding paired with '
            r'daily carbon-nitrogen mass conservation checks across 6,104,146 state transitions (Fig.~S8).'
        ),
    ]

    for fig_pdf, cap_txt, label in SUPP_FIGS:
        cap = read_caption(cap_txt, 'en')
        lines.append(
            f'\\begin{{figure}}[p]\n'
            f'\\centering\n'
            f'\\includegraphics[width=\\textwidth,height=.82\\textheight,keepaspectratio]'
            f'{{../../reports/phase8/figures/{fig_pdf}}}\n'
            f'\\caption{{{cap}}}\\label{{{label}}}\n'
            f'\\end{{figure}}\\FloatBarrier'
        )

    lines.extend([
        r'\clearpage\section{Complete Experimental Summary Groups}',
        (
            r'Supplementary Table~S1 records equal-region joint compliance, partial profit, apparent '
            r'nitrogen use efficiency ($\mathrm{NUE}_{\mathrm{app}}$), and nitrogen surplus ($S_N$) across all '
            r'evaluated cohorts, transfer schemes, climate scenarios, surplus caps, price multipliers, '
            r'and subsidy levels after within-farm-year seed averaging. Sources (\texttt{NASA}, \texttt{WUR}), '
            r'cohorts (\texttt{Former-Held-Out}, \texttt{Public-Reused}), and cross-validation schemes '
            r'(\texttt{LOYO}, \texttt{LORO}) are kept strictly unpooled.'
        ),
        r'\begin{landscape}\scriptsize\begin{longtable}{llllllllrrrrr}',
        r'\caption{Complete equal-region benchmark summary across all 367 experimental configurations.}\\',
        r'\toprule Source/cohort & Scheme & Climate & Cap & Price & Sub & Policy & Mode/track & $n$ & Joint (\%) & Profit & NUE & $S_N$ \\\midrule\endfirsthead',
        r'\toprule Source/cohort & Scheme & Climate & Cap & Price & Sub & Policy & Mode/track & $n$ & Joint (\%) & Profit & NUE & $S_N$ \\\midrule\endhead',
        r'\bottomrule\end{longtable}\end{landscape}',
    ])

    table_rows = []
    with (M_DIR / 'all-summary-groups.csv').open() as fh:
        for row in csv.DictReader(fh):
            cohort_short = {'Former-Held-Out': 'Former', 'Public-Reused': 'Public', 'Public-WUR': 'Pub-WUR'}.get(row['cohort'], row['cohort'])
            track_short = 'SL' if row['track'] == 'Sensorless' else 'Full'
            src_co = escape_plain_text(f"{row['source']}/{cohort_short}")
            scheme = escape_plain_text(row['scheme'])
            clim = escape_plain_text({'Historical': 'Hist', 'idealized_mid': 'Warm+1.8C', 'idealized_high': 'Warm+3.5C'}.get(row['climate'], row['climate']))
            cap = f"{int(float(row['cap']))}"
            price = f"{float(row['price_multiplier']):.1f}"
            sub = f"{int(float(row['subsidy']))}"
            pol = escape_plain_text(row['policy'])
            mt = escape_plain_text(f"{row['mode']}/{track_short}")
            sy = row['site_years']
            jnt = f"{100 * float(row['joint']):.2f}"
            prof = f"{float(row['partial_profit']):.2f}"
            nue = f"{float(row['NUE']):.2f}"
            sn = f"{float(row['S_N']):.1f}"
            table_rows.append(f'{src_co} & {scheme} & {clim} & {cap} & {price} & {sub} & {pol} & {mt} & {sy} & {jnt} & {prof} & {nue} & {sn} \\\\')

    # Splice rows before \bottomrule
    idx = lines.index(r'\bottomrule\end{longtable}\end{landscape}')
    lines[idx:idx] = table_rows

    lines.extend([
        r'\clearpage\section{Statistical Protocol and Retained Calibration Boundaries}',
        (
            r'All 13,512 pairwise benchmark contrasts are retained in \texttt{all-contrasts.json} with sample '
            r'counts, tie counts, two-sided exact sign-test probabilities, marginal paired bootstrap confidence '
            r'intervals, and unified family-wide Holm-adjusted probabilities. Random seeds are averaged within '
            r'each farm-year before paired statistical inference, and regional averages apply equal five-archetype '
            r'weights across Perth, Wichita, Lelystad, Beauce, and Luancheng.'
        ),
        (
            r'Two retained negative/boundary diagnostics are preserved without post-hoc tuning. First, on the '
            r'cross-continental leave-one-region-out (LORO) holdout under frozen first-pass causal linear adapters, '
            r'prior gate admission rises from zero to 60.00\% world-equal (72.02\% of prediction rows), yet '
            r'world-equal grain nitrogen mean squared error remains at 517.65 versus 505.15 $\mathrm{kg}^2\,\mathrm{ha}^{-2}$ '
            r'for static hydraulic soil priors alone, establishing that out-of-distribution admission does not replace '
            r'local soil calibration. Second, marginal 90\% conformal coverage (90.78\% Full-Telemetry, 90.37\% Sensorless) '
            r'coexists with regional undercoverage in semi-arid Perth (75.19\% Full-Telemetry) and requires region-conditional '
            r'recalibration prior to dryland field rollout.'
        ),
        r'\end{document}',
    ])
    return '\n\n'.join(lines) + '\n'


def compile_doc(stem: str, use_bibtex: bool = True):
    """Run xelatex + optional bibtex + xelatex x2 inside manuscript/phase8."""
    cmd = ['xelatex', '-interaction=nonstopmode', '-halt-on-error', f'{stem}.tex']
    subprocess.run(cmd, cwd=M_DIR, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if use_bibtex:
        subprocess.run(['bibtex', stem], cwd=M_DIR, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run(cmd, cwd=M_DIR, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.run(cmd, cwd=M_DIR, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log_txt = (M_DIR / f'{stem}.log').read_text(errors='replace')
    overfull = [ln for ln in log_txt.splitlines() if 'Overfull \\hbox' in ln]
    missing_ch = [ln for ln in log_txt.splitlines() if 'Missing character:' in ln]
    undef = [ln for ln in log_txt.splitlines() if 'There were undefined' in ln or 'Citation `' in ln and 'undefined' in ln]
    pdfinfo = subprocess.check_output(['pdfinfo', str(M_DIR / f'{stem}.pdf')], text=True)
    pages = next((ln.split(':')[1].strip() for ln in pdfinfo.splitlines() if ln.startswith('Pages:')), '?')
    return {
        'pdf': f'manuscript/phase8/{stem}.pdf',
        'pages': pages,
        'overfull_hbox': len(overfull),
        'missing_char': len(missing_ch),
        'undefined_warnings': len(undef),
    }


def main():
    (M_DIR / 'en.tex').write_text(build_main_tex('en'))
    (M_DIR / 'zh.tex').write_text(build_main_tex('zh'))
    (M_DIR / 'supplement.tex').write_text(build_supplement_tex())

    report = {
        'en': compile_doc('en', use_bibtex=True),
        'zh': compile_doc('zh', use_bibtex=True),
        'supplement': compile_doc('supplement', use_bibtex=False),
    }
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
