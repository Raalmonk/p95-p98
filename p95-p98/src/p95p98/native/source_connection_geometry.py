"""Explicit, source-bound peptide adjacency correction; legacy defaults untouched.

Only independently recorded chain/TER/paired terminal boundaries are removed.
Numbering discontinuities and existing long bonds are never exemptions. This
module reads retained Cartesian states; it never loads Rosetta or evaluates an
energy function. Candidate state data cannot redefine the source contract.
"""
from copy import deepcopy
import hashlib
import json
import math
import struct

PROFILE = 'source_chain_boundaries_v1'
STANDARD = {'ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE','LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL','CYD','CYX','HID','HIE','HIP'}

def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def distance(a,b):
    value=math.sqrt(math.fsum((float(x)-float(y))**2 for x,y in zip(a,b)))
    if len(a)!=3 or len(b)!=3 or not math.isfinite(value):raise ValueError('Invalid Cartesian coordinate')
    return value

def _residues(export):
    rows=export['residues']
    if [r['index'] for r in rows]!=list(range(1,len(rows)+1)):raise ValueError('Explicit consecutive pose indices required')
    return rows

def _coordinate_hash(export):
    payload=[]
    for row,topology in zip(export['residues'],export['projection']['topology']):
        for atom in topology[1]:payload.append(struct.pack('!ddd',*row['atoms'][atom.strip()]))
    return hashlib.sha256(b''.join(payload)).hexdigest()

