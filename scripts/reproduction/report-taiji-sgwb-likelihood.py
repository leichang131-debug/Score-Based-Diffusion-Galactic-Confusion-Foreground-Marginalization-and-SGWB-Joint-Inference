#!/usr/bin/env python3
"""Render Stage 7 diagnostic from saved arrays, without likelihood evaluation."""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/taiji-sgwb/likelihood'


def render():
    s=np.load(OUT/'spectral-summary.npz');freq=s['frequency']
    cuts=np.flatnonzero(np.diff(freq)>1.5*np.median(np.diff(freq)))+1
    plotfreq=np.insert(freq,cuts,np.nan)
    with plt.rc_context({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8}):
        fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
        for i,name in enumerate('AET'):
            line,=axes[0].loglog(plotfreq,np.insert(np.sqrt(s['mean_model_auto'][i]),cuts,np.nan),ls='--',lw=1.4,label=name+' model')
            axes[0].loglog(plotfreq,np.insert(np.sqrt(s['mean_data_auto'][i]),cuts,np.nan),color=line.get_color(),alpha=.5,lw=.65,label=name+' data')
        axes[0].set(xlabel='Frequency [Hz]',ylabel='ASD [1/sqrt(Hz)]',title='A/E/T diagonal spectra\nAnnual summary of weekly matrices');axes[0].legend(ncol=2);axes[0].grid(alpha=.25)
        for low,high in ((.0235,.0265),(.047,.052)):axes[0].axvspan(low,high,color='grey',alpha=.15)
        axes[0].set_xlim(freq[0],.05)
        axes[1].semilogx(s['scan_omega0']/1e-12,s['scan_ll']-max(s['scan_ll']),'o-',ms=4)
        axes[1].axvline(1,color='k',ls='--',label='Injected amplitude')
        axes[1].set(xlabel='Omega0 / 1e-12 (reference: 1 mHz)',ylabel='Log likelihood - scan maximum',title='Conditional amplitude scan\nNoise and slope fixed; not a posterior')
        axes[1].xaxis.set_major_locator(FixedLocator([.3,.5,1,2,3]));axes[1].xaxis.set_major_formatter(FixedFormatter(['0.3','0.5','1','2','3']));axes[1].xaxis.set_minor_formatter(NullFormatter())
        axes[1].legend();axes[1].grid(alpha=.25)
        fig.savefig(OUT/'spectral-likelihood-check.png',dpi=180);plt.close(fig)
    print('Stage 7 diagnostic rendered from spectral-summary.npz; no likelihood recomputation.')

if __name__=='__main__':render()
