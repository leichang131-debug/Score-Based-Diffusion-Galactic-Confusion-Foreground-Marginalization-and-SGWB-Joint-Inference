#!/usr/bin/env python3
"""Regenerate a compact response diagnostic from the saved cache only."""
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import h5py
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]


def main():
    with h5py.File(ROOT/"data/processed/taiji-sgwb/response/response.h5","r") as h:
        frequency=h["f_est"][()]
        mean=h["orf"][()].mean(axis=2)
    cuts=np.flatnonzero(np.diff(frequency)>1.5*np.median(np.diff(frequency)))+1
    with plt.rc_context({"font.size":11,"axes.titlesize":13,"axes.labelsize":12}):
        fig,ax=plt.subplots(figsize=(8,5))
        for i,label in enumerate(["A","E","T"]):
            ax.loglog(np.insert(frequency,cuts,np.nan),np.insert(mean[i,i].real,cuts,np.nan),label=label)
        for low,high in [(0.0235,0.0265),(0.047,0.05)]:
            ax.axvspan(low,high,color="grey",alpha=.2)
        ax.set(xlabel="Frequency (Hz)",ylabel="Mean auto ORF",
               title="Original isotropic response (nside=14)\n52 weekly segments; shaded bands excluded",
               xlim=(frequency[0],0.05))
        ax.grid(True,which="both",alpha=.3);ax.legend();fig.tight_layout()
        target=ROOT/"results/taiji-sgwb/response/orf-auto.png"
        fig.savefig(target,dpi=180,bbox_inches="tight");plt.close(fig)
    print("Regenerated diagnostic from the saved response cache; no response calculation or inference.")


if __name__=="__main__":main()
