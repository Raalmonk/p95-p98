"""Source-only exports extracted from the evaluated observation host."""
import hashlib
import json
ENERGY_PROFILE = "ref2015_bb_hbond_pair_decomposition"
ATOMIC_NUMBERS = {symbol: i for i, symbol in enumerate(('X H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og').split())}

def _atomic_number(element):
    if element in ('D', 'T'):
        return 1
    if element not in ATOMIC_NUMBERS:
        raise ValueError('unrecognized source atom element: '+element)
    return ATOMIC_NUMBERS[element]


def export_source_pose(pose, *, backend):
    """All-atom, source-only serialization without scoring; bootstrap geometry."""
    rows, bindings = [], []
    info = pose.pdb_info()
    if info is None:
        raise ValueError('source PDB residue identity is required')
    for i in range(1, pose.total_residue()+1):
        residue = pose.residue(i)
        atoms, elements = {}, {}
        for a in range(1,residue.natoms()+1):
            name = residue.atom_name(a).strip()
            xyz = residue.xyz(a)
            atoms[name] = [float(xyz.x),float(xyz.y),float(xyz.z)]
            elements[name] = str(residue.atom_type(a).element())
        chain = str(info.chain(i))
        rows.append(dict(index=i,name=residue.name3(),chain=chain,atoms=atoms,elements=elements,
            atomic_numbers={name:_atomic_number(element) for name,element in elements.items()}))
        bindings.append(dict(pose_index=i,chain=chain,residue_id=str(info.number(i))+str(info.icode(i)).strip(),aa=pose.sequence()[i-1]))
    return dict(projection=backend.projection(pose),residues=rows,source_bindings=bindings)


def export_endpoint(pose, binding, *, backend, geometry_contract):
    """Source-only final export; unchanged v2 observer scores an isolated clone.

    backend = make_fixed_backend(already_initialized_pyrosetta). No target data
    is accessed here. All atoms are retained for exact geometry-contract joins.
    """
    r = backend.rosetta
    weights = {str(r.core.scoring.name_from_score_type(t)): float(backend.scorefxn.get_weight(t))
               for t in backend.scorefxn.get_nonzero_weighted_scoretypes()}
    weights_sha = hashlib.sha256(json.dumps(weights, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    expected = geometry_contract['source_projection']['sequence']
    observation = backend.integrated_observation(pose,
        local_indices=binding['local_energy_residues0'], expected_sequence=expected)
    residues = []
    for i in range(1, pose.total_residue()+1):
        residue = pose.residue(i)
        atoms, elements = {}, {}
        for a in range(1, residue.natoms()+1):
            name = residue.atom_name(a).strip()
            xyz = residue.xyz(a)
            atoms[name] = [float(xyz.x), float(xyz.y), float(xyz.z)]
            elements[name] = str(residue.atom_type(a).element())
        residues.append(dict(index=i, name=residue.name3(), chain=geometry_contract['bindings'][i-1]['chain'], atoms=atoms, elements=elements,
            atomic_numbers={name:_atomic_number(element) for name,element in elements.items()}))
    return dict(projection=backend.projection(pose), residues=residues, observation=observation,
        fixed_energy=dict(profile=ENERGY_PROFILE, weights=weights, weights_sha256=weights_sha,
            local_residues0=binding['local_energy_residues0'], global_residues0=binding['global_energy_residues0']))

