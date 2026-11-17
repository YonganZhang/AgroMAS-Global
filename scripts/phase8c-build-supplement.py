from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];M=R/'manuscript/phase8';S=json.loads((R/'reports/phase8/phase8c-core-statistics.json').read_text())
t=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}\usepackage{fontspec,graphicx,longtable,booktabs,pdflscape,placeins}\setmainfont{Times New Roman}\setlength{\emergencystretch}{4em}
\begin{document}\title{Supplementary evidence for nutrient-objective preservation}\date{}\maketitle
\section{Forecast and controller diagnostics}
Forecast metrics are distinct from policy compliance. Pooled physical decoding does not establish a causal mechanism. Within-region native nitrogen-loss decoding is weak positive in Australia and negative elsewhere. Climate removal uses a smaller cohort, so raw group means are not a matched causal effect. All intervals are marginal and all source cohorts and validation folds remain separate.
'''
for f,c in [('fig2-g1','Frozen forecast skill, uncertainty coverage and physical-variable decoding.'),('figs2-g3-subsidy','Model, solver, specialist-removal and experimental-subsidy diagnostics. Unequal cohort sizes are labelled.')]:t+='\\begin{figure}[p]\\centering\\includegraphics[width=\\textwidth]{../../reports/phase8/figures/'+f+'.pdf}\\caption{'+c+'}\\end{figure}\\FloatBarrier\n'
t+=r'\clearpage\section{Complete summary groups}\begin{landscape}\scriptsize\begin{longtable}{llllllllrrr}\toprule Source/cohort & Fold & Climate & Cap & Price & Subsidy & Policy & Mode/track & Years & Joint(\%) & Profit\\\midrule\endhead'+'\n'
for x in S['summary']:
 vals=[x['source']+'/'+x['cohort'].replace('Former-Held-Out','Former').replace('Public-Reused','Public'),x['scheme'],x['climate'].replace('idealized_',''),str(int(x['cap'])),str(x['price_multiplier']),str(int(x['subsidy'])),x['policy'],x['mode']+'/'+('Full' if x['track']=='Full-Telemetry' else 'SL'),str(x['site_years']),f"{100*x['region_equal']['joint']:.2f}",f"{x['region_equal']['partial_profit']:.2f}"]
 t+=' & '.join(v.replace('_',r'\_').replace('%',r'\%') for v in vals)+r'\\'+'\n'
t+=r'\bottomrule\end{longtable}\end{landscape}\clearpage\section{Statistics and reproducibility}\normalsize'
t+=' All 13,512 contrasts, their sample sizes, ties, exact probabilities, marginal 95 percent intervals and Holm-adjusted sign-test probabilities are retained in the accompanying machine-readable supplement. The unit is farm-year after seed averaging. Equal-region intervals resample paired years within regions. Exact tests retain pooled paired farm-year signs or ranks. Configuration-day conservation counts include shared trajectories. Three reconstructed PPO checkpoints are separately versioned, and all 198 archived baseline PPO episodes have identical decisions and outcomes. This is not recovery of the original ZIP containers. No original result was overwritten.'
t+=r'\end{document}';(M/'supplement.tex').write_text(t)