def build_connection_contract(*, source_pdb, source_export, bindings, movable_loop, source_sha256,
                              original_source_pdb,original_source_sha256):
    """Freeze source chain/TER evidence before evaluating candidate geometry.

    source_pdb is the already-bound input/loader projection, never a candidate
    serialization. source_sha256 identifies those exact PDB bytes. The original
    unprojected source identity can be retained by the host beside this contract.
    """
    if hashlib.sha256(source_pdb).hexdigest()!=source_sha256:raise ValueError('Source bytes differ')
    if hashlib.sha256(original_source_pdb).hexdigest()!=original_source_sha256:raise ValueError('Original source bytes differ')
    rows=_residues(source_export)
    if _coordinate_hash(source_export)!=source_export['projection']['coordinates_sha256']:raise ValueError('Source Cartesian identity differs')
    if [b['pose_index'] for b in bindings]!=list(range(1,len(rows)+1)):raise ValueError('Source binding differs')
    keys=[(b['chain'],b['residue_id'].strip()) for b in bindings]
    if len(set(keys))!=len(keys):raise ValueError('Ambiguous source residue identifiers')
    key_set=set(keys);segments={};atoms={};segment=0;serials={};source_lines=source_pdb.decode().splitlines()
    for line in source_lines:
        if line.startswith('ENDMDL'):break
        if line.startswith('TER'):segment+=1
        if not line.startswith(('ATOM  ','HETATM')):continue
        key=(line[21:22],line[22:27].strip())
        if key not in key_set or line[16:17] not in (' ','A'):continue
        if key in segments and segments[key]!=segment:raise ValueError('Residue crosses source TER boundary')
        segments[key]=segment
        atom=line[12:16].strip()
        try:serials[int(line[6:11])]=(key,atom)
        except ValueError:raise ValueError('Invalid source atom serial')
        if atom in ('N','CA','C'):
            xyz=[float(line[i:i+8]) for i in (30,38,46)]
            if (key,atom) in atoms and atoms[(key,atom)]!=xyz:raise ValueError('Ambiguous source backbone atom')
            atoms[(key,atom)]=xyz
    if set(segments)!=key_set:raise ValueError('Incomplete source chain/TER evidence')
    topology=source_export['projection']['topology']
    sequence=source_export['projection']['sequence']
    if sequence!=''.join(b['aa'] for b in bindings):raise ValueError('Source sequence mismatch')
    for r,b,key in zip(rows,bindings,keys):
        if r['chain']!=b['chain']:raise ValueError('Source chain mismatch')
        for atom in ('N','CA','C'):
            if (key,atom) not in atoms or distance(atoms[(key,atom)],r['atoms'][atom])>1e-8:
                raise ValueError('Source loaded backbone is not exact input backbone')
    original_lines=original_source_pdb.decode().splitlines();original_serials={};original_segments={};original_atoms={};original_segment=0
    for line in original_lines:
        if line.startswith('ENDMDL'):break
        if line.startswith('TER'):original_segment+=1
        if line.startswith(('ATOM  ','HETATM')):
            key=(line[21:22],line[22:27].strip());atom=line[12:16].strip()
            original_serials[int(line[6:11])]=(key,atom)
            if key in key_set and line[16:17] in (' ','A'):
                if key in original_segments and original_segments[key]!=original_segment:raise ValueError('Ambiguous original source residue mapping')
                original_segments[key]=original_segment
                if atom in ('N','CA','C'):original_atoms[(key,atom)]=[float(line[j:j+8]) for j in (30,38,46)]
    if set(original_segments)!=key_set:raise ValueError('Original source mapping unavailable after projection')
    for key in keys:
        for atom in ('N','CA','C'):
            if (key,atom) not in original_atoms or original_atoms[(key,atom)]!=atoms[(key,atom)]:raise ValueError('Original source mapping/coordinates differ')
    boundaries=[];unresolved=[]
    for i in range(1,len(rows)):
        a,b=bindings[i-1:i+1];reasons=[]
        if a['chain']!=b['chain']:reasons.append('SOURCE_CHAIN_ID_BOUNDARY')
        if original_segments[keys[i-1]]!=original_segments[keys[i]]:reasons.append('SOURCE_TER_BOUNDARY')
        if 'CtermProteinFull' in topology[i-1][0] and 'NtermProteinFull' in topology[i][0]:reasons.append('SOURCE_PAIRED_PROTEIN_TERMINI')
        d=distance(rows[i-1]['atoms']['C'],rows[i]['atoms']['N'])
        if reasons:
            independent=any(x in reasons for x in ('SOURCE_CHAIN_ID_BOUNDARY','SOURCE_TER_BOUNDARY'))
            if not independent or 'SOURCE_PAIRED_PROTEIN_TERMINI' not in reasons:
                raise ValueError('Boundary needs independent source chain/TER evidence and paired native termini')
            if rows[i-1]['name'] not in STANDARD or rows[i]['name'] not in STANDARD:
                raise ValueError('Unsupported boundary residue chemistry; retain legacy observation')
            allowed_patches={'NtermProteinFull','CtermProteinFull','disulfide'}
            if any(p not in allowed_patches for t in topology[i-1:i+1] for p in t[0].split(':')[1:]):
                raise ValueError('Unsupported patched boundary chemistry')
            boundaries.append(dict(residues=[i,i+1],reasons=reasons,source_distance_A=d))
        elif not 1.0<=d<=1.7:
            unresolved.append(dict(residues=[i,i+1],source_distance_A=d,
                source_residue_ids=[a['residue_id'],b['residue_id']],
                label='PREEXISTING_UNRESOLVED_SOURCE_CONNECTION',exempt=False,
                intersects_movable_loop=bool({i,i+1}&set(movable_loop))))
    boundary_atoms={(keys[i-1],'C') for b in boundaries for i in b['residues'][:1]}|{(keys[j-1],'N') for b in boundaries for j in b['residues'][1:]}
    # Chemical declarations are read from the unstripped original input. A
    # loader projection may legitimately omit LINK/CONECT and cannot prove absence.
    explicit_edges=[]
    for line in original_lines:
        if line.startswith('LINK  '):
            edge=(((line[21:22],line[22:27].strip()),line[12:16].strip()),((line[51:52],line[52:57].strip()),line[42:46].strip()))
            explicit_edges.append(edge)
        elif line.startswith('CONECT'):
            numbers=[int(line[i:i+5]) for i in range(6,len(line),5) if line[i:i+5].strip()]
            if numbers and numbers[0] in original_serials:
                explicit_edges.extend((original_serials[numbers[0]],original_serials[x]) for x in numbers[1:] if x in original_serials)
    for edge in explicit_edges:
        if edge[0][0]!=edge[1][0] and any(atom in boundary_atoms for atom in edge):
            raise ValueError('Explicit LINK/CONECT backbone chemistry conflicts with boundary correction')
    value=dict(profile=PROFILE,source_sha256=source_sha256,
        original_source_sha256=original_source_sha256,
        source_projection=source_export['projection'],bindings=bindings,
        source_residue_names=[r['name'] for r in rows],
        source_explicit_chemical_edges=explicit_edges,
        movable_loop=sorted(set(movable_loop)),removed_peptide_boundaries=boundaries,
        preexisting_unresolved_connections=unresolved,gap_exemptions_enabled=False)
    return dict(value,contract_sha256=identity(value))

