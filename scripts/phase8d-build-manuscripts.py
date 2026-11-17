"""Generate bilingual Markdown truth and derived TeX from locked Phase8D evidence."""
from pathlib import Path
import json,csv,html,re
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';M=R/'manuscript/phase8';M.mkdir(exist_ok=True);S=json.loads((P/'phase8d-core-statistics.json').read_text());ss=S['summary']
def base(x):return x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['subsidy']==0 and x['tax']==0
baseline=[x for x in ss if base(x) and x['benchmark']=='P1' and x['cohort']=='Former-Held-Out']
ct=[x for x in S['contrasts'] if base(x) and x['benchmark']=='P1' and x['cohort']=='Former-Held-Out' and x['primary']==['TreeMLP','Sensorless','soft'] and x['reference']==['SensorlessPPO','Sensorless','tree'] and x['region']=='GLOBAL_EQUAL5' and x['metric']=='joint'][0]
figs=['fig1-architecture','fig2-p1-regimes','fig3-p2-transfer','fig4-factorial-stress','fig5-deployment-closure']
import importlib.util
spec=importlib.util.spec_from_file_location('paper_content',R/'scripts/phase8d-paper-content.py');content=importlib.util.module_from_spec(spec);spec.loader.exec_module(content);en,zh=content.build(S,R)
# Full numerical tables are generated directly, not transcribed.
with (M/'all-summary-groups.csv').open('w') as f:
 fields=['source','cohort','scheme','climate','cap','price_multiplier','subsidy','benchmark','policy','track','mode','site_years','joint','partial_profit','NUE','S_N','Native_N_loss'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for x in ss:w.writerow({k:x[k] if k in x else x['region_equal'][k] for k in fields})
with (M/'all-contrasts.json').open('w') as f:json.dump(S['contrasts'],f,indent=2)
caps_en=['Five numerical specialists, a frozen three-seed response ensemble, causal Static3-plus-anomaly adaptation, full weather × 32 residual integration and an external physical referee. No hidden referee state enters policy decisions.','P1 historical reference comparisons under matched information. Soft-Coupled, strict Tier2-Composite and archived bare relaxation are kept distinct; regional heterogeneity and nitrogen-mining indicators accompany compliance.','P2 closed-loop transfer: panel a shows all four Former/Public-by-LOYO/LORO strata; regional panels use Former only. Panel c pools closed-loop decision counts within the Former cohort, distinct from predictive-row acceptance. Anomaly OOD falls back to Static3. Acceptance does not guarantee predictive improvement.','Complete 180-cell climate-cap-price-subsidy stress surface. Black outlines mark 90 continuity cells. Heatmaps retain unfavorable cells and idealized climates are not operational forecasts.','Frozen compact model and interface, case-configuration daily mass closure, actual native simulation count and verified trajectory replay count. Repeated configuration-day records are not independent seasons.']
caps_zh=['五个数值专职模块、冻结三种子响应集成、因果Static3加异常适配、完整天气乘32残差积分以及独立物理裁判。隐藏裁判状态不进入策略。','P1历史参考下的匹配信息比较。软耦合、严格硬复合和归档仅收益回退分别报告，同时展示区域异质性和氮库消耗指标。','P2闭环迁移：a展示原留出/公开复用×LOYO/LORO全部四个分层，区域面板仅用原留出队列。c汇总该队列闭环决策计数，区别于预测行接受率。异常分布外回退Static3；接受不代表预测改善。','完整180单元气候—上限—价格—补贴压力面，黑框标示90连续性单元。不利结果保留，理想化情景不是业务天气预报。','冻结紧凑模型及接口、配置逐日守恒、实际原生模拟次数和物理缓存次数。重复配置日记录不代表独立季节。']
def esc(t):
 t=t.replace('10⁻¹¹',r'$10^{-11}$').replace('10⁻¹⁰',r'$10^{-10}$')
 for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:t=t.replace(a,b)
 return re.sub(r'\[([a-z0-9]+)\]',r'\\cite{\1}',t)
def table(zh=False):
 out=[r'\begin{longtable}{llrrr}',r'\caption{'+('历史参考条件下五区等权结果。' if zh else 'Equal-region results at the historical reference setting.')+r'}\\',r'\toprule Configuration & Track & n & Joint (\%) & Profit (EUR/ha)\\\midrule\endfirsthead',r'\toprule Configuration & Track & n & Joint (\%) & Profit (EUR/ha)\\\midrule\endhead']
 for x in baseline:
  out.append(esc(x['policy']+' '+x['mode'])+' & '+('Full' if x['track']=='Full-Telemetry' else 'Sensorless')+f" & {x['site_years']} & {100*x['region_equal']['joint']:.2f} & {x['region_equal']['partial_profit']:.2f}"+r'\\')
 out += [r'\bottomrule\end{longtable}'];result='\n'.join(out)
 if zh:result=result.replace('Configuration & Track & n & Joint', '配置 & 信息 & 年数 & 达标率').replace('Profit (EUR/ha)','部分收益 (欧元/公顷)').replace(' & Sensorless &',' & 无遥测 &').replace(' & Full &',' & 完整 &')
 return result
app_en='All Phase8B/C reports, figures and manuscript history remain archived. Phase8D uses first-pass frozen controllers and adapters with explicit CQR width amendment and adaptive benchmark reuse disclosure. Original PPO ZIP containers were unavailable; separately versioned TRAIN-only reconstructions remain unchanged. All new policy decisions are recomputed. Complete summaries, all contrasts and daily mass audits accompany the draft. No submission is authorized.'
app_zh='全部Phase8B/C报告、图表及稿件历史均已归档。Phase8D保留首轮冻结控制器和适配器，公开CQR宽度协议修订及适应性基准复用。原PPO ZIP容器未找回，已有独立版本的TRAIN重建权重保持不变。全部新策略动作重新计算。完整汇总、对比和逐日守恒证据随稿提供，未授权投稿。'
for lang,sections,caps in [('en',en,caps_en),('zh',zh,caps_zh)]:
 title='Preserving nutrient objectives during uncertain fertilizer planning' if lang=='en' else '不确定施肥规划中养分目标保持的决策效应'
 md='# '+title+'\n\n'+'\n\n'.join('## '+h+'\n\n'+t for h,t in sections);md+='\n\n## '+('Evidence and reproducibility' if lang=='en' else '证据与复现')+'\n\n'+(app_en if lang=='en' else app_zh);(M/(lang+'.md')).write_text(md)
 pre=r'''\documentclass[11pt,a4paper]{article}
\usepackage[margin=22mm]{geometry}
\usepackage{fontspec,xeCJK,graphicx,booktabs,longtable,amsmath,placeins,hyperref,natbib}
\setmainfont{Times New Roman}
\setCJKmainfont{Noto Serif CJK SC}
\hypersetup{colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue}
\setlength{\emergencystretch}{4em}
\setlength{\parskip}{5pt}
\begin{document}
'''
 tex=pre+(r'\renewcommand{\abstractname}{摘要}\renewcommand{\tablename}{表}\renewcommand{\figurename}{图}' if lang=='zh' else '')+'\\title{'+title+'}\n\\date{}\\maketitle\n'
 for idx,(h,t) in enumerate(sections):
  if idx==0:tex+='\\begin{abstract}\n'+esc(t)+'\n\\end{abstract}\n'
  else:tex+='\\section{'+h+'}\n'+esc(t)+'\n'
  if idx==2:
   tex+='\\begin{figure}[p]\\centering\\includegraphics[width=\\textwidth]{../../reports/phase8/figures/'+figs[0]+'.pdf}\\caption{'+esc(caps[0])+'}\\label{fig:1}\\end{figure}\\FloatBarrier\n'
  if idx==3:
   tex+=table(lang=='zh')+'\n'
   for j in range(1,5):tex+='\\begin{figure}[p]\\centering\\includegraphics[width=\\textwidth,height=.78\\textheight,keepaspectratio]{../../reports/phase8/figures/'+figs[j]+'.pdf}\\caption{'+esc(caps[j])+'}\\label{fig:'+str(j+1)+'}\\end{figure}\\FloatBarrier\n'
 tex+=r'\clearpage\appendix'+'\n\\section{'+('Evidence and reproducibility' if lang=='en' else '证据与复现')+'}\n'+esc(app_en if lang=='en' else app_zh)+'\n'+r'\clearpage\bibliographystyle{plainnat}\bibliography{references}\end{document}'
 (M/(lang+'.tex')).write_text(tex)
(M/'paper-bilingual-en-zh.html').write_text('<!doctype html><meta charset="utf-8"><title>Phase8D bilingual manuscript</title><style>body{max-width:1050px;margin:40px auto;font:18px/1.7 serif}section{display:grid;grid-template-columns:1fr 1fr;gap:30px}img{width:100%}</style>'+''.join('<section><div><h2>'+html.escape(a[0])+'</h2>'+''.join('<p>'+html.escape(x)+'</p>' for x in a[1].split('\n\n'))+'</div><div><h2>'+html.escape(b[0])+'</h2>'+''.join('<p>'+html.escape(x)+'</p>' for x in b[1].split('\n\n'))+'</div></section>' for a,b in zip(en,zh))+''.join('<img src="../../reports/phase8/figures/'+f+'.png">' for f in figs))
(M/'references.bib').write_text((R/'manuscript/phase7/references.bib').read_text().replace('‐','-'))
(M/'README.md').write_text('New Phase8D bilingual research draft. en.md and zh.md are prose truth; scripts/phase8d-build-manuscripts.py regenerates Markdown, derived HTML and TeX using locked statistics. Figures1–5 are regenerated from the Phase8D evidence; these are research-draft artifacts. No submission is authorized. All Phase7 files are preserved. Full tables: all-summary-groups.csv and all-contrasts.json. All exported metrics are equal-region means;site_years is per-row n. S_N=total seasonal N input minus grain N(kgN/ha);NUE=grain N/total input;total input=fertilizer+seed+wet deposition,excluding initial soil stocks. Native_N_loss=bottom leaching+denitrification(kgN/ha);partial_profit=EUR/ha excluding other farm costs.\n')
(M/'README.md').write_text((M/'README.md').read_text()+'\nFirst-pass controllers/adapters remain frozen; the CQR width amendment and retained Dev/P2 failures are explicit. Frozen PPO retains registered preprocessing, so matching information/actions does not mean every forecast summary is identical. See reports/phase8/phase8d-campaign-entrypoints.md for the loader-only recovery and completed-campaign prohibition. Storyline v3.0 defines current claims. Regeneration uses phase8d analysis/figure/manuscript scripts; compile TeX with XeLaTeX, with BibTeX for en/zh.\n')
# Report uses the same locked numerical source.
report='# Phase8D top-journal evidence report\n\n'+ '\n\n'.join('## '+h+'\n\n'+t for h,t in en[2:])+ '\n\n## Evidence\n\n- reports/phase8/phase8d-core-statistics.json\n- reports/phase8/phase8d-campaign-receipt.json\n- manuscript/phase8/all-summary-groups.csv\n- manuscript/phase8/all-contrasts.json\n\nThe Phase8B report and storyline-v1.0 are immutable archives. Figure numbering follows the current Phase8D Figures1–5 contract; previous manuscripts and figures are archived separately.\n'
report+='\n\nPhase8C publication history is preserved at `reports/phase8/phase8c-manuscript-archive/` (including the previous active report, manuscripts and figures). Cohort-separated predictive evidence: `reports/phase8/phase8d-P2-predictive-cohort-strata.json` and `.csv`.\n'
(P/'PHASE8_TOP_JOURNAL_REPORT.md').write_text(report)
(P/'PHASE8D_TOP_JOURNAL_REPORT.md').write_text(report)

(P/"figures/phase8d-captions.json").write_text(json.dumps(dict(english=caps_en,chinese=caps_zh,scope="Simulator-based adaptive benchmark reuse; P2 retrospective causal t-1;not prospective field assurance. Source cohorts/folds unpooled;intervals marginal;Holm family determined from phase8d-core-statistics.json. P2 anomaly OOD falls back to Static3, not zero total correction."),ensure_ascii=False,indent=2))
