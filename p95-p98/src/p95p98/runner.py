"""Portable deployment of the evaluated Router, native moves and P95/P98 code.

Adapted from routing/production_runner.py; dataset bindings and evaluation are
replaced by explicit user inputs. Policy logic and source-only schemas are not
rewritten. This entry point never loads a target structure or a search optimizer.
"""
import copy
from dataclasses import replace
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import sys
import time
from .controller import Capability, OperationResult, Router, State, digest
from .io import read, sha, write
from .inputs import load_input
from .ngk_budget import CooperativeStop
from .policy_client import RoutingPolicyClient
from .process import bounded_call
from .production_state import restore_state_pose
from .work_profile import load_work_profile, native_prices, reserve_observation

POLICY_HASHES = {'P95':'6c2330e612f4c2000d9965bd45d666c3ca26a74473b994b5ba4c513a06bb5ed8',
                 'P98':'533a5549d5d8722f0ea43ce418c009a589c288696d906e4dd5e386945fd0fd83'}

def policy_source(name):
    path = Path(__file__).parent/'policies'/(name.lower()+'.py')
    if name not in POLICY_HASHES or sha(path)!=POLICY_HASHES[name]:
        raise ValueError('Frozen policy identity check failed')
    return path.read_text()

def cpu_now():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime

def implementation_identity():
    root = Path(__file__).parent
    return digest({str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
                   if p.is_file() and p.suffix in ('.py', '.json', '.cpp')})

def command_identity(command):
    if not command or any(not isinstance(x,str) for x in command):
        raise ValueError('Explicit ProMod command is required')
    executable = shutil.which(command[0])
    if executable is None:
        raise ValueError('ProMod executable is unavailable: '+command[0])
    files = {str(Path(executable).resolve()): sha(Path(executable).resolve())}
    for argument in command[1:]:
        if Path(argument).is_file():
            files[str(Path(argument).resolve())] = sha(argument)
    return dict(argv=list(command), executable_files=files)

def chemistry_check(source, pose):
    """Only recognized candidate incompatibilities are scientific rejections."""
    started=time.process_time()
    try:
        changes=source.compatible(pose)
    except ValueError as exc:
        known = {'Candidate residue count differs', 'Candidate topology differs from frozen source',
                 'Candidate sequence differs from frozen source', 'Candidate fold_tree differs from frozen source',
                 'Candidate residue identity differs', 'Candidate atom/chain mapping differs',
                 'Tautomer exchanged atom must be hydrogen', 'Tautomer common atom elements differ',
                 'Candidate constraints differ from source',
                 'Candidate chemical connections or variants differ from source'}
        if str(exc) not in known:
            raise
        return dict(status='INCOMPATIBLE',reason=str(exc),cpu_seconds=time.process_time()-started)
    return dict(status='COMPATIBLE',adaptations=changes,cpu_seconds=time.process_time()-started)

def failure_charge(cap, folder):
    """Recover failed-attempt logical charge from retained evidence, once."""
    receipt_path=folder/('promod/exit.json' if cap.name.startswith('promod3') else 'native/exit.json')
    if not receipt_path.exists():
        return dict(logical_work=0.,rule='NO_COMPLETED_CPU_RECEIPT',cpu_seconds=None)
    receipt=read(receipt_path)
    cpu=receipt.get('physical_cpu_seconds',receipt.get('cpu_seconds'))
    controlled=cap.name in ('ngk_refine','ngk_rebuild')
    progress=folder/'logical_progress.json'
    returned=folder/'native/returned.json.gz'
    if returned.exists():
        value=json.loads(gzip.decompress(returned.read_bytes()))['work']
        rule='RETAINED_RETURNED_LOGICAL_WORK'
    elif controlled:
        value=read(progress)['work'] if progress.exists() else cap.logical_work
        rule='PERSISTED_LOGICAL_WORK' if progress.exists() else 'LOST_PREFIX_RESERVED_WORK'
    else:
        value=cpu;rule='MEASURED_PRIMITIVE_CPU'
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise RuntimeError('Invalid retained failed-attempt accounting')
    return dict(logical_work=min(cap.logical_work,value),cpu_seconds=cpu,rule=rule,
                receipt_sha256=sha(receipt_path))

