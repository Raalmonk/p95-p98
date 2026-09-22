"""Installable inference CLI. No search, LLM, target or dataset switches."""
import argparse
import json
import os
from pathlib import Path
import shlex
import sys

def main(argv=None):
    parser=argparse.ArgumentParser(prog='p95p98',description='Run a frozen P95/P98 local protein-search controller')
    parser.add_argument('--version',action='version',version='p95p98 0.1.0')
    commands=parser.add_subparsers(dest='command',required=True)
    verify=commands.add_parser('verify',help='Verify immutable policy identities without native work')
    run=commands.add_parser('run',help='Execute one prepared structure under a finite budget')
    run.add_argument('--input',required=True,help='JSON: structure, sequence, loops, local_energy_residues, seed, input_kind')
    run.add_argument('--policy',required=True,choices=['P95','P98'])
    run.add_argument('--work-profile',required=True,help='Explicit fixed logical-cost profile JSON')
    run.add_argument('--resources',required=True,help='Verified source-excluded ProMod3 resource manifest')
    run.add_argument('--promod-python',required=True,help='Separate ProMod3 interpreter or wrapper command')
    run.add_argument('--cpu-seconds',type=float,default=1800.)
    run.add_argument('--wall-seconds',type=float,default=5400.)
    run.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):
        os.environ[name]='1'
    try:
        from .runner import policy_source, POLICY_HASHES
        if args.command=='verify':
            for name in POLICY_HASHES:policy_source(name)
            print(json.dumps(dict(status='POLICY_IDENTITIES_VERIFIED',policies=POLICY_HASHES)))
            return 0
        from .runner import run as execute
        result=execute(args.input,args.policy,args.work_profile,args.resources,
            shlex.split(args.promod_python),args.output,args.cpu_seconds,args.wall_seconds)
        print(json.dumps({k:result[k] for k in ('status','policy','geometry_valid','action_counts','physical_cpu_seconds','logical_work','wall_seconds','error')},indent=2))
        return 0 if result['status'] in ('COMPLETE','BUDGET_DELIVERY') else 2
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
