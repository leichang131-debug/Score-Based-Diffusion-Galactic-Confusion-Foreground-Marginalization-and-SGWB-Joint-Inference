import numpy as np
import healpy as hlp

from .constants import MOSA_LABELS
from .tdi import TDI, calc_delayop_factor
from .data import MOSADict
from .. constants import PI_2, PI, C
from ..utils import calc_sphere_frame

class Interferometer:
    """Interferometer.

    Parameters
    ----------
    orbit : Orbit
        Orbit of interferometer.
    """
    def __init__(self, orbit):
        self.orbit = orbit
        # self.noise_psd = noise_psd

    def calc_noise_acc_corr_factor(self, f, t, tdi1, tdi2=None):
        """Calculate transform factor of correlation induced by Acc noise of TDI channels.
        
        Parameters
        ----------
        f : np.array_like
        t : np.array_like
        tdi1, tdi2 : TDI
        """
        ltt = self.orbit.calc_ltt(t)
        delay_factor = calc_delayop_factor(f, ltt)
        polyop1_factor = tdi1.calc_polyop_factor(f, ltt)
        if tdi2 is None:
            ans = calc_noise_acc_corr_factor(delay_factor, polyop1_factor)
        else:
            polyop2_factor = tdi2.calc_polyop_factor(f, ltt)
            ans = calc_noise_acc_corr_factor(delay_factor, polyop1_factor, polyop2_factor)
        return ans 


    def calc_noise_ro_corr_factor(self, f, t, tdi1, tdi2=None):
        """Calculate transform factor of correlation induced by RO nise of TDI channels.

        Parameters
        ----------
        f : np.array_like
        t : np.array_like
        tdi1, tdi2 : TDI
        """
        ltt = self.orbit.calc_ltt(t)
        polyop1_factor = tdi1.calc_polyop_factor(f, ltt)
        if tdi2 is None:
            ans = calc_noise_ro_corr_factor(polyop1_factor)
        else:
            polyop2_factor = tdi2.calc_polyop_factor(f, ltt)
            ans = calc_noise_ro_corr_factor(polyop1_factor, polyop2_factor)
        return ans 
        
    def calc_gw_response(self, longitude, latitude, f, t, tdi):
        """Calculate response function to GW of TDI channel.
        
        Parameters
        ----------
        longitude : float or array_like
        latitude : float or array_like
        f : float or array_like
        t : float or array_like
        tdi : TDI
        """
        f = np.asarray(f)
        longitude = np.asarray(longitude)
        latitude = np.asarray(latitude)
        n_ndim = longitude.ndim


        ltt = self.orbit.calc_ltt(t)
        p_sc = self.orbit.calc_sc_position(t)
        cg = p_sc.sum / 3.
        p_recv = p_sc - cg      #position relative to CG
        vec_arm = self.orbit.calc_arm_vector(t)
        tdi_factor = tdi.calc_polyop_factor(f, ltt)
        ans_p = 0.
        ans_c = 0.

        for mosa in MOSA_LABELS:
            sc = mosa[0]
            l_arm = np.linalg.norm(vec_arm[mosa], axis=-1, keepdims=True)
            vec_u = vec_arm[mosa] / l_arm
            rp, rc = calc_oneway_response(longitude, latitude, f, ltt[mosa], vec_u, p_recv[sc])
            ans_p += tdi_factor[mosa][(...,)+(None,)*n_ndim] * rp
            ans_c += tdi_factor[mosa][(...,)+(None,)*n_ndim] * rc
        return ans_p, ans_c
    
    def calc_orf(self, f, t, tdi1, tdi2=None):
        """Calculate ORF between TDI channels.

        Parameters
        ----------
        f : float or np.ndarray
        t : float or np.ndarray
        tdi1, tdi2 : TDI
        """
        nside = 14
        nsource = hlp.nside2npix(nside)
        colatitude, longitude = hlp.pix2ang(nside=nside, ipix=np.arange(nsource))
        latitude = PI_2 - colatitude
        rp1, rc1 = self.calc_gw_response(longitude, latitude, f, t, tdi1)
        if tdi2 is None:
            ans = (np.abs(rp1)**2 + np.abs(rc1)**2) / 2.
        else:
            rp2, rc2 = self.calc_gw_response(longitude, latitude, f, t, tdi2)
            ans = (rp1 * np.conjugate(rp2) + rc1 * np.conjugate(rc2)) / 2.
        ans = np.mean(ans, axis=-1)
        return ans
    
    # def calc_orfI(self, f, t, tdi1, tdi2=None):
    #     """Calculate ORFI of two tdi channels.

    #     Parameters
    #     ----------
    #     f : np.ndarray
    #         Frequency.
    #     t : float
    #         Time to evaluate at.
    #     tdi1 : TDI or MOSADict.
    #     tdi2 : TDI
    #     """
    #     ltt = self.orbit.calc_ltt(t)
    #     p_sc = self.orbit.calc_sc_position(t)
    #     arm_vec = self.orbit.calc_arm_vector(t)
    #     arm_length = MOSADict({mosa: np.linalg.norm(arm_vec[mosa]) for mosa in MOSA_LABELS})
    #     sen = TDISensitivity(p_sc, arm_vec/arm_length, ltt)
    #     if isinstance(tdi1, TDI):
    #         tdi1_factor = tdi1.calc_polyop_factor(f, ltt)
    #     else:
    #         tdi1_factor = tdi1
    #     if tdi2 is None:
    #         ans = sen.TDI_average_response(f, tdi1_factor)
    #     elif isinstance(tdi2, TDI):
    #         tdi2_factor = tdi2.calc_polyop_factor(f, ltt)
    #         ans = sen.TDI_average_correlation(f, tdi1_factor, tdi2_factor)
    #     else:
    #         tdi2_factor = tdi2
    #         ans = sen.TDI_average_correlation(f, tdi1_factor, tdi2_factor)
    #     return ans
        
