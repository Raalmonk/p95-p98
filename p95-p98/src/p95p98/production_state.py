"""Restore retained full-precision native atoms, never rerun a native mover."""
import re
from .controller import PreparationPending


def restore_state_pose(source, parent, saved):
    pose = parent.payload['pose'].clone()
    names = saved.get('residue_type_names')
    if names is not None:
        if len(names) != pose.size():
            raise PreparationPending('Retained endpoint sequence length changed')
        types = pose.residue_type_set_for_pose()
        for i, name in enumerate(names, 1):
            if pose.residue(i).name() != name:
                residue = source.r.core.conformation.ResidueFactory.create_residue(types.name_map(name))
                pose.replace_residue(i, residue, False)
    tree = saved.get('fold_tree', saved['projection']['fold_tree'])
    if str(pose.fold_tree()) != tree:
        matches = re.findall(r'EDGE\s+(\d+)\s+(\d+)\s+(-?\d+)', tree)
        remainder = re.sub(r'EDGE\s+\d+\s+\d+\s+-?\d+', '', tree).replace('FOLD_TREE', '').strip()
        if not matches or remainder:
            raise PreparationPending('Retained nonstandard FoldTree needs exact edge restoration')
        native = source.r.core.kinematics.FoldTree()
        for a,b,label in matches:
            native.add_edge(int(a),int(b),int(label))
        if not native.check_fold_tree() or str(native) != tree:
            raise PreparationPending('Retained FoldTree reconstruction differs')
        pose.fold_tree(native)
    if 'secstruct' in saved:
        for i, code in enumerate(saved['secstruct'], 1):
            pose.set_secstruct(i, code)
    for i,a,xyz in saved['atoms']:
        if a > pose.residue(i).natoms():
            raise PreparationPending('Retained residue atom inventory differs')
        pose.set_xyz(source.r.core.id.AtomID(a,i), source.r.numeric.xyzVector_double_t(*xyz))
    if source.backend.projection(pose) != saved['projection']:
        raise PreparationPending('Retained full atom/topology projection differs; do not resample')
    source.set_rng(saved['rng'])
    return pose
