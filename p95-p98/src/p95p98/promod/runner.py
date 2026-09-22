"""Single-use, CPU-accounted process launcher. No cached structure is required."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def execute(input_json, action, output_dir, resources_json, python_command,
            cpu_limit, wall_limit, *, progress=None):
    if action not in ('promod3_database', 'promod3_mc'):
        raise ValueError('Unsupported ProMod3 branch')
    if not all(math.isfinite(x) and x > 0 for x in (cpu_limit, wall_limit)):
        raise ValueError('Positive finite CPU and wall limits required')
    if not hasattr(os, 'wait4'):
        raise RuntimeError('ProMod3 execution requires POSIX wait4 CPU accounting')
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    job = dict(input_json=str(Path(input_json).resolve()), action=action,
               resources_json=str(Path(resources_json).resolve()),
               output_dir=str(output), cpu_limit_seconds=min(1800, math.floor(cpu_limit)))
    if job['cpu_limit_seconds'] < 1:
        return dict(status='BUDGET_EXHAUSTED', physical_cpu_seconds=0., native_started=False)
    with (output / 'job.json').open('x') as stream:
        json.dump(job, stream)
    command = list(python_command) + ['-m', 'p95p98.promod.worker', str(output / 'job.json')]
    env = dict(os.environ, PM3_OPENMM_CPU_THREADS='1', OPENMM_CPU_THREADS='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    begin = time.monotonic()
    timeout = False
    with (output/'stdout.log').open('xb') as stdout, (output/'stderr.log').open('xb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True, env=env)
        try:
            while True:
                pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                if pid:
                    break
                if progress is not None:
                    progress()
                if time.monotonic()-begin >= min(5400., wall_limit):
                    timeout = True
                    os.killpg(process.pid, signal.SIGKILL)
                    pid, status, usage = os.wait4(process.pid, 0)
                    break
                time.sleep(.1)
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            os.wait4(process.pid, 0)
            raise
        code = os.waitstatus_to_exitcode(status)
        process.returncode = code
    cpu = usage.ru_utime + usage.ru_stime
    result = dict(exit_code=code, physical_cpu_seconds=cpu,
                  new_physical_cpu_seconds=cpu, reused_completed_attempt=False,
                  wall_seconds=time.monotonic()-begin,
                  native_started=(output/'native_started.json').is_file())
    if timeout:
        result['status'] = 'WALL_LIMIT'
    elif code == -signal.SIGXCPU:
        result['status'] = 'CPU_LIMIT'
    elif code == -signal.SIGKILL:
        result['status'] = 'KILLED_UNKNOWN_CAUSE'
    elif code == 0 and (output/'native_result.json').is_file():
        result.update(json.loads((output/'native_result.json').read_text()))
        if result['status'] == 'MODEL_RETURNED':
            from .native import file_sha256
            path = output/'mapped.pdb'
            if file_sha256(path) != result['mapped_pdb_sha256']:
                raise RuntimeError('ProMod3 output binding differs')
            result['mapped_pdb'] = str(path)
    else:
        result['status'] = 'INFRASTRUCTURE_OR_ADAPTER_ERROR'
    (output/'exit.json').write_text(json.dumps(result, indent=2)+'\n')
    return result
