#Estimate the spectrum of SGWB with interpolation.
#TDC II 2.8 training sets, CGB foreground is substracted in advance.
import multiprocessing

import numpy as np
from scipy.signal import windows, ShortTimeFFT
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import logging
import h5py
from pathlib import Path

import eryn.ensemble
import eryn.state
import eryn.prior
import eryn.moves
import eryn.backends

from taijisgwb.detector.tdi import tdi_X2, aet_from_xyz, tdi_aet_from_tdi_x
from taijisgwb.detector.noise import TaijiNoisePSD
from taijisgwb import Interferometer
from taijisgwb.detector.orbit import InterpolationOrbit
from taijisgwb.waveform import calc_omega_powerlaw
from taijisgwb.utils import psd_from_omega

logging.basicConfig(level = logging.INFO, 
                    format = "%(asctime)s - %(levelname)s: %(message)s")
multiprocessing.set_start_method("fork")

PROJ_DIR = Path("/home/yang/WorkSpace/taiji_data_challenge_sgwb")
PARENT_DIR = Path(__file__).parent

#======== Parameter settings ========
#samples
f_analow, f_anaupp = 1e-4, 5e-2
f_res = 1e-5
tperseg = 7. * 24 * 3600
npool = 62
#input & output
strain_file = PROJ_DIR / "data/TDCII2-8.h5"
result_outdir = PARENT_DIR / "results/"
asd_img_name = "asd_AET_nofg.png"
backend_name = "rj_AET_nofg.h5"
#====================================

save_path = Path(result_outdir)
save_path.mkdir(parents=True, exist_ok=True)

#------- Generate TDI variables ------- 
#read and gen.
logging.info("Read simulation results.")
tdi_names = ["A", "E", "T"]
ntdi = len(tdi_names)
tdi_methods = tdi_aet_from_tdi_x(tdi_X2)

with h5py.File(strain_file, "r") as f:
    time = f["data"]["time"][()]
    strain_X2, strain_Y2, strain_Z2 = f["data"]["XYZ"][()] - f["data"]["foreground"][()]

dt = time[1] - time[0]
fsample = 1. / dt
ndrop_points = int(2000 * fsample)

time = time[ndrop_points:-ndrop_points]
strain_AET2 = aet_from_xyz(strain_X2, strain_Y2, strain_Z2)
strain_AET2 = [strain_AET2[i][ndrop_points:-ndrop_points]
              for i in range(ntdi)]

#-------- Binning & PSD est ----------
nperseg = int(tperseg * fsample)
nseg = len(time) // nperseg
tperseg = nperseg * dt
f_low = 1. / tperseg
nperbin = int(f_res / f_low)
logging.info(f"Cut into {nseg} segments, {tperseg/3600/24 :.1f} days per segment.")
logging.info(f"Binning in frequency domain, {nperbin} per bin.")