def _validate(export,contract):
    if contract.get('profile')!=PROFILE or contract.get('gap_exemptions_enabled') is not False:raise ValueError('Unsupported source geometry profile')
    if identity({k:v for k,v in contract.items() if k!='contract_sha256'})!=contract['contract_sha256']:raise ValueError('Source contract changed')
    rows=_residues(export);projection=export['projection'];source=contract['source_projection']
    if _coordinate_hash(export)!=projection['coordinates_sha256']:raise ValueError('Candidate Cartesian identity differs')
    if len(rows)!=len(contract['bindings']):raise ValueError('Candidate residue count differs')
    for key in ('sequence','topology','fold_tree'):
        if projection[key]!=source[key]:raise ValueError('Candidate '+key+' differs from frozen source')
    for r,b,topology,name in zip(rows,contract['bindings'],source['topology'],contract['source_residue_names']):
        if r['name']!=name:raise ValueError('Candidate residue identity differs')
        if r['chain']!=b['chain'] or set(r['atoms'])!=set(n.strip() for n in topology[1]):raise ValueError('Candidate atom/chain mapping differs')
        for xyz in r['atoms'].values():distance(xyz,xyz)
    return rows

def correct_exported_observation(export,legacy_observation,contract):
    """Recompute affected geometry only; preserve energy and legacy evidence."""
    import numpy as np
    from .numerics import geometry_feedback
    rows=_validate(export,contract);n=len(rows)
    removed={tuple(x['residues']) for x in contract['removed_peptide_boundaries']}
    old=deepcopy(legacy_observation);result=deepcopy(old)
    old_cn={tuple(x['residues']):x for x in old['expected_peptide_bonds']}
    if set(old_cn)!={(i,i+1) for i in range(1,n)}:raise ValueError('Legacy adjacency inventory differs')
    cn=[];errors=[]
    for i,row in enumerate(rows,1):
        atoms=row['atoms']
        errors.extend([distance(atoms['N'],atoms['CA'])-1.458,distance(atoms['CA'],atoms['C'])-1.525])
        if i<n and (i,i+1) not in removed:
            d=distance(atoms['C'],rows[i]['atoms']['N'])
            if abs(d-old_cn[(i,i+1)]['distance_A'])>1e-8:raise ValueError('Retained CN observation differs from coordinates')
            cn.append(dict(residues=[i,i+1],distance_A=d,outside_A=max(1-d,d-1.7,0.)))
            errors.append(d-1.329)
    # Existing custom-contact numerator excludes every adjacent pose pair.
    # Restore all heavy contacts only for the independently disconnected pairs.
    heavy=lambda r:[(a,p) for a,p in r['atoms'].items() if r['elements'].get(a) not in ('H','X') and not a.startswith('H') and not a.startswith('VRT')]
    heavy_count=sum(len(heavy(r)) for r in rows)
    added_contact_count=0;added_extreme=[]
    extreme_keys={tuple(sorted(tuple(x) for x in e['atoms'])) for e in old['extreme_contacts']}
    atom_orders=[{name.strip():j for j,name in enumerate(t[1],1)} for t in export['projection']['topology']]
    for i,j in sorted(removed):
        a,b=rows[i-1],rows[j-1]
        for _,p in heavy(a):
            for _,q in heavy(b):
                if distance(p,q)<1.8:added_contact_count+=1
        # Removing C(i)-N(j) removes these length-one/two graph exclusions.
        # Standard residue backbone chemistry is checked when contract is built;
        # other real inter-residue chemistry and all existing contacts are kept.
        pairs=[('C','N'),('CA','N'),('O','N'),('OXT','N'),('C','CA')]
        if b['name']=='PRO':pairs.append(('C','CD'))
        for first,second in pairs:
            if first not in a['atoms'] or second not in b['atoms']:continue
            d=distance(a['atoms'][first],b['atoms'][second])
            if d>=.5:continue
            key=tuple(sorted(((i,atom_orders[i-1][first]),(j,atom_orders[j-1][second]))))
            if key not in extreme_keys:
                added_extreme.append(dict(atoms=[list(x) for x in key],distance_A=d,deficit_A=.5-d))
                extreme_keys.add(key)
    if removed:
        result.update(expected_peptide_bonds=cn,
            backbone_bond_rms_error_A=float(np.sqrt(np.mean(np.asarray(errors)**2))),
            custom_short_contact_score=old['custom_short_contact_score']+1000.*added_contact_count/heavy_count,
            extreme_contacts=old['extreme_contacts']+added_extreme)
        result['valid']=bool(all(result.get(k) is True for k in ('sequence_exact','required_heavy_complete','finite_coordinates')) and
            all(x['outside_A']==0 for x in cn) and result['backbone_bond_rms_error_A']<=.05 and result['custom_short_contact_score']<=30 and not result['extreme_contacts'])
        result['geometry_feedback']=geometry_feedback(result)
    result['source_connection_geometry']=dict(profile=PROFILE,contract_sha256=contract['contract_sha256'],
        removed_peptide_boundaries=deepcopy(contract['removed_peptide_boundaries']),
        preexisting_unresolved_connections=deepcopy(contract['preexisting_unresolved_connections']),
        gap_exemptions_enabled=False,added_custom_contacts=added_contact_count,added_extreme_contacts=added_extreme,
        legacy_valid=old['valid'],legacy_geometry_feedback=old.get('geometry_feedback'),
        legacy_backbone_bond_rms_error_A=old['backbone_bond_rms_error_A'],legacy_custom_short_contact_score=old['custom_short_contact_score'],
        legacy_expected_peptide_bonds=old['expected_peptide_bonds'])
    return result

