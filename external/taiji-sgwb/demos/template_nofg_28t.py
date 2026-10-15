#Estimate the spectrum of SGWB with known template.
#TDC II 2.8 training sets, CGB foreground is substracted in advance.
import multiprocessing

import numpy as np
from scipy.signal import windows, ShortTimeFFT
import matplotlib.pyplot as plt
import logging
import h5py
from pathlib import Path

import eryn.ensemble
import eryn.prior
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
backend_name = "template_AET_nofg.h5"
#====================================

save_path = Path(result_outdir)
save_path.mkdir(parents=True, exist_ok=True)

#------- Generate TDI variables ------- 
#read and gen.
logging.info("Read simulation results.")
tdi_names = ['A', 'E', 'T']
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

#------------------------------ MCMC -------------------------------
def log_likelihood(params):
    a_acc, a_ro, params_sgwb = params

    psd_acc = a_acc[:, None]**2 * spectrum_acc
    csd_hypo = np.sum(psd_acc[:, None, :] * acc_corr_factor, axis=2)
    psd_ro = a_ro[:, None]**2 * spectrum_ro
    csd_hypo += np.sum(psd_ro[:, None, :] * ro_corr_factor, axis=2)

    omega_sgwb = calc_omega_powerlaw(f_est, *params_sgwb)
    csd_hypo += orf * psd_from_omega(f_est, omega_sgwb)

    csd_hypo = np.moveaxis(csd_hypo, [0, 1], [-2, -1])
    inv_csd_hypo = np.linalg.inv(csd_hypo)
    inv_csd_hypo = np.moveaxis(inv_csd_hypo, [-2, -1], [0, 1])
    ll_exp = -nperbin * np.sum(csd_est * inv_csd_hypo).real
    ll_coef = -nperbin * np.sum(np.log(np.linalg.det(csd_hypo).real)) 

    ans = ll_exp + ll_coef
    ans /= win_bw
    return ans

#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
nstep = 350
ntemp = 6
nwalker = 62
branch_names = ["acc", "ro", "sgwb"]
ndim = {key: val for key, val in zip(
        branch_names,
        [6, 6, 2]
        )}
nleaf_max = {key: 1 for key in branch_names}
nleaf_min = {key: 1 for key in branch_names}

priors = {
    branch_names[0]: {},
    branch_names[1]: {},
    branch_names[2]: {
        0: eryn.prior.uniform_dist(1e-14, 5e-11),
        1: eryn.prior.uniform_dist(-1., 2.)
    }
}
for i in range(6):
    priors[branch_names[0]][i] = eryn.prior.uniform_dist(.75*3e-15, 1.25*3e-15)
    priors[branch_names[1]][i] = eryn.prior.uniform_dist(.75*8e-12, 1.25*8e-12)

params0 = {branch_name: np.empty((ntemp, nwalker, 1, ndim[branch_name]))
           for branch_name in branch_names}
for branch_name in branch_names:
    for d in range(ndim[branch_name]):
        params0[branch_name][:, :, 0, d] = priors[branch_name][d].rvs(size=(ntemp, nwalker))

pool = multiprocessing.Pool(processes=npool)
backend = eryn.backends.HDFBackend(result_outdir/backend_name)
sampler = eryn.ensemble.EnsembleSampler(nwalker, ndim, log_likelihood, priors,
                                        tempering_kwargs = dict(ntemps=ntemp),
                                        nbranches = len(branch_names),
                                        branch_names = branch_names,
                                        nleaves_min = nleaf_min,
                                        nleaves_max = nleaf_max,
                                        pool = pool,
                                        backend = backend)
sampler.run_mcmc(params0, nstep, burn=1000, thin_by=12, progress=True)