def calc_noise_acc_factor(delayop_factor, polyop_factor):
    """Calculate tdi transform factor of ACC noise .
    P_ij + P_ji * D_ji

    Parameters
    ----------
    delayop_factor : MOSADict
        [..., freq]
    polyop_factor : MOSADict
        [..., freq]
    """
    ans = polyop_factor + polyop_factor.reverse * delayop_factor.reverse
    return ans

def calc_noise_acc_corr_factor(delayop_factor, polyop1_factor, polyop2_factor=None):
    """Calculate tdi correlation factor of ACC noise.
    
    Parameters
    ----------
    delayop_factor : MOSADict
        [..., freq]
    polyop_factor : MOSADict
        [..., freq]
    """
    if polyop2_factor is None:
        ans = abs(calc_noise_acc_factor(delayop_factor, polyop1_factor))**2
    else:
        ans = calc_noise_acc_factor(delayop_factor, polyop1_factor) * np.conj(
                calc_noise_acc_factor(delayop_factor, polyop2_factor))
    return ans

def calc_noise_ro_factor(polyop_factor):
    return polyop_factor

def calc_noise_ro_corr_factor(polyop1_factor, polyop2_factor=None):
    if polyop2_factor is None:
        ans = abs(calc_noise_ro_factor(polyop1_factor))**2
    else:
        ans = calc_noise_ro_factor(polyop1_factor) * np.conj(
                calc_noise_ro_factor(polyop2_factor))
    return ans

def calc_oneway_response(longitude, latitude, f, ltt, vec_u, p_recv):
    """Calculate one-way response function.
    
    Parameters
    ----------
    longitude : float or array_like
    latitude : float or array_like
    f : float or array_like
        Frequency
    ltt : float or array_like
    vec_u : array_like
        Unit arm vector [ltt, coords].
    p_recv : array_like
        Position of receiver [ltt, coords].

    Returns
    -------
    tuple
        Response to plus and cross mode, [ltt, f, longitude].
    """
    longitude = np.asarray(longitude)
    latitude = np.asarray(latitude)
    f = np.asarray(f)
    ltt = np.asarray(ltt)
    vec_u = np.asarray(vec_u)
    p_recv = np.asarray(p_recv)

    fltt = np.multiply.outer(f, ltt)
    if not np.isscalar(fltt):
        fltt = fltt[(...,) + (None,)*longitude.ndim]
    theta = PI_2 - latitude
    phi = longitude

    vec_n, vec_theta, vec_phi = calc_sphere_frame(theta, phi)
    ndotu_1 = np.tensordot(vec_u, vec_n, axes=(-1,-1)) + 1.
    thetadotu = np.tensordot(vec_u, vec_theta, axes=(-1,-1))
    phidotu = np.tensordot(vec_u, vec_phi, axes=(-1,-1))
    ndotprecv = np.tensordot(p_recv/C, vec_n, axes=(-1,-1))

    pre_factor = -1.j * PI * fltt
    sinc_factor = np.sinc(fltt * ndotu_1)
    exp_factor = np.exp(pre_factor * ndotu_1)
    recv_factor = np.exp(2.j * PI * np.multiply.outer(f, ndotprecv))
    factor = pre_factor * sinc_factor * exp_factor * recv_factor
    ep = thetadotu**2 - phidotu**2
    ec = 2. * thetadotu * phidotu

    rp = factor * ep
    rc = factor * ec
    if (f_ndim:=f.ndim != 0) and (ltt_ndim:=ltt.ndim != 0):
        old_axes = np.arange(f_ndim)
        new_axes = old_axes + ltt_ndim
        rp = np.moveaxis(rp, old_axes, new_axes)
        rc = np.moveaxis(rc, old_axes, new_axes)
    return rp, rc
