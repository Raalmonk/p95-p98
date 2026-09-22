"""Persistent serial client. Any failed call closes the worker, never falls back."""
import copy
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import time

from ..policy_contract import EVENTS, _memory, validate_decision
try:
    from .core import MAX_REQUEST, MAX_RESPONSE, PolicyRuntimeError, decode, encode, project_source, validate_source
except ImportError:
    from core import MAX_REQUEST, MAX_RESPONSE, PolicyRuntimeError, decode, encode, project_source, validate_source


class PolicyClient:
    def __init__(self, source, *, source_fields, timeout_s=1., cpu_s=.5, memory=None):
        validate_source(source)
        if type(timeout_s) not in (int, float) or not 0 < timeout_s <= 3 or type(cpu_s) not in (int, float) or not 0 < cpu_s <= 3:
            raise PolicyRuntimeError('wall and CPU limits must be in (0,3]')
        self.source, self.fields = source, tuple(source_fields)
        if len(set(self.fields)) != len(self.fields):
            raise PolicyRuntimeError('duplicate source whitelist fields')
        self.timeout, self.cpu_limit = timeout_s, cpu_s
        self.memory = _memory({} if memory is None else memory)
        self.process = None
        self.directory = None
        self.serial = 0
        self.cpu_seconds = 0.
        self.worker_cpu_seconds = 0.
        self.wall_seconds = 0.
        self.lock = threading.Lock()

    def __enter__(self):
        if self.process is not None:
            raise PolicyRuntimeError('worker already started')
        self.directory = tempfile.TemporaryDirectory(prefix='ngk-policy-')
        self.process = subprocess.Popen([sys.executable, '-I', '-S', str(Path(__file__).with_name('worker.py'))],
            cwd=self.directory.name, env={}, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True, bufsize=0)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        try:
            response = self._exchange({'source': self.source, 'cpu_s': self.cpu_limit,
                                       'initial_serial': self.serial}, startup=True)
            if response != {'ok': True, 'ready': True}:
                raise PolicyRuntimeError('worker initialization failed')
        except BaseException:
            self.close()
            raise
        return self

    def _exchange(self, payload, startup=False):
        if self.process is None or self.process.returncode is not None:
            raise PolicyRuntimeError('worker unavailable')
        data = encode(payload, MAX_REQUEST)
        sent, output = 0, bytearray()
        deadline = time.monotonic() + (3. if startup else self.timeout)
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise PolicyRuntimeError('policy wall timeout')
                for key, _ in selector.select(remaining):
                    if key.fileobj is self.process.stdin:
                        try:
                            sent += os.write(self.process.stdin.fileno(), data[sent:])
                        except BrokenPipeError as exc:
                            raise PolicyRuntimeError('worker exited while receiving request') from exc
                        if sent == len(data):
                            selector.unregister(self.process.stdin)
                    else:
                        chunk = os.read(self.process.stdout.fileno(), MAX_RESPONSE + 1 - len(output))
                        if not chunk:
                            raise PolicyRuntimeError('worker exited (CPU/memory limit or execution error)')
                        output.extend(chunk)
                        if len(output) > MAX_RESPONSE:
                            raise PolicyRuntimeError('response exceeded byte bound')
                        if b'\n' in output:
                            if not output.endswith(b'\n') or output.count(b'\n') != 1:
                                raise PolicyRuntimeError('nonserial worker response')
                            return decode(output)

    def decide(self, event, observation, *, capabilities, populated_slots):
        if not self.lock.acquire(blocking=False):
            raise PolicyRuntimeError('concurrent policy calls are not allowed')
        begin = time.monotonic()
        try:
            if event not in EVENTS:
                raise PolicyRuntimeError('unknown event')
            projected = project_source(observation, self.fields)
            self.serial += 1
            response = self._exchange({'serial': self.serial, 'view': {'event': event, 'observation': projected, 'memory': self.memory}})
            if response.get('serial') != self.serial or response.get('ok') is not True:
                raise PolicyRuntimeError('candidate execution failed: ' + str(response.get('error', 'sequence')))
            self.cpu_seconds += response['cpu_s']
            answer = response['value']
            if type(answer) is not dict or set(answer) != {'decision', 'memory'}:
                raise PolicyRuntimeError('candidate must return decision and memory')
            clean = validate_decision(dict(event=event, **answer), event=event,
                capabilities=capabilities, populated_slots=populated_slots)
            self.memory = copy.deepcopy(clean['memory'])
            return clean
        except BaseException:
            self.close()
            raise
        finally:
            self.wall_seconds += time.monotonic() - begin
            self.lock.release()

    def close(self):
        if self.process is not None:
            if self.process.returncode is None:
                try:
                    os.kill(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                _, status, usage = os.wait4(self.process.pid, 0)
                self.process.returncode = os.waitstatus_to_exitcode(status)
                self.worker_cpu_seconds += usage.ru_utime + usage.ru_stime
            self.process.stdin.close()
            self.process.stdout.close()
            self.process = None
        if self.directory is not None:
            self.directory.cleanup()
            self.directory = None

    def __exit__(self, *_):
        self.close()
