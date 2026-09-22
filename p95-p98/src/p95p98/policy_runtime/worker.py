"""One isolated interpreter per trajectory; no native state or target data."""
import json
import math
from pathlib import Path
import resource
import signal
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import MAX_REQUEST, MAX_RESPONSE, MAX_RSS, SAFE, decode, encode, validate_source


def receive():
    data = sys.stdin.buffer.readline(MAX_REQUEST + 1)
    if not data:
        raise EOFError()
    if len(data) > MAX_REQUEST or not data.endswith(b'\n'):
        raise ValueError('oversized or unterminated input')
    return decode(data)


def send(value):
    sys.stdout.buffer.write(encode(value, MAX_RESPONSE))
    sys.stdout.buffer.flush()


def main():
    resource.setrlimit(resource.RLIMIT_AS, (MAX_RSS, MAX_RSS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGPROF, signal.SIG_DFL)
    initial = receive()
    validate_source(initial['source'])
    cpu_limit = initial['cpu_s']
    if type(cpu_limit) not in (int, float) or not 0 < cpu_limit <= 3:
        raise ValueError('invalid CPU limit')
    namespace = {'__builtins__': dict(SAFE)}
    exec(compile(initial['source'], '<candidate>', 'exec'), namespace, namespace)
    initial_serial = initial.get('initial_serial', 0)
    if type(initial_serial) is not int or initial_serial < 0:
        raise ValueError('invalid initial serial')
    send({'ok': True, 'ready': True})
    expected = initial_serial + 1
    while True:
        try:
            request = receive()
        except EOFError:
            return
        if request['serial'] != expected:
            raise ValueError('request sequence differs')
        start = time.process_time()
        signal.setitimer(signal.ITIMER_PROF, cpu_limit)
        try:
            value = namespace['decide'](request['view'])
            # Keep timer armed through output conversion and size checking.
            encoded = encode(value, MAX_RESPONSE - 1024)
            value = decode(encoded)
            elapsed = time.process_time() - start
            response = {'ok': True, 'serial': expected, 'value': value, 'cpu_s': elapsed}
            send(response)
        except BaseException as exc:
            send({'ok': False, 'serial': expected, 'error': type(exc).__name__, 'cpu_s': time.process_time() - start})
            return
        finally:
            signal.setitimer(signal.ITIMER_PROF, 0)
        expected += 1


if __name__ == '__main__':
    main()
