"""Immutable paired checkpoints for unrecorded burn-in and original production."""
import json
import shutil
from pathlib import Path
import numpy as np
from eryn.state import State
from taiji_sgwb_checkpoint import sha,pack_rng,unpack_rng


def write_json(path,value):
    p=Path(path);temp=p.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(p)


def save_checkpoint(root,backend,sampler,state,burn_done,provenance):
    """Save unthinned latest state separately; burn is never stored in chain."""
    root=Path(root);name=f'burn-{burn_done:04d}-production-{sampler.iteration:04d}'
    directory=root/'checkpoints'/name
    assert not directory.exists(),'Refuse checkpoint overwrite'
    directory.mkdir(parents=True)
    values={**{'coords_'+k:v for k,v in state.branches_coords.items()},**{'inds_'+k:v for k,v in state.branches_inds.items()},'log_like':state.log_like,'log_prior':state.log_prior,'betas':state.betas}
    np.savez_compressed(directory/'state.npz',**values)
    shutil.copyfile(backend,directory/'template_AET_nofg.h5')
    record={'schema_version':1,'burn_done':burn_done,'production_done':int(sampler.iteration),'provenance':provenance,'npz_sha256':sha(directory/'state.npz'),'backend_sha256':sha(directory/'template_AET_nofg.h5'),'numpy_rng':pack_rng(np.random.get_state()),'sampler_rng':pack_rng(sampler.random_state),'temperature_time':int(sampler.temperature_control.time),'moves':[{'class':type(m).__name__,'accepted':m.accepted.tolist(),'num_proposals':int(m.num_proposals),'time':int(m.time)} for m in sampler.moves]}
    write_json(directory/'state.json',record)
    write_json(root/'latest-checkpoint.json',{'directory':str(directory.relative_to(root)),'state_json_sha256':sha(directory/'state.json')})
    # Keep three immutable pairs, avoiding a growing chain-copy archive.
    generations=sorted((root/'checkpoints').iterdir(),key=lambda p:p.stat().st_mtime)
    for old in generations[:-3]:shutil.rmtree(old)
    return record


def checkpoint_record(root):
    root=Path(root);pointer=json.loads((root/'latest-checkpoint.json').read_text());p=root/pointer['directory']
    assert sha(p/'state.json')==pointer['state_json_sha256']
    record=json.loads((p/'state.json').read_text())
    assert sha(p/'state.npz')==record['npz_sha256'] and sha(p/'template_AET_nofg.h5')==record['backend_sha256']
    return p,record


def restore_state(sampler,path,record,provenance):
    assert record['provenance']==provenance
    assert sampler.iteration==record['production_done']
    data=np.load(Path(path)/'state.npz')
    names=list(sampler.branch_names)
    state=State({k:data['coords_'+k] for k in names},inds={k:data['inds_'+k] for k in names},log_like=data['log_like'],log_prior=data['log_prior'],betas=data['betas'],random_state=unpack_rng(record['sampler_rng']))
    sampler.random_state=unpack_rng(record['sampler_rng'])
    assert pack_rng(sampler.random_state)==record['sampler_rng']
    sampler.temperature_control.time=record['temperature_time'];sampler.temperature_control.betas=state.betas.copy()
    for m,r in zip(sampler.moves,record['moves']):
        assert type(m).__name__==r['class'];m.accepted=np.array(r['accepted']);m.num_proposals=r['num_proposals'];m.time=r['time']
    np.random.set_state(unpack_rng(record['numpy_rng']))
    return state
