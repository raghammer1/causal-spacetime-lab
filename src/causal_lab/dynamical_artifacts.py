"""Scientific figures with explicit quantum/measurement/control distinctions."""
from __future__ import annotations
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .dynamical_graphs import GraphCatalog,static_controls


def write_tables(out,rows,summary):
    out=Path(out)
    with (out/'advancement.csv').open('w',newline='') as f:
        fields=['N','cell','attempted','valid','successes','C','L','T','D','lower','upper','assessment']
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for r in summary['cells']:
            writer.writerow({**{k:r[k] for k in fields if k in r},**r['component_successes'],
                'lower':r['cp_family_bounds'][0],'upper':r['cp_family_bounds'][1]})
    with (out/'structure.csv').open('w',newline='') as f:
        fields=['N','cell','preparation','batch','replicate','age','connected_probability','expected_edge_count',
                'edge_count_variance','expected_components','expected_triangles','expected_clustering',
                'occupation_contrast','tv_density','tv_product','tv_count','tv_degree']
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for row in rows:
            for s in row.get('structure',[]):
                w.writerow({**{k:row[k] for k in fields[:5]},'age':s['age'],
                    **{k:s['observed'][k] for k in fields[6:13]},
                    **{'tv_'+key:s['nulls'][key]['tv'] for key in ('density','product','count','degree')}})


def _save(fig,out,name):
    fig.savefig(Path(out)/name,dpi=155,bbox_inches='tight',metadata={'Software':'causal-spacetime-lab Experiment 7'})
    plt.close(fig)


def _first(rows,n,cell,prep):
    return next((r for r in rows if r['N']==n and r['cell']==cell and r['preparation']==prep and r.get('status')=='ok'),None)


