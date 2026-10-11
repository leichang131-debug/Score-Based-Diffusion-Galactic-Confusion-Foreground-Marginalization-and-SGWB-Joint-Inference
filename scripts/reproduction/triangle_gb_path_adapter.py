"""External kernel hook for original author-specific HDF5 paths; notebook source stays unchanged."""
import json
from pathlib import Path
import h5py
ROOT=Path(__file__).resolve().parents[2]
MAPPING={
 '/Users/taijidatacenter/workspace/TDCData/0_1_VGB_TDIXYZ.h5': ROOT/'data/raw/triangle-gb/0_1_VGB_TDIXYZ.h5',
 '/Users/taijidatacenter/workspace/TDCData/0_1_VGB_parameters.h5': ROOT/'data/raw/triangle-gb/0_1_VGB_parameters.h5',
 '/Users/taijidatacenter/Downloads/LDCData/LDC2_sangria_training_v2.h5': ROOT/'data/raw/triangle-gb/LDC2_sangria_training_v2.h5',
}


def install_adapter():
    if getattr(h5py.File,'_triangle_gb_path_adapter',False):return
    original=h5py.File
    class MappedFile(original):
        _triangle_gb_path_adapter=True
        def __init__(self,name,*args,**kwargs):
            target=MAPPING.get(str(name))
            if target is not None:
                if not target.is_file():raise FileNotFoundError(f'Prepared input missing: {target}')
                folder=ROOT/'runs/triangle-gb';folder.mkdir(parents=True,exist_ok=True)
                with (folder/'path-mapping.jsonl').open('a') as f:
                    f.write(json.dumps({'original':str(name),'mapped':str(target.relative_to(ROOT))})+'\n')
                name=str(target)
            super().__init__(name,*args,**kwargs)
    # A subclass preserves notebook isinstance(obj, h5py.File) checks.
    h5py.File=MappedFile
