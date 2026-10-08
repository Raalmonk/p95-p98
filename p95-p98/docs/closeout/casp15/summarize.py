"""Verify retained joins and summarize CASP15 scalars; no native/model calls.

Run with Python 3 from any directory. Prints Markdown; --json prints JSON.
This checks published extraction consistency, not independent experiment replay.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, statistics
HERE=Path(__file__).resolve().parent
METHODS=('P95','P98','native_NGK','short_NGK')
TARGETS={'T1104','T1109','T1123','T1139','T1187','T1194'}
MODELS=('AlphaFold2','ESMFold')
def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1.1e-6)
def summarize():
    payload=(HERE/'results_per_input.csv').read_bytes()
    rows=list(csv.DictReader(payload.decode().splitlines()))
    evidence=json.loads((HERE/'mc_control_evidence.json').read_text())
    counts=list(csv.DictReader((HERE/'mc_control_counts.csv').open()))
    assert hashlib.sha256(payload).hexdigest()==evidence['results_csv_sha256']
    assert len(rows)==48 and len(evidence['records'])==24 and len(counts)==24
    assert {(r['target'],r['start_model'],r['method']) for r in rows}=={
        (t,s,m) for t in TARGETS for s in MODELS for m in METHODS}
    assert all(r['status']=='COMPLETE' and r['geometry_valid']=='true' for r in rows)
    by_index={int(r['index']):r for r in rows};by_count={int(r['index']):r for r in counts}
    assert len(by_index)==48 and len(by_count)==24
    package=HERE.parents[2]
    for name,expected in evidence['policies'].items():
        assert hashlib.sha256((package/f'src/p95p98/policies/{name.lower()}.py').read_bytes()).hexdigest()==expected
    for e in evidence['records']:
        r=by_index[e['index']];c=by_count[e['index']]
        assert (e['target'],e['start_model'],e['method'])==(r['target'],r['start_model'],r['method'])
        assert e['policy_sha256']==evidence['policies'][e['method']]
        assert e['action_counts']==json.loads(r['action_counts'])
        assert e['action_counts'].get('promod3_database',0)==int(c['database_calls'])==0
        assert close(e['method_cpu_seconds'],r['method_cpu_seconds'])
        assert close(e['method_cpu_seconds'],c['method_cpu_seconds'])
        assert e['terminal_sha256']==c['terminal_sha256']
        native=e['refinement_actions'][0]['native_counts']
        for k in ('kic','repack','minimize','mc_trials','mc_accepts','controller','observation_score_calls','safe_stop'):
            assert native.get(k,0)==int(c[k])
    output=[]
    for model in (*MODELS,'All'):
        selected=[r for r in rows if model=='All' or r['start_model']==model]
        source={}
        for r in selected:
            key=(r['target'],r['start_model'])
            values=tuple(float(r[k]) for k in ['source_local_bb_rmsd_A','source_global_ca_rmsd_A','source_local_energy_REU','source_global_energy_REU'])
            if key in source:assert source[key]==values
            source[key]=values
        ngk=sum(float(r['method_cpu_seconds']) for r in selected if r['method']=='native_NGK')
        group=dict(start_model=model,independent_targets=len({r['target'] for r in selected}),
            source_inputs=len(source),source_mean_local_bb_rmsd_A=statistics.mean(x[0] for x in source.values()),methods=[])
        for method in METHODS:
            subset=[r for r in selected if r['method']==method]
            q=dict(method=method,n=len(subset))
            for k in ['method_cpu_seconds','local_bb_rmsd_A','global_ca_rmsd_A','local_energy_REU','global_energy_REU']:
                q['mean_'+k]=statistics.mean(float(r[k]) for r in subset)
            q['cpu_ratio_native']=sum(float(r['method_cpu_seconds']) for r in subset)/ngk
            q['mean_delta_source_local_bb_rmsd_A']=statistics.mean(float(r['local_bb_rmsd_A'])-float(r['source_local_bb_rmsd_A']) for r in subset)
            group['methods'].append(q)
        output.append(group)
    return dict(status='RETAINED_SCALARS_AND_CONTROL_COUNTS_VERIFIED',
        source_csv_sha256=hashlib.sha256(payload).hexdigest(),groups=output,
        policy_records=24,database_calls=0,counts=counts)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',action='store_true');args=p.parse_args()
    data=summarize()
    if args.json:print(json.dumps(data,indent=2,allow_nan=False));return
    print('# CASP15 retained results\n\n'+data['status']+'\n')
    print('| Start | Method | n | Mean CPU (s) | CPU/native | Local BB RMSD (Å) | Δsource (Å) |')
    print('|---|---|---:|---:|---:|---:|---:|')
    for g in data['groups']:
        print(f"| {g['start_model']} | Unprocessed source | {g['source_inputs']} | — | — | {g['source_mean_local_bb_rmsd_A']:.6f} | 0 |")
        for m in g['methods']:
            print(f"| {g['start_model']} | {m['method']} | {m['n']} | {m['mean_method_cpu_seconds']:.6f} | {100*m['cpu_ratio_native']:.4f}% | {m['mean_local_bb_rmsd_A']:.6f} | {m['mean_delta_source_local_bb_rmsd_A']:+.6f} |")
    print('\nNo database actions in 24 policy runs. Counter totals are separate from sparse callback samples.')
    print('\n| P98 start | Target | KIC attempts | Safe stops |')
    print('|---|---|---:|---:|')
    for c in data['counts']:
        if c['method']=='P98':print(f"| {c['start_model']} | {c['target']} | {c['kic']} | {c['safe_stop']} |")
if __name__=='__main__':main()
