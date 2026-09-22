"""Frozen whole-entry filter, exact compiled legacy alignment, source metadata only."""
import concurrent.futures
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
from . import resource_identity as b0
import argparse

OUT = None
LIB = None
MATRIX = (ctypes.c_int*676)()
for (a,b),value in b0._BLOSUM62.items():
    MATRIX[(ord(a)-65)*26+ord(b)-65] = value
PROTECTED = None

def align(a,b):
    out = (ctypes.c_int*4)()
    LIB.identity(a.encode(),b.encode(),MATRIX,out)
    return list(out)

def screen(item):
    index, sequence = item
    for record in PROTECTED['sequences']:
        result = align(sequence, record['sequence'])
        if result[1]*5 >= result[3]*2:
            return index, {'label':record['label'], 'score':result[0], 'exact_matches':result[1], 'gap_char_count':result[2], 'denominator':result[3]}
    return index, None

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def main():
    global OUT, LIB, PROTECTED
    parser = argparse.ArgumentParser(description='Build source-excluded coupled ProMod3 databases')
    parser.add_argument('--protected', required=True, help='JSON with sequences:[{label,sequence}], entries:[PDB identifiers]')
    parser.add_argument('--identity-library', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--structure-db', required=True)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    OUT = Path(args.output).resolve()
    OUT.mkdir(parents=True, exist_ok=False)
    LIB = ctypes.CDLL(str(Path(args.identity_library).resolve()))
    LIB.identity.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    PROTECTED = json.loads(Path(args.protected).read_text())
    if not PROTECTED['sequences'] or args.workers < 1:
        raise ValueError('At least one protected sequence and worker required')
    for record in PROTECTED['sequences']:
        if not record['sequence'] or any(aa not in b0._AMINO_ACIDS for aa in record['sequence']):
            raise ValueError('Protected sequence must be canonical and nonempty')
    if any(len(e)!=4 or not e.isalnum() or e!=e.lower() for e in PROTECTED['entries']):
        raise ValueError('Protected entries must be lowercase four-character PDB identifiers')
    started=time.time()
    import promod3, ost
    if str(promod3.__version__) != '3.7.0' or str(ost.__version__) != '2.12.0':
        raise RuntimeError('Required ProMod3 3.7.0 and OpenStructure 2.12.0')
    from promod3 import loop
    source=loop.StructureDB.Load(str(Path(args.structure_db).resolve()))
    rows=[];tasks=[]
    entries=set(PROTECTED['entries'])
    for i in range(source.GetNumCoords()):
        raw,entry,group=b0._coordinfo_identity(source.GetCoordInfo(i).id)
        try:sequence=b0._db_sequence_string(source.GetSequence(i))
        except ValueError:sequence=None
        reason='EXCLUDE_PROTECTED_SOURCE_ENTRY' if entry in entries else 'EXCLUDE_UNPARSEABLE_ENTRY_ID' if entry is None else 'EXCLUDE_MISSING_OR_NONCANONICAL_SEQUENCE' if sequence is None else None
        rows.append({'index':i,'raw_id':raw,'entry':entry,'group':group,'reason':reason})
        if reason is None:tasks.append((i,sequence))
    checkpoint=OUT/'identity-results.jsonl'
    done={}
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            item=json.loads(line);done[item[0]]=item[1]
    with checkpoint.open('a',buffering=1) as f, concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i,witness in pool.map(screen,[x for x in tasks if x[0] not in done],chunksize=8):
            f.write(json.dumps([i,witness])+'\n');done[i]=witness
            if len(done)%1000==0:print('screened',len(done),len(tasks),flush=True)
    for i,witness in done.items():
        rows[i]['first_threshold_witness']=witness
        rows[i]['reason']='EXCLUDE_IDENTITY_GE_40_PERCENT' if witness else None
    excluded={r['group'] for r in rows if r['reason'] is not None}
    keep=[r['index'] for r in rows if r['group'] not in excluded]
    assert keep
    for row in rows:
        row['disposition']='EXCLUDE' if row['group'] in excluded else 'KEEP'
    (OUT/'filter-ledger.json').write_text(json.dumps({'policy':'source-derived expected_sequence; exact legacy BLOSUM62 three-state global affine -11/-1; matches/min_length>=0.4; first witness; whole entry','source_members':len(rows),'kept_members':len(keep),'rows':rows,'protected':PROTECTED},indent=2))
    out=OUT/'database';out.mkdir(exist_ok=True)
    filtered=source.GetSubDB(keep)
    sp=out/'structure_db.dat'
    if not sp.exists():filtered.Save(str(sp))
    assert loop.StructureDB.Load(str(sp)).GetNumCoords()==len(keep)
    frag=loop.FragDB(1.0,20)
    for n in range(3,15):
        frag.AddFragments(n,1.0,filtered)
        print('fragments',n,frag.GetNumFragments(n),flush=True)
    fp=out/'frag_db.dat'
    if not fp.exists():frag.Save(str(fp))
    reloaded=loop.FragDB.Load(str(fp))
    assert all(reloaded.GetNumFragments(n)==frag.GetNumFragments(n) for n in range(3,15))
    manifest = {'promod3_version':'3.7.0', 'openstructure_version':'2.12.0',
        'source_structure_sha256':digest(Path(args.structure_db)),
        'resources':{key:{'path':str(path.relative_to(OUT)), 'sha256':digest(path)}
            for key,path in [('structure_db_sha256',sp),('fragment_db_sha256',fp),
                             ('source_filter_sha256',OUT/'filter-ledger.json')]}}
    (OUT/'resources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'FILTER_COMPLETE.json').write_text(json.dumps({'status':'COMPLETE','structure_sha256':digest(sp),'fragment_sha256':digest(fp),'kept_members':len(keep),'wall_seconds':time.time()-started,'explicit_loaders_verified':True},indent=2))

if __name__=='__main__':main()
