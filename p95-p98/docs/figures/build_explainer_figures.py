"""Build the loop/RMSD and cost-boundary explanatory diagrams.

The loop drawing is schematic, not a measured protein or experimental result.
Cost values are transcribed from the linked public closeout records.
"""
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from figure_style import *

def curve(ax,points,color,lw=3,alpha=1,style='-'):
    codes=[MplPath.MOVETO]+[MplPath.CURVE4]*(len(points)-1)
    ax.add_patch(PathPatch(MplPath(points,codes),facecolor='none',edgecolor=color,
        lw=lw,alpha=alpha,linestyle=style,capstyle='round'))

def loop_figure():
    fig=canvas('What loop modeling and RMSD mean',
        'A schematic guide to the search and the structural comparison.',(14,7.5))
    ax=diagram(fig)
    ax.set_position([.035,.14,.93,.67])
    ax.text(2,95,'A  Try connected loop shapes',fontsize=18,fontweight='bold')
    ax.text(54,95,'B  Compare matching atoms',fontsize=18,fontweight='bold')
    ax.plot([49,49],[10,94],color=GRID,lw=1)
    # Fixed scaffold is shared; only the loop takes alternative conformations.
    curve(ax,[(4,36),(0,20),(8,8),(17,21),(26,33),(28,15),(40,24),
        (49,33),(39,42),(41,59)],LIGHT_GRAY,6)
    for i,(h,col,a) in enumerate([(90,LIGHT_BLUE,.35),(75,LIGHT_BLUE,.55),(63,BLUE,1)]):
        curve(ax,[(4,36),(8,h),(34,h),(41,59)],col,4,a)
    ax.scatter([4,41],[36,59],s=85,c=INK,zorder=5)
    ax.text(4,29,'Fixed ends',fontsize=12,color=MUTED)
    ax.text(11,8,'Surrounding scaffold',fontsize=13,color=MUTED)
    ax.text(4,85,'Candidate loops',fontsize=14,color=BLUE)
    fig.text(.055,.082,'KIC closes each proposed loop; energy ranks candidates.',fontsize=12,color=MUTED)
    # Matched atoms on two schematic curves. No numerical energies or RMSDs.
    t=np.linspace(0,1,11)
    x=56+39*t
    ref_y=42+27*np.sin(np.pi*t)+3*np.sin(2*np.pi*t)
    mod_y=ref_y+np.sin(np.pi*t)*(8*np.sin(2*np.pi*t)+3)
    ax.plot(x,ref_y,color=GRAY,lw=3,label='Experimental loop')
    ax.plot(x,mod_y,color=BLUE,lw=3,label='Modeled loop')
    for xx,yy,zz in zip(x,ref_y,mod_y):
        ax.plot([xx,xx],[yy,zz],color=LIGHT_GRAY,lw=1.3,zorder=0)
    ax.scatter(x,ref_y,s=30,c=GRAY,zorder=3)
    ax.scatter(x,mod_y,s=30,c=BLUE,zorder=3)
    ax.plot([56,61],[83,83],color=BLUE,lw=3)
    ax.text(63,83,'Modeled',fontsize=13,va='center',color=BLUE)
    ax.plot([77,82],[83,83],color=GRAY,lw=3)
    ax.text(84,83,'Experimental',fontsize=13,va='center',color=GRAY)
    ax.text(55,28,r'RMSD = $\sqrt{\mathrm{mean}(d_i^2)}$',fontsize=20)
    ax.text(55,19,'Distances after alignment, in Å. Lower is closer.',fontsize=12,color=MUTED)
    ax.text(55,8,'Local: the loop region   •   Global: the whole protein',fontsize=12,color=MUTED)
    fig.text(.055,.037,'Lower energy does not necessarily mean a structure closer to the experiment.',fontsize=13,color=INK)
    save(fig,'loop_and_rmsd')

def cost_figure():
    fig=canvas('What each cost number counts',
        'Discovery, resource building, a modeling run and evaluation have separate ledgers.',(14,10.5))
    ax=diagram(fig)
    # A two-by-two sequence leaves enough room for the full accounting scope.
    box(ax,2,56,44,38,'1  Discover the programs',[
        'Once, before deployment',
        '380.437 route-CPU hours',
        '21,531,286 recorded LLM tokens',
        'P96 tokens missing; 0 paid API calls',
        'LLM waiting and money not reconciled'],fontsize=13)
    box(ax,54,56,44,38,'2  Build the fragment library',[
        'Once per protected input set',
        'CASP15: 148.44 CPU seconds',
        'Public 1L2Y example: 29.36 CPU seconds',
        'BENCH48 build cost not reconciled'],fontsize=13)
    box(ax,2,4,44,43,'3  Run a program on an input',[
        'Used in program-vs-NGK comparisons',
        'BENCH48 logical work: 16.11% / 25.13%',
        'BENCH48 route CPU: 17.84% / 26.66%',
        'Both pairs: P95 / P98, relative to NGK',
        'CASP15 P98: 6.66% / 151.50% CPU',
        'AlphaFold2 / ESMFold starts, vs NGK'],accent=True,fontsize=12.7)
    box(ax,54,4,44,43,'4  Check the outputs',[
        'Final structure-quality scoring',
        'MolProbity where performed',
        'Preflight and starting-model scoring',
        'Counted separately from method CPU',
        'CASP15 MolProbity was skipped'],fontsize=13)
    arrow(ax,(47,75),(52,75))
    arrow(ax,(76,54),(76,51))
    arrow(ax,(76,51),(24,51))
    arrow(ax,(24,51),(24,49))
    arrow(ax,(47,25),(52,25))
    fig.text(.055,.032,'Logical work is not seconds. CASP15 retains 156.18 s of earlier repair attempts separately.',fontsize=12.5,color=MUTED)
    save(fig,'cost_boundaries')

if __name__=='__main__':
    loop_figure()
    cost_figure()