def save_state(source,state):
    pose = state.payload['pose']
    atoms = []
    for i in range(1,pose.size()+1):
        for a in range(1,pose.residue(i).natoms()+1):
            xyz=pose.residue(i).xyz(a)
            atoms.append((i,a,(xyz.x,xyz.y,xyz.z)))
    return dict(binding=state.binding,features=state.features,
        exported=state.payload['exported'],rng=state.payload['rng'],
        projection=source.backend.projection(pose),atoms=atoms,
        residue_type_names=[pose.residue(i).name() for i in range(1,pose.size()+1)],
        secstruct=pose.secstruct(),fold_tree=str(pose.fold_tree()))

class Executor:
    def __init__(self,source,output,program,profile,resources,promod_command,
                 cpu_budget,wall_budget,cpu_start,wall_start,reserve,promod_input):
        self.source,self.output,self.program=source,output,program
        self.profile,self.tariff=profile,profile['tariff']
        self.prices=native_prices(profile)
        self.resources,self.promod_command=resources,promod_command
        self.cpu_budget,self.wall_budget=cpu_budget,wall_budget
        self.cpu_start,self.wall_start=cpu_start,wall_start
        self.reserve,self.promod_input=reserve,promod_input
        self.serial=0; self.counts={}; self.outcomes={}; self.failed_work=0.; self.failure_account=None

    def remaining_cpu(self):
        return max(0.,self.cpu_budget-(cpu_now()-self.cpu_start)-self.reserve)

    def remaining_wall(self):
        return max(0.,self.wall_budget-(time.monotonic()-self.wall_start)-self.reserve)

    def available(self,cap,parent):
        if self.remaining_cpu()<1 or self.remaining_wall()<=0 or cap.logical_work<1:
            return False
        if cap.name.startswith('promod3'):
            return parent.binding==self.source.raw.binding
        return parent.binding['sequence_sha256']==self.source.raw.binding['sequence_sha256']

    def after_result(self,result):
        if result.states:
            self.source.set_rng(result.states[-1].payload['rng'])
        if hashlib.sha256(self.source.rng().encode()).hexdigest()!=result.rng_sha256:
            raise RuntimeError('Committed RNG and routing ledger differ')

    def __call__(self,cap,parent,context):
        folder=self.output/'actions'/f'{self.serial:04d}'
        self.failed_work=0.; self.failure_account=None
        try:
            return self._execute(cap,parent,context)
        except Exception:
            self.failure_account=failure_charge(cap,folder)
            self.failed_work=self.failure_account['logical_work']
            if folder.exists():
                write(folder/'failed_work.json',self.failure_account)
            raise

    def _execute(self,cap,parent,context):
        from .native.observations import VIEW_FIELDS
        source=self.source
        before_rng=source.rng()
        if hashlib.sha256(before_rng.encode()).hexdigest()!=context['rng_sha256']:
            raise RuntimeError('Current route RNG mismatch')
        folder=self.output/'actions'/f'{self.serial:04d}'
        self.serial+=1; folder.mkdir(parents=True,exist_ok=False)
        self.counts[cap.name]=self.counts.get(cap.name,0)+1
        write(folder/'binding.json',dict(action=cap.token,parent=parent.binding,context=context))
        cpu_limit=min(1800,math.floor(self.remaining_cpu()))
        wall_limit=min(5400,self.remaining_wall())
        if cap.name not in ('ngk_refine','ngk_rebuild'):
            cpu_limit=min(cpu_limit,math.floor(cap.logical_work))
        controlled=cap.name in ('ngk_refine','ngk_rebuild')
        if cpu_limit<1 or wall_limit<=0:
            raise RuntimeError('Budget exhausted before native dispatch')
        endpoint_cost=self.tariff['view']+self.tariff['fresh_state']
        if cap.name.startswith('promod3'):
            from .promod import execute
            result=execute(self.promod_input,cap.name,folder/'promod',self.resources,
                           self.promod_command,cpu_limit,wall_limit)
            cpu=result['physical_cpu_seconds']; status=result['status']
            self.outcomes[status]=self.outcomes.get(status,0)+1
            if 'mapped_pdb' not in result:
                if status not in ('PARTIAL_MODEL','CPU_LIMIT','WALL_LIMIT','BUDGET_EXHAUSTED'):
                    raise RuntimeError('ProMod3 did not complete; see '+str(folder/'promod'))
                return OperationResult([],min(cap.logical_work,max(cpu,1e-12)),cpu,
                    status='NO_CANDIDATE',provenance=result,rng_sha256=context['rng_sha256'])
            pose=source.backend.load(result['mapped_pdb'])
            source.set_rng(before_rng)
            chemistry=chemistry_check(source,pose)
            write(folder/'chemical_identity.json',chemistry)
            if chemistry['status']!='COMPATIBLE':
                self.outcomes['CHEMISTRY_INCOMPATIBLE']=self.outcomes.get('CHEMISTRY_INCOMPATIBLE',0)+1
                return OperationResult([],min(cap.logical_work,max(cpu+chemistry['cpu_seconds'],1e-12)),cpu,
                    status='NO_CANDIDATE',provenance=dict(generation=result,chemistry=chemistry),
                    rng_sha256=context['rng_sha256'])
            state=source.state(pose)
            work=cpu+endpoint_cost+chemistry['cpu_seconds']
            memory=None
            details=result
        else:
            def native():
                from .native import ngk_adapter
                from .native.legacy_protocol import prefix
                from .native.execution import run_legacy_refinement
                from .native.decision_trace import DecisionRecorder
                from .minimize import render
                pose=parent.payload['pose'].clone()
                memory=None; details={}
                cooperative=CooperativeStop(cpu_limit=cpu_limit,wall_limit=wall_limit,
                                             terminal_reserve=self.reserve)
                if cap.name=='minimize':
                    start=time.process_time()
                    result=source.backend.apply(pose,render(source.definitions),'minimize')
                    work=time.process_time()-start
                    if result['apply_success'] is not True:
                        raise RuntimeError('Original MinMover returned failure')
                    details=dict(stage='minimize',normal_return=True)
                else:
                    ngk_adapter.configure_runtime(source.r,ngk_adapter.PARAMETERS)
                    pose,loops,score,pre=prefix(source.r,pose,source.definitions,rebuild=cap.name=='ngk_rebuild')
                    write(folder/'prefix_returned.json',pre)
                    work=pre['process_cpu_seconds']; memory=context['policy_memory']
                    remaining=max(0.,cap.logical_work-work-endpoint_cost)
                    if pre['gate']['eligible'] and remaining>=reserve_observation(self.tariff)+self.prices['controller'] and not cooperative.should_stop('refinement_entry'):
                        recorder=DecisionRecorder(maximum_details=16)
                        def binding(host,role):
                            return source.fingerprint_binding(host.mc.last_accepted_pose() if role=='last' else host.pose)
                        def progress(host,marker):
                            write(folder/'logical_progress.json',dict(work=work+host.work,stage='refinement',marker=marker))
                        with RoutingPolicyClient(self.program,source_fields=VIEW_FIELDS) as client:
                            host,memory=run_legacy_refinement(r=source.r,parent_pose=pose,loops=loops,
                                client=client,context=context,scorefxn=score,
                                observation_builder=source.observer,prices=self.prices,
                                work_limit=remaining,recorder=recorder,state_binding=binding,
                                observation_tariff=self.tariff,cooperative_stop=cooperative,
                                budget_receipt=progress)
                        work+=host.work
                        details=dict(stage='refinement',normal_return=True,native_counts=dict(host.counts),
                                     decisions=recorder.records)
                    else:
                        details=dict(stage='prefix',normal_return=True,refinement_entered=False,
                                     prefix_gate=pre['gate'])
                chemistry=chemistry_check(source,pose)
                write(folder/'chemical_identity.json',chemistry)
                if chemistry['status']!='COMPATIBLE':
                    from .native.export import export_source_pose
                    return dict(rejected_chemistry=True,chemistry=chemistry,
                        retained_endpoint=export_source_pose(pose,backend=source.backend),
                        rng=source.rng(),memory=memory,work=work+chemistry['cpu_seconds'],details=details)
                state=source.state(pose)
                return dict(state=save_state(source,state),memory=memory,
                            work=work+endpoint_cost+chemistry['cpu_seconds'],details=details)
            result,receipt=bounded_call(folder/'native',native,cpu_limit,wall_limit)
            cpu=receipt['cpu_seconds'];status=receipt['status']
            self.outcomes[status]=self.outcomes.get(status,0)+1
            if result is None:
                if status=='ERROR':
                    raise RuntimeError('Native action failed; see '+str(folder/'native/error.json'))
                if controlled:
                    work=(read(folder/'logical_progress.json')['work'] if (folder/'logical_progress.json').exists() else cap.logical_work)
                else: work=cpu
                return OperationResult([],min(cap.logical_work,max(work,1e-12)),cpu,
                    status='NO_CANDIDATE',provenance=dict(receipt=receipt,retained_parent=True),
                    policy_memory=context.get('policy_memory') if controlled else None,
                    rng_sha256=context['rng_sha256'])
            if result.get('rejected_chemistry'):
                self.outcomes['CHEMISTRY_INCOMPATIBLE']=self.outcomes.get('CHEMISTRY_INCOMPATIBLE',0)+1
                source.set_rng(result['rng'])
                return OperationResult([],min(cap.logical_work,max(result['work'],1e-12)),cpu,
                    status='NO_CANDIDATE',provenance=dict(receipt=receipt,chemistry=result['chemistry']),
                    policy_memory=result['memory'] if controlled else None,
                    rng_sha256=hashlib.sha256(result['rng'].encode()).hexdigest())
            saved=result['state']
            pose=restore_state_pose(source,parent,saved)
            source.set_rng(saved['rng'])
            if source.fingerprint_binding(pose)!=saved['binding']:
                raise RuntimeError('Restored full precision endpoint binding differs')
            state=State(saved['binding'],saved['features'],dict(pose=pose,exported=saved['exported'],rng=saved['rng']))
            work,memory=result['work'],result['memory']
            details=dict(receipt=receipt,details=result['details'])
        if work>cap.logical_work:
            source.set_rng(before_rng)
            return OperationResult([],cap.logical_work,cpu,status='NO_CANDIDATE',
                provenance=dict(actual_logical_work=work,rejected_over_budget=True,details=details),
                policy_memory=context.get('policy_memory') if controlled else None,rng_sha256=context['rng_sha256'])
        return OperationResult([state],max(work,1e-12),cpu,provenance=details,
            policy_memory=memory,rng_sha256=state.binding['rng_sha256'])

