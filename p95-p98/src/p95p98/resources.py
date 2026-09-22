"""Verify user-owned native resource files, not an experimental dataset."""
from pathlib import Path
from .io import read, sha

def verify_resources(path):
    path=Path(path).resolve()
    data=read(path)
    required={'structure_db_sha256','fragment_db_sha256','source_filter_sha256'}
    if set(data.get('resources',{})) != required:
        raise ValueError('Resources require StructureDB, paired FragDB and source-filter receipt')
    paths={}
    for name,item in data['resources'].items():
        p=Path(item['path'])
        if not p.is_absolute():p=path.parent/p
        if not p.is_file() or sha(p)!=item['sha256']:
            raise ValueError('Missing or changed native resource: '+name)
        paths[name]=p
    return paths
