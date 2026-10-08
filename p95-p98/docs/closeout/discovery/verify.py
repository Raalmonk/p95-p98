"""Offline joins, source identities and literal historical patch replay; no policy execution."""
import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
def read(name):
    return json.loads((HERE / name).read_text())
def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

rows = list(csv.DictReader((HERE / 'proposals.csv').open()))
receipts = read('receipts.json')
assert [int(r['proposal']) for r in rows] == list(range(1,102))
assert len(receipts['proposals']) == 101
for row, receipt in zip(rows,receipts['proposals']):
    n = int(row['proposal'])
    assert receipt['proposal'] == n == receipt['reservation']['ordinal']
    started = any(x['status'] == 'complete' for x in receipt['transport_results'])
    if receipt['consumed_no_result']:
        started = receipt['consumed_no_result']['turn_started_event_present']
    assert started == (row['model_started'] == 'True')
    result = receipt['evaluation_summary']
    assert bool(result) == (row['outcome_recorded'] == 'True')
    if result:
        assert result['coverage']['evaluated_rows'] == int(row['result_rows']) == 48
        assert result['dispositions'].get('VALID',0) == int(row['valid_rows'])
        assert result['mp_coverage']['complete'] == 48
    assert bool(receipt['model_usage']) == (n != 96)
counts = {k:sum(r[k] == 'True' for r in rows) for k in
          ('reserved','model_started','returned_source','policy_evaluated','outcome_recorded')}
assert list(counts.values()) == [101,101,100,99,100], counts
historic = receipts['historical_counts']
assert historic['archive_entries'] - historic['archive_unique_sources'] == 20
assert historic['db_programs'] - historic['db_unique_sources'] == 20
for case in read('cases.json'):
    n = case['proposal']
    if not case['returned_source']:
        assert n == 96 and not case['policy_evaluated']
        continue
    parent = (HERE / f'P{n}/parent.py').read_text()
    child = (HERE / f'P{n}/child.py').read_text()
    answer = (HERE / f'P{n}/answer.txt').read_text()
    assert sha(parent) == case['parent_source_sha256']
    assert sha(child) == case['source_sha256']
    assert sha(answer) == case['answer_sha256']
    blocks = re.findall(r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE',answer,re.S)
    assert blocks, n
    replay = parent
    for old,new in blocks:
        assert replay.count(old) == 1, (n,'ambiguous or absent SEARCH')
        replay = replay.replace(old,new,1)
    assert replay == child, (n,'patch/source mismatch')
    history = read(f'P{n}/historical_evaluation.json')
    assert history['program_sha256'] == case['source_sha256']
    assert len(history['rows']) == 48
    for row in history['rows'].values():
        assert row['mp_complete'] is True
        if n == 45:
            assert row['execution_status'] == 'INVALID_POLICY' and row['action_counts'] == {}
        else:
            assert row['disposition'] == 'VALID'
    if n in (95,98):
        policy = HERE.parents[2] / f'src/p95p98/policies/p{n}.py'
        assert sha(policy.read_text()) == case['source_sha256']
manifest_path = HERE / 'SHA256.json'
for item in read('validator_entrypoints.json').values():
    if isinstance(item,dict):
        assert hashlib.sha256((HERE.parents[2]/item['public_path']).read_bytes()).hexdigest() == item['release_file_sha256']
if manifest_path.exists():
    for name,digest in read('SHA256.json').items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest, name
print(json.dumps(dict(status='PASS',counts=counts,migration_copies=20,
    patch_replays=[45,95,98],scientific_calls=0,validator_executions=0)))
