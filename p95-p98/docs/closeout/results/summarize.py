"""Recompute descriptive closeout tables from the shipped CSV; stdlib only."""
import csv
import json
import statistics as st
from pathlib import Path

HERE=Path(__file__).resolve().parent
rows=list(csv.DictReader((HERE/'per_input.csv').open()))
METHODS=('P95','P98','NGK')
QUALITY=('legacy_local_rmsd_A','legacy_global_rmsd_A','local_energy_REU','global_energy_REU')
COST=('logical_work_not_seconds','cpu_seconds','measured_run_cpu_seconds','incremental_run_cpu_seconds','active_wall_seconds','worker_wait_seconds')
groups={m:sorted([r for r in rows if r['method']==m],key=lambda r:int(r['input_index'])) for m in METHODS}
assert all(len(v)==48 for v in groups.values())
assert all([r['input_index'] for r in groups[m]]==[str(i) for i in range(48)] for m in METHODS)
assert all(len({groups[m][i]['episode_id'] for m in METHODS})==1 for i in range(48))
def values(rs,key): return [float(r[key]) for r in rs if r[key]!='']
def desc(xs): return dict(n=len(xs),sum=sum(xs),mean=st.mean(xs),median=st.median(xs),min=min(xs),max=max(xs)) if xs else dict(n=0)
summary={'scope':'BENCH48 development, 48 inputs, 32 homology components; derived descriptive summaries, not new fitness', 'methods':{},'ratios':{},'paired_valid_deltas_method_minus_NGK':{}}
for m,rs in groups.items():
    summary['methods'][m]={'planned':48,'returned':sum(r['endpoint_available']=='True' for r in rs),'valid':sum(r['valid']=='True' for r in rs),'full15_mp':sum(r['full15_mp']=='True' for r in rs),'whole_route_reused':sum(r['whole_route_reused']=='True' for r in rs),'metrics':{k:desc(values(rs,k)) for k in QUALITY+COST+('retained_preparation_cpu_seconds','local_rmsd_A','global_rmsd_A')}}
    if m=='NGK':continue
    summary['ratios'][m]={}
    for k in COST[:3]:
        pairs=[(float(a[k]),float(b[k])) for a,b in zip(rs,groups['NGK']) if a[k] and b[k] and float(b[k])>0]
        a,b=zip(*pairs)
        summary['ratios'][m][k]={'n':len(pairs),'sum_ratio':sum(a)/sum(b),'median_per_input_ratio':st.median(x/y for x,y in pairs),'ratio_of_medians':st.median(a)/st.median(b),'per_input_ratio_min':min(x/y for x,y in pairs),'per_input_ratio_max':max(x/y for x,y in pairs)}
    summary['paired_valid_deltas_method_minus_NGK'][m]={}
    for domain in ('WS','hard'):
        pairs=[(a,b) for a,b in zip(rs,groups['NGK']) if (a['domain']=='ws280')==(domain=='WS') and a['valid']==b['valid']=='True']
        summary['paired_valid_deltas_method_minus_NGK'][m][domain]={'n':len(pairs),**{k:st.mean(float(a[k])-float(b[k]) for a,b in pairs) for k in QUALITY}}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# BENCH48 descriptive tables','', 'All quality values in the first table are frozen raw means over all 48 returned inputs, including NGK row36 geometry-invalid output. RMSD is in Å; energy is in REU. These are not component-balanced fitness. Pooled legacy RMSD mixes W/S backbone expanded-region and hard CA loop-region definitions: use the paired subgroup changes for frozen-quality interpretation.','', '| Method | Returned/planned | Valid | MP complete | Local RMSD | Global RMSD | Local energy | Global energy | Logical work sum | Accounted route CPU (s) |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for m in METHODS:
    d=summary['methods'][m];q=d['metrics']
    lines.append(f"| {m} | {d['returned']}/48 | {d['valid']} | {d['full15_mp']} | "+' | '.join(f"{q[k]['mean']:.6f}" for k in QUALITY)+f" | {q[COST[0]]['sum']:.3f} | {q['cpu_seconds']['sum']:.3f} |")
lines+=['','| Method / cost | Sum ratio | Median input ratio | Ratio of medians | Paired n |','|---|---:|---:|---:|---:|']
for m in METHODS[:2]:
    for k in COST[:2]:
        r=summary['ratios'][m][k]
        lines.append(f"| {m} / {k} | {r['sum_ratio']:.6%} | {r['median_per_input_ratio']:.6%} | {r['ratio_of_medians']:.6%} | {r['n']} |")
lines+=['','Paired valid raw mean changes below are method minus NGK; negative is better. The invalid NGK hard input remains in the main 48-input table above.','','| Method | Group | Both-valid n / planned | Δ local RMSD | Δ global RMSD | Δ local energy | Δ global energy |','|---|---|---:|---:|---:|---:|---:|']
for m in METHODS[:2]:
    for group,d in summary['paired_valid_deltas_method_minus_NGK'][m].items():
        lines.append(f"| {m} | {group} | {d['n']}/{32 if group=='WS' else 16} | "+' | '.join(f'{d[k]:.6f}' for k in QUALITY)+' |')
lines+=['','Existing common scaffold-fit CA display metrics and fixed-energy medians; all available outputs including the NGK invalid output, n=48 per cell. These CA values are derived figure metrics, not the frozen fitness.','','| Method | Local CA RMSD median (Å) | Global CA RMSD median (Å) | Local energy median (REU) | Global energy median (REU) |','|---|---:|---:|---:|---:|']
for m in METHODS:
    d=summary['methods'][m]['metrics']
    lines.append('| '+m+' | '+' | '.join(f"{d[k]['median']:.6f}" for k in ('local_rmsd_A','global_rmsd_A','local_energy_REU','global_energy_REU'))+' |')
(HERE/'TABLES.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
