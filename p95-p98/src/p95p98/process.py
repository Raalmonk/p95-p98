"""Isolated native actions, adapted from the evaluated production bounded_call.

Only JSON-compatible endpoint exports cross the process boundary. No Pose pickle
or pre-existing experimental cache is used. An uncertain prior action is not retried.
"""
import gzip
import json
import math
import os
from pathlib import Path
import resource
import signal
import time
import traceback
from .io import read, write

def classify(exitcode, *, returned=False, wall=False, installed=False):
    if wall:
        return 'WALL_LIMIT'
    if exitcode == 0 and returned:
        return 'RETURNED'
    if exitcode == -signal.SIGXCPU and installed:
        return 'CPU_LIMIT'
    return 'ERROR'

def bounded_call(folder, function, cpu_limit, wall_limit):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if (folder/'started.json').exists():
        raise RuntimeError('Prior action exists: reconcile it; no automatic repeat')
    if cpu_limit < 1 or wall_limit <= 0:
        raise ValueError('Action budget exhausted before dispatch')
    if len(list(Path('/proc/self/task').iterdir())) != 1:
        raise RuntimeError('Native action requires a single-threaded parent')
    write(folder/'started.json', dict(parent_pid=os.getpid(), cpu_limit=cpu_limit,
                                     wall_limit=wall_limit, started_unix=time.time()))
    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
            ceiling = math.floor(cpu_limit)
            resource.setrlimit(resource.RLIMIT_CPU, (ceiling, ceiling+1))
            write(folder/'child_limits.json', dict(pid=os.getpid(), installed=[ceiling,ceiling+1]))
            fd = os.open(folder/'native.log', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
            os.dup2(fd,1); os.dup2(fd,2); os.close(fd)
            value = function()
            payload = json.dumps(value, allow_nan=False, separators=(',',':')).encode()
            with gzip.open(folder/'returned.json.gz', 'xb') as stream:
                stream.write(payload)
            os._exit(0)
        except BaseException:
            write(folder/'error.json', dict(traceback=traceback.format_exc()))
            os._exit(1)
    begin = time.monotonic()
    timeout = False
    try:
        while True:
            found, status, usage = os.wait4(pid, os.WNOHANG)
            if found:
                break
            if time.monotonic()-begin >= wall_limit:
                os.killpg(pid, signal.SIGKILL)
                timeout = True
                _,status,usage = os.wait4(pid,0)
                break
            time.sleep(.1)
    except BaseException:
        try: os.killpg(pid,signal.SIGKILL)
        except ProcessLookupError: pass
        _,status,usage = os.wait4(pid,0)
        write(folder/'exit.json', dict(status='USER_ABORTED',
              cpu_seconds=usage.ru_utime+usage.ru_stime, exitcode=os.waitstatus_to_exitcode(status)))
        raise
    code = os.waitstatus_to_exitcode(status)
    path = folder/'returned.json.gz'
    kind = classify(code, returned=path.exists(), wall=timeout,
                    installed=(folder/'child_limits.json').exists())
    receipt = dict(status=kind, exitcode=code, cpu_seconds=usage.ru_utime+usage.ru_stime,
                   wall_seconds=time.monotonic()-begin)
    write(folder/'exit.json',receipt)
    return (json.loads(gzip.decompress(path.read_bytes())) if kind=='RETURNED' else None),receipt
