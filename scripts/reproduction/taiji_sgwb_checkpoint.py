"""JSON sidecar for Eryn state not fully captured by the original HDF backend."""
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(8*1024*1024):h.update(b)
    return h.hexdigest()


def pack_rng(state):
    return [state[0],np.asarray(state[1],dtype=np.uint32).tolist(),int(state[2]),int(state[3]),float(state[4])]


def unpack_rng(value): return (value[0],np.array(value[1],dtype=np.uint32),int(value[2]),int(value[3]),float(value[4]))


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def state_summary(sampler):
    state=sampler.get_last_sample()
    arrays={**{'coords_'+k:v for k,v in state.branches_coords.items()},**{'inds_'+k:v for k,v in state.branches_inds.items()},'log_like':state.log_like,'log_prior':state.log_prior,'betas':state.betas}
    hashes={k:hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for k,v in arrays.items()}
    return {'iteration':int(sampler.iteration),'array_sha256':hashes,'sampler_rng_sha256':digest(pack_rng(sampler.random_state)),'numpy_rng_sha256':digest(pack_rng(np.random.get_state())),'temperature_adaptation_time':int(sampler.temperature_control.time),'move_counters':[{'class':type(m).__name__,'num_proposals':int(m.num_proposals),'accepted_sha256':hashlib.sha256(np.ascontiguousarray(m.accepted).tobytes()).hexdigest(),'time':int(m.time)} for m in sampler.moves]}


def save_sidecar(sampler,backend_file,path,provenance):
    value={'schema_version':1,'backend_filename':Path(backend_file).name,'backend_sha256':sha(backend_file),'provenance':provenance,'state_summary':state_summary(sampler),'numpy_global_rng':pack_rng(np.random.get_state()),'sampler_rng':pack_rng(sampler.random_state),'temperature':{'time':int(sampler.temperature_control.time),'betas':sampler.temperature_control.betas.tolist()},'moves':[{'class':type(m).__name__,'num_proposals':int(m.num_proposals),'accepted':m.accepted.tolist(),'time':int(m.time)} for m in sampler.moves]}
    path=Path(path);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(path)
    return value


def restore_sidecar(sampler,backend_file,path,provenance):
    value=json.loads(Path(path).read_text())
    assert sha(backend_file)==value['backend_sha256'],'Backend changed after checkpoint'
    assert provenance==value['provenance'],'Source/config/input provenance changed'
    assert sampler.iteration==value['state_summary']['iteration']
    assert pack_rng(sampler.random_state)==value['sampler_rng'],'HDF sampler RNG did not restore'
    last=sampler.get_last_sample()
    assert np.array_equal(last.betas,np.array(value['temperature']['betas']))
    sampler.temperature_control.time=value['temperature']['time']
    sampler.temperature_control.betas=np.array(value['temperature']['betas'])
    assert len(sampler.moves)==len(value['moves'])
    for move,record in zip(sampler.moves,value['moves']):
        assert type(move).__name__==record['class']
        move.num_proposals=record['num_proposals'];move.accepted=np.array(record['accepted']);move.time=record['time']
    np.random.set_state(unpack_rng(value['numpy_global_rng']))
    assert state_summary(sampler)==value['state_summary'],'Restored state differs from saved state'
    return value


from eryn.backends import HDFBackend


class RestartCompatibleHDFBackend(HDFBackend):
    """Normalize only key_order readback types for Eryn 1.2.6 dict equality.

    Upstream HDFBackend returns ndarray dictionary values while the sampler
    expects lists. Contents/order/writing/likelihood/chain are not changed.
    """
    @property
    def key_order(self):
        return {key:value.tolist() if isinstance(value,np.ndarray) else value
                for key,value in super().key_order.items()}
