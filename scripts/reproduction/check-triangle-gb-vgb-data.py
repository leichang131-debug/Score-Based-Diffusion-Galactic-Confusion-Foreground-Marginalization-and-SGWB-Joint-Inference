#!/usr/bin/env python3
"""Validate public VGB inputs and unchanged tutorial preparation cells; no search/sampling."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/triangle-gb/data'
DATA = ROOT / 'data/raw/triangle-gb'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'runs/triangle-gb/matplotlib'))
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ.setdefault(key, '1')

import h5py
import numpy as np
from Triangle.Constants import DAY
from Triangle.Data import read_dict_from_h5
from Triangle.FFTTools import FFT_window
from Triangle.TDI import AETfromXYZ, XYZfromAET, TDIStringManipulation
from Triangle.Orbit import Orbit
from Triangle_GB import TDIFly, TDIFlyGB

NAMES = ['1_TDIFlyGB_Rapid_Search(CPU).ipynb', '2_TDIFlyGB_Parameter_Estimation(CPU).ipynb']


def inventory(path):
    result = {'filename': path.name, 'groups': [], 'datasets': []}
    with h5py.File(path, 'r') as file:
        def visit(name, obj):
            if isinstance(obj, h5py.Group):
                result['groups'].append({'path': '/' + name, 'attributes': list(obj.attrs.keys())})
                return
            item = {'path': '/' + name, 'shape': list(obj.shape), 'dtype': str(obj.dtype),
                    'elements': int(obj.size), 'logical_bytes': int(obj.size * obj.dtype.itemsize),
                    'chunks': obj.chunks, 'compression': obj.compression,
                    'attributes': list(obj.attrs.keys())}
            if np.issubdtype(obj.dtype, np.number):
                nan_count = inf_count = finite_count = 0
                for start in range(0, obj.shape[0] if obj.ndim else 1, 262144):
                    values = obj[start:start + 262144] if obj.ndim else obj[()]
                    nan_count += int(np.isnan(values).sum())
                    inf_count += int(np.isinf(values).sum())
                    finite_count += int(np.isfinite(values).sum())
                item.update(nan_count=nan_count, inf_count=inf_count, finite_count=finite_count)
                assert finite_count == obj.size, f'Nonfinite values in {name}'
            result['datasets'].append(item)
        file.visititems(visit)
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    report = {'scope': 'Public VGB full-data checks and unchanged tutorial input/preprocessing cells only; no search, waveform fitting or nested sampling.',
              'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'checks': {}, 'notebook_cells_executed': [], 'notes': []}

    def check(name, fn):
        before = time.perf_counter()
        detail = fn()
        passed = detail.get('strict_coverage_pass', True) if isinstance(detail, dict) else True
        report['checks'][name] = {'passed': passed, 'detail': detail, 'seconds': time.perf_counter() - before}
        print('PASS' if passed else 'COVERAGE GAP', name, flush=True)
        return detail

    provenance = json.loads((OUT / 'download-provenance.json').read_text())
    def verify_files():
        for item in provenance['files']:
            path = ROOT / item['path']
            assert path.stat().st_size == item['official_bytes']
            md5, sha = hashlib.md5(), hashlib.sha256()
            with path.open('rb') as f:
                while chunk := f.read(1024 * 1024):
                    md5.update(chunk); sha.update(chunk)
            assert md5.hexdigest() == item['official_md5'] == item['local_md5']
            assert sha.hexdigest() == item['local_sha256']
        return 'Both entire local files match official byte counts/MD5 and recorded SHA-256.'
    check('file_checksums', verify_files)
    trees = check('full_hdf5_inventory_and_finiteness', lambda: [inventory(DATA / item['filename']) for item in provenance['files']])
    (OUT / 'hdf5-schema.json').write_text(json.dumps(trees, indent=2) + '\n')
    nbs = {name: json.loads((ROOT / 'external/triangle-gb/Examples' / name).read_text()) for name in NAMES}
    common_cells = [5, 6, 9, 17]
    def compare_cells():
        for index in common_cells:
            assert nbs[NAMES[0]]['cells'][index]['source'] == nbs[NAMES[1]]['cells'][index]['source']
        return {'zero_based_cell_indices': common_cells, 'equal_source': True}
    check('common_tutorial_cells_identical', compare_cells)
    ns = dict(np=np, h5py=h5py, read_dict_from_h5=read_dict_from_h5,
              AETfromXYZ=AETfromXYZ, FFT_window=FFT_window, DAY=DAY,
              Orbit=Orbit, TDIFly=TDIFly, TDIFlyGB=TDIFlyGB,
              TDIStringManipulation=TDIStringManipulation,
              DATA_DIR=str(DATA / '0_1_VGB_TDIXYZ.h5'),
              PARAM_DIR=str(DATA / '0_1_VGB_parameters.h5'),
              ORBIT_DIR=str(ROOT / 'external/triangle-simulator/OrbitData/MicroSateOrbitEclipticTCB'))

    def cell(name, index, namespace):
        source = ''.join(nbs[name]['cells'][index]['source'])
        exec(compile(source, name + ':cell' + str(index), 'exec'), namespace)
        report['notebook_cells_executed'].append({'filename': name, 'zero_based_cell_index': index,
            'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'source_modified': False})

    def read_inputs():
        cell(NAMES[0], 5, ns)
        data, params = ns['data_dict'], ns['inject_parameters']
        time_array = np.asarray(data['time'])
        assert time_array.ndim == 1 and len(time_array) > 1
        assert set(['X2', 'Y2', 'Z2']) <= set(data['XYZ'])
        assert all(np.asarray(data['XYZ'][k]).shape == time_array.shape for k in ['X2', 'Y2', 'Z2'])
        required = ['A', 'f0', 'fdot0', 'inclination', 'longitude', 'latitude', 'phase0', 'psi']
        assert set(required) <= set(params)
        lengths = {k: len(np.atleast_1d(v)) for k, v in params.items()}
        assert len(set(lengths.values())) == 1
        assert next(iter(lengths.values())) > 4
        assert np.all(params['A'] > 0) and np.all(params['f0'] > 0)
        return {'time_shape': list(time_array.shape), 'XYZ_keys': sorted(data['XYZ']),
                'parameter_fields': sorted(params), 'source_count': next(iter(lengths.values())),
                'parameter_lengths': lengths,
                'meaning': 'Parameter arrays share source-index ordering; XYZ is the aggregate data, not a separate per-source channel table.'}
    check('tutorial_reader_and_parameter_alignment', read_inputs)

    def axis():
        time_array = np.asarray(ns['data_dict']['time'])
        diff = np.diff(time_array)
        dt = float(diff[0])
        assert dt > 0 and np.all(diff > 0)
        assert np.allclose(diff, dt, rtol=0, atol=1e-8)
        assert np.isclose(time_array[0] / dt, round(time_array[0] / dt), rtol=0, atol=1e-8)
        cell(NAMES[0], 6, ns)
        padded = ns['data_time']
        channels = ns['data_channels_td']
        assert np.allclose(np.diff(padded), dt, rtol=0, atol=1e-8)
        assert padded[0] == 0 and channels.shape == (2, len(padded))
        assert np.isfinite(channels).all()
        count = len(ns['data_time_pad'])
        assert np.all(channels[:, :count] == 0)
        data = ns['data_dict']['XYZ']
        A, E, T = AETfromXYZ(data['X2'], data['Y2'], data['Z2'])
        restored = XYZfromAET(A, E, T)
        scale = max(float(np.max(np.abs(data[k]))) for k in ['X2', 'Y2', 'Z2'])
        residual = max(float(np.max(np.abs(restored[i] - data[k]))) for i, k in enumerate(['X2', 'Y2', 'Z2']))
        assert residual / scale < 1e-12
        return {'dt_seconds': dt, 'raw_start_seconds': float(time_array[0]),
                'raw_end_seconds': float(time_array[-1]), 'raw_samples': len(time_array),
                'zero_padding_samples': count, 'padded_samples': len(padded),
                'Tobs_seconds': float(ns['Tobs']), 'AE_shape': list(channels.shape),
                'XYZ_AET_roundtrip_max_relative_error': residual / scale}
    check('time_axis_zero_padding_and_channel_conversion', axis)

    def fft():
        cell(NAMES[0], 9, ns)
        f, fd = ns['data_frequency'], ns['data_channels_fd']
        assert np.all(f > 0) and np.all(np.diff(f) > 0)
        assert fd.shape == (2, len(f)) and np.isfinite(fd).all()
        assert np.allclose(np.diff(f), 1.0/ns['Tobs'], rtol=1e-8, atol=1e-16)
        return {'frequency_samples': len(f), 'df_hz': float(f[1] - f[0]),
                'min_frequency_hz': float(f[0]), 'max_frequency_hz': float(f[-1]),
                'AE_frequency_shape': list(fd.shape), 'tukey_alpha': 10000 / ns['Tobs'],
                'normalization': 'Original FFT_window implementation; DC excluded, Tukey window and coherent-gain correction retained.'}
    check('original_tutorial_windowed_fft', fft)

    def selected_sources():
        details = []
        for name in NAMES:
            local = ns.copy()
            for index in [12, 13, 14]:
                cell(name, index, local)
            chosen = local['true_gb_parameters']
            band = local['band_idx']
            level = float(local['PSDlevel'])
            assert len(band) > 1 and level > 0 and np.isfinite(level)
            assert np.isfinite(local['data_channels_fd']).all()
            assert ns['data_frequency'][0] < chosen['f0'] < ns['data_frequency'][-1]
            details.append({'filename': name, 'source_index_zero_based': int(local['analyze_gb_idx']),
                'parameters': {k: float(v) for k, v in chosen.items()},
                'band_width_hz': float(local['band_width']), 'band_bins': len(band),
                'band_first_index_in_DC_excluded_fft': int(band[0]),
                'band_last_index_in_DC_excluded_fft': int(band[-1]),
                'band_start_hz': float(local['data_frequency'][0]),
                'band_end_hz': float(local['data_frequency'][-1]), 'PSDlevel': level})
        return details
    check('original_example_source_selection_and_band', selected_sources)

    def orbit_range():
        cell(NAMES[0], 17, ns)
        orbit, gen = ns['orbit'], ns['gb_tdifly_generator']
        low, high = float(orbit.tdata[0]), float(orbit.tdata[-1])
        raw = ns['data_dict']['time']
        raw_covered = bool(low <= raw[0] <= raw[-1] <= high)
        padded_covered = bool(low <= ns['data_time'][0] <= ns['data_time'][-1] <= high)
        sparse_covered = bool(low <= gen.sparse_times[0] <= gen.sparse_times[-1] <= high)
        # Constructor uses interpolation of delayed times. Inspect the actual arguments.
        delay_times = np.concatenate([np.asarray(gen.sparse_times - delays[i]).ravel()
            for channel in gen.delay_dict for delays in channel.values() for i in range(len(delays))])
        delay_min, delay_max = float(delay_times.min()), float(delay_times.max())
        raw_start = float(raw[0])
        max_delay = max(float(np.max(np.asarray(delays))) for channel in gen.delay_dict for delays in channel.values() if len(delays))
        assert raw_start - max_delay >= low
        if not raw_covered or delay_min < low or delay_max > high:
            report['notes'].append('Strict orbit coverage is NOT satisfied: observed tail and zero-padded sparse boundary delayed times require default spline extrapolation. Finite interface output does not validate extrapolation accuracy. Source/data are unchanged.')
        query = np.unique(np.concatenate([delay_times, np.asarray(gen.sparse_times)]))
        assert all(np.isfinite(fn(query)).all() for fn in orbit.Positionfunctions().values())
        assert all(np.isfinite(fn(query)).all() for fn in orbit.LTTfunctions().values())
        outside = int(np.count_nonzero((raw < low) | (raw > high)))
        strict = raw_covered and padded_covered and sparse_covered and delay_min >= low and delay_max <= high
        return {'orbit_rows': int(orbit.N), 'orbit_dt_seconds': float(orbit.dt),
                'orbit_min_seconds': low, 'orbit_max_seconds': high,
                'raw_data_covered': raw_covered, 'padded_grid_covered': padded_covered, 'sparse_endpoint_covered': sparse_covered,
                'strict_coverage_pass': bool(strict), 'default_interpolators_finite_on_required_sparse_queries': True,
                'observed_samples_outside_orbit': outside,
                'observed_fraction_outside_orbit': outside / len(raw),
                'observed_end_excess_seconds': max(0.0, float(raw[-1])-high),
                'sparse_end_excess_seconds': max(0.0, float(gen.sparse_times[-1])-high),
                'Nsparse': int(gen.Nsparse), 'sparse_min_seconds': float(gen.sparse_times[0]),
                'sparse_max_seconds': float(gen.sparse_times[-1]),
                'TDI_delayed_query_min_seconds': delay_min, 'TDI_delayed_query_max_seconds': delay_max,
                'max_cumulative_delay_seconds': max_delay,
                'boundary_extrapolation_seconds_below_orbit': max(0.0, low-delay_min),
                'observed_start_minus_max_delay_seconds': raw_start-max_delay,
                'note': 'Actual default Orbit and Nsparse=512 constructor used; no waveform generation, search or sampling.'}
    check('default_orbit_and_delayed_time_compatibility', orbit_range)
    report['source_commits'] = {name: subprocess.check_output(['git','-C',str(ROOT/'external'/name),'rev-parse','HEAD'],text=True).strip() for name in ['triangle-gb','triangle-simulator']}
    report['path_adapter'] = {'type':'Script namespace bindings only; no notebook strings changed.',
        'DATA_DIR':'data/raw/triangle-gb/0_1_VGB_TDIXYZ.h5',
        'PARAM_DIR':'data/raw/triangle-gb/0_1_VGB_parameters.h5',
        'ORBIT_DIR':'external/triangle-simulator/OrbitData/MicroSateOrbitEclipticTCB'}
    report['all_checks_pass'] = all(item['passed'] for item in report['checks'].values())
    report['elapsed_seconds'] = time.perf_counter()-started
    report['input_preparation_checks_pass'] = all(item['passed'] for name, item in report['checks'].items() if name != 'default_orbit_and_delayed_time_compatibility')
    report['strict_orbit_coverage_confirmed'] = report['checks']['default_orbit_and_delayed_time_compatibility']['passed']
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Data checks: {sum(item['passed'] for item in report['checks'].values())}/{len(report['checks'])} passed; {report['elapsed_seconds']:.3f} seconds.", flush=True)
    return 0 if report['all_checks_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