def write_figures(out,rows,equilibrium,summary):
    out=Path(out);n=max(r['N'] for r in rows);cells=sorted({r['cell'] for r in rows})
    colors={'Splus':'#0072B2','Sempty':'#009E73','E':'#D55E00'}
    plt.rcParams.update({'font.size':8,'axes.titlesize':9,'figure.titlesize':12})
    fig,axes=plt.subplots(3,len(cells),figsize=(max(5,2.6*len(cells)),8),squeeze=False,layout='constrained')
    for j,c in enumerate(cells):
        for prep in colors:
            selected=[r for r in rows if r['N']==n and r['cell']==c and r['preparation']==prep and r.get('status')=='ok']
            if not selected:continue
            x=[s['age'] for s in selected[0]['structure']]
            for k,key in enumerate(('expected_edge_count','connected_probability','occupation_contrast')):
                values=np.array([[s['observed'][key] for s in r['structure']] for r in selected])
                axes[k,j].plot(x,values.mean(0),'.-',color=colors[prep],label=prep)
                if len(values)>1:axes[k,j].fill_between(x,values.min(0),values.max(0),color=colors[prep],alpha=.12)
        params=selected[0]['parameters'];axes[0,j].set_title(f"μ={params['mu']:g}, Γ={params['Gamma']:g}")
        for k in range(3):axes[k,j].set_xlabel('External time')
    for ax,label in zip(axes[:,0],('Expected active links','Born probability connected','Labeled occupation range')):ax.set_ylabel(label)
    axes[0,0].legend();fig.suptitle(f'Unconditioned quantum evolution, N={n}\nE: independent-preparation mean and full range, not confidence bands')
    _save(fig,out,'evolution.png')

    fig,axes=plt.subplots(2,len(cells),figsize=(max(5,2.6*len(cells)),5.8),squeeze=False,layout='constrained')
    for j,c in enumerate(cells):
        r=_first(rows,n,c,'E');a=np.load(out/r['array_file']);catalog=GraphCatalog(n)
        for k,graph in enumerate(a['born_draws'][3,:2]):
            xy=np.column_stack((np.cos(np.arange(n)*2*np.pi/n),np.sin(np.arange(n)*2*np.pi/n)))
            ax=axes[k,j]
            for u,v in catalog.edges:
                if catalog.adjacency[graph,u,v]:ax.plot(xy[[u,v],0],xy[[u,v],1],color='#666666',lw=1.5)
            ax.scatter(xy[:,0],xy[:,1],s=90,c=colors['E'],zorder=3)
            for u in range(n):ax.text(*xy[u],str(u),ha='center',va='center',color='white',fontsize=8)
            ax.set_aspect('equal');ax.axis('off');ax.set_title(f"cell{c}, draw{k+1}\nP(G)={a['full_born'][3,graph]:.4f}; components={catalog.components[graph]}")
    fig.suptitle(f'First two unselected Born measurements at age2, N={n}\nCircular drawing is a combinatorial layout, not physical position')
    _save(fig,out,'born_graph_examples.png')

    fig,axes=plt.subplots(3,len(cells),figsize=(max(5,2.6*len(cells)),7.5),squeeze=False,layout='constrained')
    vmax=0
    mats=[]
    for c in cells:
        e=_first(rows,n,c,'E');s=_first(rows,n,c,'Splus');a=np.load(out/e['array_file']);b=np.load(out/s['array_file'])
        mats.append([b['full_response'][3],a['full_response'][3],a['initial_frozen_response'][3]])
        vmax=max(vmax,max(float(x[~np.eye(n,dtype=bool)].max()) for x in mats[-1]))
    for j,c in enumerate(cells):
        for k in range(3):
            matrix=mats[j][k].copy();np.fill_diagonal(matrix,np.nan)
            im=axes[k,j].imshow(matrix,vmin=0,vmax=vmax,cmap='magma');axes[k,j].set_title(f'cell{c}');axes[k,j].set_xlabel('Target label')
    for ax,label in zip(axes[:,0],('Splus full','First E full','Same E initially frozen')):ax.set_ylabel(label+'\nSource label')
    fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.6,label='Target trace distance')
    fig.suptitle(f'Operational Y-intervention response at age2 + delay.25, N={n}\nNo graph threshold or layout enters these quantum measurements')
    _save(fig,out,'operational_response_maps.png')

    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
    for j,(null,label) in enumerate((('density','Density-matched'),('product','Marginal-product'),('degree','Full degree-vector matched'))):
        for c in cells:
            selected=[r for r in rows if r['N']==n and r['cell']==c and r['preparation']=='E' and r.get('status')=='ok']
            tv=[r['structure'][3]['nulls'][null]['tv'] for r in selected]
            diff=[r['structure'][3]['observed']['connected_probability']-r['structure'][3]['nulls'][null]['properties']['connected_probability'] for r in selected]
            axes[j].scatter(tv,diff,s=12,alpha=.65,label=f'cell{c}')
        axes[j].axhline(0,color='gray',lw=.6);axes[j].set_title(label);axes[j].set_xlabel('Exact graph-law total variation');axes[j].set_ylabel('Born minus null connectivity')
    axes[0].legend(ncol=2,fontsize=6);fig.suptitle(f'Exact age2 graph-law comparisons, N={n}\nEach dot is an independent preparation; law differences are not evidence of a manifold')
    _save(fig,out,'graph_null_comparisons.png')

    fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
    table=summary['cells'];x=np.arange(len(table))
    for k,condition in enumerate(('C','L','T','D')):
        axes[0].bar(x+(k-1.5)*.2,[r['component_successes'][condition]/r['attempted'] for r in table],width=.19,label=condition)
    mean=np.array([r['successes']/r['attempted'] for r in table]);lo=np.array([r['cp_family_bounds'][0] for r in table]);hi=np.array([r['cp_family_bounds'][1] for r in table])
    axes[1].errorbar(x,mean,yerr=np.array([mean-lo,hi-mean]),fmt='o',capsize=3,color='#0072B2');axes[1].axhline(.8,c='#D55E00',ls='--')
    for ax in axes:
        ax.set_xticks(x,[f"{r['N']}/c{r['cell']}" for r in table],rotation=60);ax.set_xlabel('N / parameter cell');ax.set_ylim(-.02,1.05)
    axes[0].set_ylabel('Descriptive component success fraction');axes[0].legend(ncol=4)
    axes[1].set_ylabel('Joint success probability; exact familywise bounds')
    fig.suptitle(f"Registered necessary-property screen: {summary['decision']}\nC connectivity; L concentrated response; T stability; D gain over initially frozen links")
    _save(fig,out,'registered_decision.png')

    catalog=GraphCatalog(n);static=np.load(out/'arrays'/f'static_N{n}.npz');controls=static_controls(catalog)
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
    delays=np.array([0,.05,.1,.25,.5,1,2])
    for j,name in enumerate(('chain','complete','matching')):
        graph=controls[name];response=static['response'][graph];distance=catalog.distance[graph]
        for d in sorted(set(distance.ravel())- {0}):
            y=response[:,distance==d].mean(1);axes[j].plot(delays,y,'.-',label='disconnected' if d<0 else f'd={d}')
        axes[j].set_title(name+' (supplied graph)');axes[j].set_xlabel('Response delay');axes[j].set_ylabel('Mean target trace distance');axes[j].legend(fontsize=7)
    fig.suptitle(f'Fresh-product static TFIM controls, N={n}\nDistances are supplied combinatorial truth; no physical velocity is inferred')
    _save(fig,out,'supplied_propagation_controls.png')

    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for size in sorted({e['N'] for e in equilibrium}):
        eq=[e for e in equilibrium if e['N']==size]
        axes[0].plot([e['cell'] for e in eq],[e['properties']['connected_probability'] for e in eq],'.-',label=f'ground N={size}')
    for beta in (.5,2.):
        eq=[e for e in equilibrium if e['N']==4]
        axes[0].plot([e['cell'] for e in eq],[next(t for t in e['thermal'] if t['beta']==beta)['properties']['connected_probability'] for e in eq],'.--',label=f'Gibbs N4 β={beta}')
    measurements=[r for r in rows if 'nonselective_measurement_tv' in r]
    axes[1].bar([r['cell'] for r in measurements],[r['nonselective_measurement_tv'] for r in measurements],color='#009E73')
    axes[0].set_xlabel('Parameter cell');axes[0].set_ylabel('Born connectivity');axes[0].legend(fontsize=7)
    axes[1].set_xlabel('Parameter cell');axes[1].set_ylabel('TV of future measured vs unmeasured Born law')
    fig.suptitle('Equilibrium and measurement are separate preparations\nGround/Gibbs states do not result from unitary cooling; N4 dephasing includes every outcome')
    _save(fig,out,'equilibrium_and_measurement.png')