class SourceConnectionBackend:
    """Trusted-host opt-in, installed before SourceObservationBackendV2.

    export_state must export the retained real payload, never candidate reports.
    The caller must freeze/verify the source contract before issuing actions.
    """
    def __init__(self,backend,*,contract,export_state,expected_contract_sha256):
        if contract['contract_sha256']!=expected_contract_sha256:raise ValueError('Unbound source contract')
        self.backend=backend;self.contract=deepcopy(contract);self.export_state=export_state;self.observations={}

    def __getattr__(self,name):return getattr(self.backend,name)

    def raw_observation(self,handle):
        if handle not in self.observations:
            self.observations[handle]=correct_exported_observation(self.export_state(handle),self.backend.raw_observation(handle),self.contract)
        return deepcopy(self.observations[handle])

    def controller_observation(self,handle):
        value=deepcopy(self.backend.controller_observation(handle));raw=self.raw_observation(handle)
        value['valid']=raw['valid'];value['diagnostics'].update(bond_rms_A=raw['backbone_bond_rms_error_A'],custom_contact_score=raw['custom_short_contact_score'],peptide_violation_count=sum(x['outside_A']>0 for x in raw['expected_peptide_bonds']),extreme_contact_count=len(raw['extreme_contacts']))
        return value

    def check_delivery(self,handle):return self.raw_observation(handle)['valid']

def adapt_backend(backend,*,profile=None,**kwargs):
    if profile is None:return backend
    if profile!=PROFILE:raise ValueError('Unknown source connection profile')
    return SourceConnectionBackend(backend,**kwargs)