f_est = np.arange(nperseg//2+1) * f_low
nbin = len(f_est) // nperbin

win_array = windows.kaiser(M=nperseg, beta=14)
win_bw = nperseg * np.sum(win_array**2) / np.sum(win_array)**2
logging.info(f"Normalized equivalent noise bandwidth of window: {win_bw :.1f} bins.")
SFT = ShortTimeFFT(win_array, nperseg, fsample,
                   fft_mode="onesided", scale_to="psd")
strain_segs = np.empty((ntdi, nseg, len(f_est)), dtype=complex)
for i, strain in enumerate(strain_AET2):
    strain_segs[i] = SFT.stft_detrend(strain, "constant",
                                        p0=0, p1=nseg, k_offset=nperseg//2).T
    # strain_chunk_analysed_[..., 1:-1 if nperseg%2 == 0 else None] *= 2
csd_est = np.conj(strain_segs[:, None, :, :]) * strain_segs[None, :, :, :]

csd_est = csd_est[..., :(nbin*nperbin)].reshape(ntdi, ntdi, nseg, -1, nperbin)
csd_est = np.mean(csd_est, axis=-1) * 2.
f_est = np.mean(f_est[:(nbin*nperbin)].reshape(-1, nperbin), axis=-1)

#choose [f_analow, f_anaupp].
mask = (f_est >= f_analow) & (f_est < f_anaupp)
f_est = f_est[mask]
csd_est = csd_est[..., mask]

#plot & notch.
def notch_mask(x, intervals):
    ans = np.ones_like(x, dtype=bool)
    for interval in intervals:
        idx = (x >= interval[0]) & (x < interval[1])
        ans[idx] = False
    return ans

f_notch = [
    (2.35e-2, 2.65e-2), (4.7e-2, 5.2e-2),
]

for i in range(ntdi):
    plt.loglog(f_est, (np.mean(csd_est[i, i].real, axis=0))**.5, label=tdi_names[i])
for interval in f_notch:
    plt.axvspan(*interval, color="grey", alpha=.5)
plt.grid()
plt.xlabel("Frequency")
plt.ylabel("ASD")
plt.legend()
plt.title("Average ASD of TDI variables")
plt.savefig(PARENT_DIR / asd_img_name, bbox_inches="tight", dpi=300)
plt.close()

mask = notch_mask(f_est, f_notch)
f_est = f_est[mask]
nf_est = len(f_est)
csd_est = csd_est[..., mask]


#---------------------- Transfer function ------------------------
orbit = InterpolationOrbit(PROJ_DIR/"data/MicroSateOrbitEclipticTCB/MicroSateOrbit.hdf5")
taiji = Interferometer(orbit)
t_seg = (np.arange(nseg) + .5) * tperseg + ndrop_points * dt
ltt = orbit.calc_ltt(t_seg)

acc_corr_factor = np.empty((ntdi, ntdi, 6, nseg, nf_est), dtype=complex)
ro_corr_factor = np.empty((ntdi, ntdi, 6, nseg, nf_est), dtype=complex)
for i in range(ntdi):
    acc_corr_factor[i, i] = taiji.calc_noise_acc_corr_factor(f_est, t_seg, tdi_methods[i]).to_array
    ro_corr_factor[i, i] = taiji.calc_noise_ro_corr_factor(f_est, t_seg, tdi_methods[i]).to_array
    for j in range(i+1, ntdi):
        acc_corr_factor[i, j] = taiji.calc_noise_acc_corr_factor(f_est, t_seg, tdi_methods[i], tdi_methods[j]).to_array
        acc_corr_factor[j, i] = np.conj(acc_corr_factor[i, j])
        ro_corr_factor[i, j] = taiji.calc_noise_ro_corr_factor(f_est, t_seg, tdi_methods[i], tdi_methods[j]).to_array
        ro_corr_factor[j, i] = np.conj(ro_corr_factor[i, j])

spectrum_acc = TaijiNoisePSD.calc_psd_acc(f_est, 1.)
spectrum_ro = TaijiNoisePSD.calc_psd_ro(f_est, 1.)

logging.info("Calculate ORF.")
orf = np.empty((ntdi, ntdi, nseg, nf_est), dtype=complex)
for i in range(ntdi):
    orf[i, i] = taiji.calc_orf(f_est, t_seg, tdi_methods[i])
    for j in range(i+1, ntdi):
        orf_ = taiji.calc_orf(f_est, t_seg, tdi_methods[i], tdi_methods[j])
        orf[i, j] = orf_
        orf[j, i] = np.conj(orf_)

# ------------------- MCMC ---------------------
log_f_est = np.log10(f_est)

def create_omega_interp_fun(knot, edge):
    log_f_interp = np.concatenate(([np.log10(f_analow)], knot[:, 0], [np.log10(f_anaupp)]))
    log_omega_interp = np.concatenate(([edge[0, 0]],
                                        knot[:, 1], [edge[0, 1]]))
    interp_fun = interp1d(log_f_interp, log_omega_interp, kind="quadratic", assume_sorted=False)
    return interp_fun

def log_likelihood(params):
    a_acc, a_ro, params_knot, params_edge = params
    a_acc = a_acc[0]
    a_ro = a_ro[0]

    psd_acc = a_acc[:, None]**2 * spectrum_acc
    csd_hypo = np.sum(psd_acc[:, None, :] * acc_corr_factor, axis=2)
    psd_ro = a_ro[:, None]**2 * spectrum_ro
    csd_hypo += np.sum(psd_ro[:, None, :] * ro_corr_factor, axis=2)

    omega_interp_fun = create_omega_interp_fun(params_knot, params_edge)
    log_omega_hypo = omega_interp_fun(log_f_est)
    if log_omega_hypo.min() < -14. or log_omega_hypo.max() > -9.:
        return -1e50
    csd_hypo += orf * psd_from_omega(f_est, 10**log_omega_hypo)

    csd_hypo = np.moveaxis(csd_hypo, [0, 1], [-2, -1])
    inv_csd_hypo = np.linalg.inv(csd_hypo)
    inv_csd_hypo = np.moveaxis(inv_csd_hypo, [-2, -1], [0, 1])
    ll_exp = -nperbin * np.sum(csd_est * inv_csd_hypo).real
    ll_coef = -nperbin * np.sum(np.log(np.linalg.det(csd_hypo).real)) 

    ans = (ll_exp + ll_coef) / win_bw
    return ans

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
nstep = 350
ntemp = 6
nwalker = npool
branch_names = ["acc", "ro",  "sgwb_knot", "sgwb_edge"]
ndim = {key: val for key, val in zip(
    branch_names,
    [6, 6, 2, 2]
    )}
nleaf_max = {key: val for key, val in zip(
    branch_names,
    [1, 1, 16, 1]
    )}
nleaf_min = {key: val for key, val in zip(
    branch_names,
    [1, 1, 1, 1]
    )}
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

priors = {
    branch_names[0]: {},
    branch_names[1]: {},
    branch_names[2]: {
        0: eryn.prior.uniform_dist(np.log10(f_analow), np.log10(f_anaupp)),
        1: eryn.prior.uniform_dist(-14., -9.)
    },
    branch_names[3]: {
        0: eryn.prior.uniform_dist(-14., -9.),
        1: eryn.prior.uniform_dist(-14., -9.)
    }
}
for i in range(6):
    priors[branch_names[0]][i] = eryn.prior.uniform_dist(.75*3e-15, 1.25*3e-15)
    priors[branch_names[1]][i] = eryn.prior.uniform_dist(.75*8e-12, 1.25*8e-12)

params0 = {
    branch_name: np.empty((ntemp, nwalker, nleaf_max[branch_name], ndim[branch_name]))
    for branch_name in branch_names
}
for branch_name in branch_names:
    for l in range(nleaf_max[branch_name]):
        for d in range(ndim[branch_name]):
            params0[branch_name][:, :, l, d] = priors[branch_name][d].rvs(size=(ntemp, nwalker))

inds0 = {}
inds0[branch_names[0]] = np.ones((ntemp, nwalker, nleaf_max[branch_names[0]]),
                                 dtype = bool)
inds0[branch_names[1]] = np.ones((ntemp, nwalker, nleaf_max[branch_names[1]]),
                                 dtype = bool)
inds0_branch2 = np.random.randint(2,
                                  size = (ntemp, nwalker, nleaf_max[branch_names[2]]),
                                  dtype = bool) 
inds0_branch2[:, :, 0] = True
inds0[branch_names[2]] = inds0_branch2
inds0[branch_names[3]] = np.ones((ntemp, nwalker, nleaf_max[branch_names[3]]),
                                 dtype = bool)


noise_move = eryn.moves.StretchMove(live_dangerously=True,
                                    gibbs_sampling_setup={branch_names[0]: None, branch_names[1]: None})
cov = {
    branch_names[2]: np.diag([0.02, 0.01])**2,
    branch_names[3]: np.diag([0.02, 0.02])**2,
}
sgwb_move = eryn.moves.GaussianMove(cov, gibbs_sampling_setup={branch_names[2]: None, branch_names[3]: None})
moves = eryn.moves.CombineMove([noise_move, sgwb_move])

pool = multiprocessing.Pool(processes=npool)
backend = eryn.backends.HDFBackend(result_outdir/backend_name)
sampler = eryn.ensemble.EnsembleSampler(nwalker, ndim, log_likelihood, priors,
                                        tempering_kwargs = dict(ntemps=ntemp),
                                        nbranches = len(branch_names),
                                        branch_names = branch_names,
                                        nleaves_max = nleaf_max,
                                        nleaves_min = nleaf_min,
                                        moves = moves,
                                        rj_moves = True,
                                        pool = pool,
                                        backend = backend)

state0 = eryn.state.State(params0, 
                          log_prior = sampler.compute_log_prior(params0, inds=inds0), 
                          log_like = sampler.compute_log_like(params0, inds=inds0)[0],
                          inds = inds0
                          )
sampler.run_mcmc(state0, nstep, burn=2000, thin_by=15, progress=True)
