"""Full-precision native pose fingerprint; no dataset loader."""

def fingerprint(pose):
    from pyrosetta import rosetta
    rows=[]
    for i in range(1,pose.total_residue()+1):
        r=pose.residue(i);atoms=[]
        for a in range(1,r.natoms()+1):
            xyz=r.xyz(a);aid=rosetta.core.id.AtomID(a,i);dofs=[]
            for kind in (rosetta.core.id.DOF_Type.PHI,rosetta.core.id.DOF_Type.THETA,rosetta.core.id.DOF_Type.D):
                did=rosetta.core.id.DOF_ID(aid,kind)
                # A jump/root atom has no scalar PHI/THETA/D; query only valid DOFs.
                dofs.append(None if pose.atom_tree().atom(aid).is_jump() else pose.dof(did))
            atoms.append([r.atom_name(a),xyz.x,xyz.y,xyz.z,dofs])
        rows.append(dict(name=r.name(),chain=pose.chain(i),atoms=atoms,
            connections=[[c,r.connected_residue_at_resconn(c),r.residue_connection_conn_id(c)]
                         for c in range(1,r.n_possible_residue_connections()+1)],
            variants=[str(v) for v in r.type().variant_types()],
            mainchain=list(r.mainchain_torsions()),chi=list(r.chi())))
    stream=rosetta.std.ostringstream();pose.constraint_set().show_definition(stream,pose)
    return dict(sequence=pose.annotated_sequence(),fold_tree=str(pose.fold_tree()),residues=rows,
        jumps=[str(pose.jump(i)) for i in range(1,pose.num_jump()+1)],constraints=stream.str(),secstruct=pose.secstruct())

