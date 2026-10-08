"""Shared, deterministic style for the NGNGK documentation figures."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent
INK = '#18313F'
MUTED = '#5E6D77'
BLUE = '#096DAA'
LIGHT_BLUE = '#79B4D4'
PALE = '#EAF4F9'
GRAY = '#78838A'
LIGHT_GRAY = '#B7C0C5'
GRID = '#E3E9EC'
PAPER = '#FFFFFF'

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':13,
    'text.color':INK, 'axes.labelcolor':INK, 'xtick.color':MUTED,
    'ytick.color':MUTED, 'axes.edgecolor':GRID, 'axes.spines.top':False,
    'axes.spines.right':False, 'svg.fonttype':'none', 'savefig.facecolor':PAPER,
    'figure.facecolor':PAPER, 'axes.facecolor':PAPER})

def canvas(title, subtitle='', size=(14,8)):
    fig=plt.figure(figsize=size)
    fig.text(.055,.95,title,fontsize=25,fontweight='bold',va='top')
    if subtitle: fig.text(.055,.887,subtitle,fontsize=13,color=MUTED,va='top')
    return fig

def diagram(fig):
    ax=fig.add_axes([.035,.04,.93,.78])
    ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
    return ax

def box(ax,x,y,w,h,title,body=(),accent=False,fontsize=13):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.7,rounding_size=1.2',
        facecolor=PALE if accent else '#F5F7F8',edgecolor=LIGHT_BLUE if accent else GRID,lw=1.2))
    ax.text(x+2,y+h-3,title,fontsize=15,fontweight='bold',va='top',color=BLUE if accent else INK)
    for i,line in enumerate(body): ax.text(x+2,y+h-11-i*5.8,line,fontsize=fontsize,va='top',color=INK)

def arrow(ax,a,b,label='',color=MUTED,rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=15,lw=1.5,
        color=color,connectionstyle=f'arc3,rad={rad}',shrinkA=2,shrinkB=2))
    if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+2,label,fontsize=12,color=color,ha='center')

def save(fig,name):
    fig.savefig(OUT/f'{name}.svg',metadata={'Date':None,'Creator':'NGNGK documentation figure builder'})
    fig.savefig(OUT/f'{name}.png',dpi=180)
    plt.close(fig)
