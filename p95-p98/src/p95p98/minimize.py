"""The evaluated local Cartesian MinMover, with explicit movable intervals.

Parameter values match Protein-InDelMaker kic_close.xml (SHA256
33d767aae302e00923cd08d475f679cacc6cbc3bccdfc770326d6a89b84bf2dd)
and the evaluated finite_minimize.rendered_xml interval adapter. No relax,
residue design, automatic bond declaration or implicit alternate method.
"""
import xml.etree.ElementTree as ET

def render(loops):
    root = ET.Element('ROSETTASCRIPTS')
    scores = ET.SubElement(root, 'SCOREFXNS')
    score = ET.SubElement(scores, 'ScoreFunction', name='ref15sfxn_cart', weights='ref2015.wts')
    ET.SubElement(score, 'Reweight', scoretype='pro_close', weight='0.0')
    ET.SubElement(score, 'Reweight', scoretype='cart_bonded', weight='0.625')
    movers = ET.SubElement(root, 'MOVERS')
    mover = ET.SubElement(movers, 'MinMover', name='min_cart', scorefxn='ref15sfxn_cart', chi='true', bb='1', cartesian='T')
    move = ET.SubElement(mover, 'MoveMap', name='move_loop')
    ET.SubElement(move, 'Span', begin='1', end='99999', chi='false', bb='false')
    for loop in loops:
        ET.SubElement(move, 'Span', begin=str(loop['start']), end=str(loop['stop']), chi='true', bb='true')
    protocol = ET.SubElement(root, 'PROTOCOLS')
    ET.SubElement(protocol, 'Add', mover='min_cart')
    return ET.tostring(root, encoding='unicode')
