#!/usr/bin/env python3
"""Diagnostic trace from actual short-chain arrays; not posterior visualization."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/taiji-sgwb/template-short-chain'


def main():
    data=np.load(OUT/'resume/chain-arrays.npz');steps=np.arange(1,9)
    with plt.rc_context({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'legend.fontsize':8,'xtick.labelsize':9,'ytick.labelsize':9}):
        fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
        ll=data['log_like'][:,0,:];offset=float(ll.max())
        axes[0].plot(steps,(ll-offset)[:,::4],alpha=.35,lw=.7)
        axes[0].plot(steps,np.median(ll,axis=1)-offset,color='k',label='Walker median')
        axes[0].set(xlabel='Saved ensemble step',ylabel='Cold log likelihood - observed maximum',title='Cold walkers: likelihood trace');axes[0].legend()
        omega=data['chain_sgwb'][:,0,:,0,0]/1e-12
        axes[1].plot(steps,omega[:,::4],alpha=.45,lw=.8)
        axes[1].axhline(1,color='k',ls='--',label='Injected amplitude')
        axes[1].set(xlabel='Saved ensemble step',ylabel='Omega0 / 1e-12',title='Prior-start amplitude trace\nNot a converged posterior');axes[1].legend()
        for i in range(6):axes[2].plot(steps,data['betas'][:,i],'.-',label=f'Temperature {i}')
        axes[2].set(xlabel='Saved ensemble step',ylabel='Inverse temperature (beta)',title='Original adaptive ladder');axes[2].legend(ncol=2)
        for ax in axes:
            ax.axvline(4.5,color='red',ls=':',lw=1,label='Process restart')
            ax.set_xticks(steps);ax.grid(alpha=.2)
        fig.suptitle('Original template: 4 saved steps + fresh-process continuation for 4 steps',fontsize=12)
        fig.savefig(OUT/'short-chain-traces.png',dpi=170);plt.close(fig)
    print('Rendered actual eight-step traces; no posterior/convergence claim or likelihood rerun.')

if __name__=='__main__':main()
