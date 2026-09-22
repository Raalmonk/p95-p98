"""Native environment entry point, retaining original operations and defaults."""
import json
from pathlib import Path
import resource
import sys
import time
from .native import ProModNative, file_sha256
from .mapping import map_output_lines


def main():
    job = json.loads(Path(sys.argv[1]).read_text())
    limit = job['cpu_limit_seconds']
    resource.setrlimit(resource.RLIMIT_CPU, (limit, limit+1))
    import promod3, ost
    from promod3 import modelling, loop, sidechain
    from ost import io, seq
    if str(promod3.__version__) != '3.7.0' or str(ost.__version__) != '2.12.0':
        raise RuntimeError('Required ProMod3 3.7.0 and OpenStructure 2.12.0')
    manifest_path = Path(job['resources_json'])
    resources = json.loads(manifest_path.read_text())
    paths = {k: (manifest_path.parent/v['path']).resolve()
             for k,v in resources['resources'].items()}
    hashes = {k: v['sha256'] for k,v in resources['resources'].items()}
    folder = Path(job['output_dir'])
    def publish(name, data):
        (folder/name).write_text(json.dumps(data, indent=2)+'\n')
    def checkpoint(stage, handle):
        path = folder/(stage+'.pdb')
        io.SavePDB(handle.model, str(path))
        publish(stage+'.json', dict(stage=stage, gaps=len(handle.gaps),
                process_cpu_seconds=time.process_time(), pdb_sha256=file_sha256(path)))
    adapter = ProModNative(modelling=modelling, loop=loop, sidechain=sidechain,
        io=io, seq=seq, input_root=Path(job['input_json']).parent,
        resource_paths=paths, verified_resources=hashes,
        database_receipt=dict(hashes, status='VERIFIED'), checkpoint=checkpoint)
    publish('native_started.json', dict(action=job['action'], epoch=time.time()))
    raw, data = adapter.prepare(job['input_json'], file_sha256(job['input_json']))
    result = adapter.branch(raw, action=job['action'], frozen_parameters={})
    model = result.pop('model')
    if model is not None:
        io.SavePDB(model, str(folder/'native.pdb'))
        mapped = map_output_lines((folder/'native.pdb').read_text().splitlines(keepends=True), data)
        (folder/'mapped.pdb').write_text(''.join(mapped))
        result['mapped_pdb_sha256'] = file_sha256(folder/'mapped.pdb')
    result.update(native_branch_calls=1, target_access=False,
                  rng_identity='ProMod3 native defaults; no Rosetta RNG substitution',
                  resources=hashes)
    publish('native_result.json', result)


if __name__ == '__main__':
    main()
