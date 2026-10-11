#!/usr/bin/env python3
"""Verify full Sangria inputs and prepare the exact full-size cache expected by unchanged Example 3."""
import datetime,hashlib,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/triangle-gb/sangria'
DATA=ROOT/'data/raw/triangle-gb/LDC2_sangria_training_v2.h5'
WORK=ROOT/'runs/triangle-gb/workspace/Triangle-GB'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'runs/triangle-gb/matplotlib'))
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ.setdefault(k,'1')
import h5py,numpy as np
from Triangle.Constants import DAY,PI
from Triangle.FFTTools import FFT_window
from Triangle.TDI import AETfromXYZ,TDIStringManipulation
from Triangle.Orbit import Orbit
from Triangle_GB import TDIFlyGB
FIELDS=['Amplitude','Frequency','FrequencyDerivative','InitialPhase','Inclination','EclipticLongitude','EclipticLatitude','Polarization']
PARAMS=['A','f0','fdot0','phase0','inclination','longitude','latitude','psi']


def numeric_fields(a,prefix=''):
    if a.dtype.names:
        for n in a.dtype.names:yield from numeric_fields(a[n],prefix+n+'/')
    elif np.issubdtype(a.dtype,np.number):yield prefix.rstrip('/') or '<value>',a


def scan(file):
    inventory=[]
    def visit(name,obj):
        if not isinstance(obj,h5py.Dataset):return
        item={'path':'/'+name,'shape':list(obj.shape),'dtype':str(obj.dtype),'dtype_descr':obj.dtype.descr,'compression':obj.compression,'numeric_fields':{}}
        block=max(1,8*1024*1024//max(1,obj.dtype.itemsize))
        n=obj.shape[0] if obj.ndim else 1
        for start in range(0,n,block):
            a=np.asarray(obj[start:start+block] if obj.ndim else obj[()])
            for key,v in numeric_fields(a):
                counts=item['numeric_fields'].setdefault(key,{'values':0,'nan_count':0,'inf_count':0})
                counts['values']+=int(v.size);counts['nan_count']+=int(np.isnan(v).sum());counts['inf_count']+=int(np.isinf(v).sum())
        inventory.append(item)
        print('SCANNED',name,obj.shape,flush=True)
    file.visititems(visit);return inventory


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(4*1024*1024):h.update(b)
    return h.hexdigest()


def main():
    start=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True);(WORK/'Test').mkdir(parents=True,exist_ok=True)
    report={'scope':'Full input scan, full dgb parameter-cache preparation and unchanged non-plot Example 3 interface cells; not a complete notebook execution.', 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':{},'original_cells':[]}
    provenance=json.loads((OUT/'download-provenance.json').read_text());assert DATA.stat().st_size==provenance['official_bytes'];assert sha(DATA)==provenance['local_sha256']
    report['checks']['verified_input_sha256']=True
    with h5py.File(DATA,'r') as f:
        schema=scan(f);(OUT/'hdf5-schema.json').write_text(json.dumps(schema,indent=2)+'\n')
        for path in ['/sky/dgb/cat','/sky/dgb/tdi']:
            item=next(x for x in schema if x['path']==path)
            assert all(c['nan_count']==0 and c['inf_count']==0 for c in item['numeric_fields'].values())
        report['checks']['default_dgb_all_numeric_values_finite']=True
        cat=f['sky/dgb/cat'];tdi=f['sky/dgb/tdi'];assert set(FIELDS)<=set(cat.dtype.names);assert set(['t','X','Y','Z'])<=set(tdi.dtype.names)
        assert cat.ndim==2 and cat.shape[1]==1 and tdi.ndim==2 and tdi.shape[1]==1
        report['default_shapes']={'cat':list(cat.shape),'tdi':list(tdi.shape)}
        # The notebook already supports this cache. Prepare ALL rows without 208M scalar HDF5 reads or giant Python lists.
        cache=WORK/'Test/dgb_parameters.txt';partial=cache.with_suffix('.txt.part')
        with partial.open('w') as out:
            out.write("# 'A', 'f0', 'fdot0', 'phase0', 'inclination', 'longitude', 'latitude', 'psi'\n")
            for first in range(0,len(cat),131072):
                records=cat[first:first+131072,0];a=np.column_stack([records[k] for k in FIELDS]);assert np.isfinite(a).all();np.savetxt(out,a,fmt='%.18e')
                if first%(131072*32)==0:print('CACHE ROWS',min(len(cat),first+len(records)),'/',len(cat),flush=True)
        partial.replace(cache)
        cache_hash=sha(cache);print('CACHE READY',len(cat),'rows',flush=True)
        n=json.loads((ROOT/'external/triangle-gb/Examples/3_LDC2a_GB_Reconstruction.ipynb').read_text())
        ns=dict(h5f=f,np=np,AETfromXYZ=AETfromXYZ,FFT_window=FFT_window,DAY=DAY,PI=PI,Orbit=Orbit,TDIFlyGB=TDIFlyGB,TDIStringManipulation=TDIStringManipulation)
        from tqdm import tqdm
        ns['tqdm']=tqdm
        def cell(i):
            s=''.join(n['cells'][i]['source']);exec(compile(s,'3_LDC2a_GB_Reconstruction.ipynb:cell'+str(i),'exec'),ns);report['original_cells'].append({'zero_based_index':i,'sha256':hashlib.sha256(s.encode()).hexdigest(),'modified':False})
        original_cwd=Path.cwd();os.chdir(WORK/'Examples')
        try:
            for i in [6,9,12,13]:cell(i)
            # Verify the complete loaded cache against the authoritative HDF5, not a subset.
            for first in range(0,len(cat),131072):
                records=cat[first:first+131072,0]
                for key,field in zip(PARAMS,FIELDS):assert np.array_equal(ns['gb_parameters'][key][first:first+len(records)],records[field])
            report['checks']['full_cache_exact_roundtrip_against_catalog']=True
            for i in [15,17,18,22,24]:cell(i)
        finally:os.chdir(original_cwd)
        t=ns['data_time'];diff=np.diff(t);assert np.all(diff>0) and np.allclose(diff,diff[0],rtol=0,atol=1e-8)
        assert ns['data_channels_td'].shape==(3,len(t)) and np.isfinite(ns['data_channels_td']).all()
        assert np.isfinite(ns['data_channels_fd']).all() and np.isfinite(ns['template_in_bin']).all()
        assert ns['template_in_bin'].shape==ns['data_channels_fd_in_bin'].shape
        o=ns['orbit'];g=ns['gb_response_generator'];raw_covered=bool(o.tdata[0]<=t[0] and t[-1]<=o.tdata[-1]);sparse_covered=bool(o.tdata[0]<=g.sparse_times[0] and g.sparse_times[-1]<=o.tdata[-1]);assert raw_covered and sparse_covered
        delayed=np.concatenate([np.asarray(g.sparse_times-d[i]).ravel() for c in g.delay_dict for d in c.values() for i in range(len(d))])
        assert all(np.isfinite(fn(delayed)).all() for fn in o.Positionfunctions().values())
        report['checks']['original_dgb_channel_fft_parameter_band_and_template_interfaces']=True
        report['checks']['observed_and_nominal_sparse_orbit_coverage']=True
        report['time_and_orbit']={'dt_seconds':float(diff[0]),'data_start_seconds':float(t[0]),'data_end_seconds':float(t[-1]),'samples':len(t),'orbit_rows':o.N,'orbit_start_seconds':float(o.tdata[0]),'orbit_end_seconds':float(o.tdata[-1]),'sparse_end_seconds':float(g.sparse_times[-1]),'delayed_query_min_seconds':float(delayed.min()),'delayed_query_max_seconds':float(delayed.max()),'negative_start_boundary_extrapolation_seconds':max(0.,float(o.tdata[0]-delayed.min()))}
        report['selected_band']={'center_hz':float(ns['FCENTER']),'sources':len(ns['source_idx']),'frequency_bins':len(ns['data_idx']),'template_shape':list(ns['template_in_bin'].shape)}
        report['parameter_conventions']={'cache_columns':PARAMS,'catalog_fields':FIELDS,'after_loading':'Original cell 15: psi += pi/2; phase0 *= -1. Cache retains original pre-transform catalog values.'}
        report['cache']={'local_ignored_path':str(cache.relative_to(ROOT)),'rows':len(cat),'columns':8,'bytes':cache.stat().st_size,'sha256':cache_hash,'all_rows_verified':True,'upstream_supported_loadtxt_branch_used':True}
        report['nonfinite_optional_fields']=[{'dataset':item['path'],'field':name,**counts} for item in schema for name,counts in item['numeric_fields'].items() if counts['nan_count'] or counts['inf_count']]
    report['all_preparation_checks_pass']=all(report['checks'].values());report['elapsed_seconds']=time.perf_counter()-start
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('Sangria preparation checks passed',flush=True)


if __name__=='__main__':main()