def run(input_path,policy,work_profile,resources,promod_command,output,cpu_seconds=1800.,wall_seconds=5400.):
    from .native.runtime import NativeSource
    from .native.observations import VIEW_FIELDS
    from .promod import prepare_source
    from .resources import verify_resources
    if not hasattr(os,'fork') or not Path('/proc/self').exists():
        raise RuntimeError('Native execution requires Linux')
    for value in (cpu_seconds,wall_seconds):
        if not math.isfinite(value) or value<=0:
            raise ValueError('Positive finite budgets required')
    data=load_input(input_path); profile=load_work_profile(work_profile)
    program=policy_source(policy)
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    with (output/'owner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        bound_resources=verify_resources(resources)
        from .native.ngk_adapter import ROSETTA_VERSION
        identity=dict(input=data,source_sha256=sha(data['structure']),policy=policy,
            policy_sha256=POLICY_HASHES[policy],work_profile_sha256=profile['profile_sha256'],
            resources_sha256=sha(resources),cpu_seconds=cpu_seconds,wall_seconds=wall_seconds,
            promod_command=command_identity(promod_command),package_sha256=implementation_identity(),
            runtime_version=ROSETTA_VERSION,python_version=sys.version)
        if (output/'started.json').exists():
            old=read(output/'started.json')
            if old['identity']!=identity:
                raise RuntimeError('Output belongs to different inputs/configuration')
            if (output/'result.json').exists():
                retained=read(output/'result.json')
                if retained['status']=='ERROR':
                    raise RuntimeError('Prior failed run requires reconciliation; retained endpoint is preserved')
                return retained
            raise RuntimeError('Prior run incomplete: retained artifacts require reconciliation, not re-execution')
        reserve=profile['delivery_reserve_cpu_seconds']
        minimum=reserve+profile['policy_setup_work']+profile['tariff']['view']+profile['tariff']['fresh_state']+2*profile['operation_prices']['controller']
        if cpu_seconds<=minimum or wall_seconds<=reserve:
            raise ValueError('Budget is below the explicit profile setup/delivery reserve')
        cpu_start=cpu_now();wall_start=time.monotonic()
        write(output/'started.json',dict(identity=identity,started_unix=time.time()))
        source=NativeSource(data['structure'],data['loops'],data['sequence'],data['seed'],
                            data['input_kind'],local_energy_residues=data['local_energy_residues'])
        promod_input=prepare_source(data['structure'],data['sequence'],data['loops'],output/'prepared_promod')
        executor=Executor(source,output,program,profile,resources,promod_command,
                          cpu_seconds,wall_seconds,cpu_start,wall_start,reserve,promod_input)
        runtime=digest(str(source.r.utility.Version.version()));implementation=sha(__file__)
        db=digest(read(resources))
        caps=[Capability(name,'frozen',digest(dict(source=source.raw.binding,implementation=implementation)),
              runtime,implementation,cpu_seconds,1,database_sha256=db if name.startswith('promod3') else None)
              for name in ('minimize','promod3_database','promod3_mc','ngk_rebuild','ngk_refine')]
        router=Router(source.raw,caps,executor,budget=cpu_seconds-reserve,
            callback_work=profile['operation_prices']['controller'],protocol_sha256=implementation,
            policy_sha256=POLICY_HASHES[policy],clone_state=source.clone_state)
        router.work=profile['policy_setup_work']+profile['tariff']['view']+profile['tariff']['fresh_state']
        state=None;status='COMPLETE';error=None
        try:
            with RoutingPolicyClient(program,source_fields=VIEW_FIELDS) as client:
                while state is None:
                    left=max(0.,router.budget-router.work-2*router.callback_work)
                    router.capabilities={c.token:replace(c,logical_work=min(c.logical_work,left)) for c in caps if left>=1.}
                    if router.work+router.callback_work>router.budget:
                        status='BUDGET_DELIVERY'; state=source.clone_state(router.states[max(router.states)]); break
                    state=router.step(client.decide_view)
                    write(output/'route_steps'/f'{len(router.evidence):04d}.json',router.evidence[-1])
                    write(output/'progress.json',dict(actions=executor.counts,logical_work=router.work,
                        cpu_seconds=cpu_now()-cpu_start,wall_seconds=time.monotonic()-wall_start,
                        last_step=len(router.evidence)))
        except Exception as exc:
            status='ERROR';error=type(exc).__name__+': '+str(exc)
            if router.pending_operation is not None:
                router.work+=executor.failed_work
            state=source.clone_state(router.states[max(router.states)])
        endpoint=source.serialize_endpoint(state)
        (output/'final.pdb').write_text(endpoint['pdb_text'])
        with gzip.open(output/'endpoint.json.gz','wt') as stream:
            json.dump(endpoint,stream,allow_nan=False)
        result=dict(status=status,error=error,policy=policy,policy_sha256=POLICY_HASHES[policy],
            structure='final.pdb',final_structure_sha256=sha(output/'final.pdb'),
            geometry_valid=state.features['geometry_valid'],features=state.features,
            delivered_binding=state.binding,action_counts=executor.counts,outcomes=executor.outcomes,
            logical_work=router.work,logical_budget=router.budget,physical_cpu_seconds=cpu_now()-cpu_start,
            cpu_budget_seconds=cpu_seconds,wall_seconds=time.monotonic()-wall_start,wall_budget_seconds=wall_seconds,
            policy_memory=router.memory,model_calls=0,target_structure_used=False,
            emergency_delivery=status!='COMPLETE',work_profile_sha256=profile['profile_sha256'],
            failed_attempt_account=executor.failure_account)
        write(output/'result.json',result)
        return result
