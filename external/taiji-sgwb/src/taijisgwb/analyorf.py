#WARNING: this module is buggy and has NOT been used at present.
import numpy as np
from scipy.special import expi

from .constants import PI, TWOPI, C

def _get_Ei(alpha, z1, z2):
    """Calculate Ei items in ORF.
    #TODO: on negative real axis, on 0. 
    
    Parameters
    ----------
    alpha : np.ndarray
        2 * pi * f * d / c. 
    z1 : complex
        Lower bound.
    z2 : complex
        Upper bound.
    """
    z1_alpha = -1j * alpha * z1
    z2_alpha = -1j * alpha * z2
    ans = expi(z2_alpha) - expi(z1_alpha)
    if np.imag(z1) < 0.:
        sign1 = np.sign(np.real(z1))
        sign2 = np.sign(np.real(z2))
        if sign1 != sign2:
            ans -= 1.j * sign1 * TWOPI
    return ans

def _orfI_oneitem(alpha, proj_u1, proj_u2, gamma, d):
    """One item in ORF_I of oneway tracking.
    
    Parameters
    ----------
    alpha : np.ndarray
        2 * pi * f * d / c.
    proj_u1 : float
        Projection of d on u1.
    proj_u2 : float
        Projection d on u2.
    gamma : float
        Angle between u1 and u2.
    d : float
        Distance between receive points.
    """
    mask = alpha < 1e-5
    cos_gamma = np.cos(gamma)
    if alpha0_flag := np.any(mask):
        ans0 = 2. * TWOPI * (1. + cos_gamma / 3) 
        if gamma > 1e-5:
            ans0 += 8. * TWOPI * (1. - cos_gamma) * np.log(np.sin(gamma / 2))
    if np.all(mask):
        return np.full_like(alpha, ans0, dtype=complex)
    
    alpha = alpha[~mask]
    cos_alpha = np.cos(alpha)
    sin_alpha = np.sin(alpha)
    onej_alpha = 1j * alpha
    cos_delta1 = proj_u1 / d
    cos_delta2 = proj_u2 / d
    sin_gamma = np.sin(gamma)
    sinc_alpha = sin_alpha / alpha
    cos_min_sinc_alpha = cos_alpha - sinc_alpha
    ans_noexpi = -4j * PI * (cos_delta1 + cos_delta2) * cos_min_sinc_alpha / alpha
    ans_noexpi += TWOPI * (3. * cos_delta1 * cos_delta2 - cos_gamma) * (
                    2 * cos_min_sinc_alpha / alpha**2 + sinc_alpha)
    ans_noexpi_coef1 = 2. - 7. * cos_gamma - cos_delta1 * cos_delta2
    ans_noexpi_coef2 = 0.

    delta1_0flag = cos_delta1 > (1 - 1e-10)
    delta1_piflag = cos_delta1 < (-1 + 1e-10)
    delta2_0flag = cos_delta2 > (1 - 1e-10)
    delta2_piflag = cos_delta2 < (-1 + 1e-10)

    if delta1_0flag or delta1_piflag:
        ans_noexpi_coef1 += 2. * cos_delta2 if delta1_0flag else -2. * cos_delta2
        ans_noexpi_coef2 += .5 * cos_delta2 * (cos_alpha - np.exp(onej_alpha * cos_delta1))
    else: 
        csc2_delta1 = 1. / (1. - cos_delta1**2)
        ans_noexpi_coef1 += 4. * (cos_gamma - cos_delta1 * cos_delta2) * csc2_delta1
        ans_noexpi_coef2 += (cos_delta2 - cos_delta1 * cos_gamma) * (cos_alpha - np.exp(onej_alpha * cos_delta1)) * csc2_delta1
    if delta2_0flag or delta2_piflag:
        ans_noexpi_coef1 += 2. * cos_delta1 if delta2_0flag else -2. * cos_delta1
        ans_noexpi_coef2 += .5 * cos_delta1 * (cos_alpha - np.exp(onej_alpha * cos_delta2))
    else:
        csc2_delta2 = 1. / (1. - cos_delta2**2)
        ans_noexpi_coef1 += 4. * (cos_gamma - cos_delta1 * cos_delta2) * csc2_delta2
        ans_noexpi_coef2 += (cos_delta1 - cos_delta2 * cos_gamma) * (cos_alpha - np.exp(onej_alpha * cos_delta2)) * csc2_delta2
    ans_noexpi += TWOPI * sinc_alpha * ans_noexpi_coef1
    ans_noexpi += 8j * PI * ans_noexpi_coef2 / alpha

    if sin_gamma < 1e-5:
        ans_expi = 0.
    elif delta1_0flag:
        z1 = 1 - cos_delta2
        ans_expi = -8 * PI * (1 - cos_gamma) * _get_Ei(alpha, z1, 2) * np.exp(onej_alpha)
    elif delta1_piflag:
        z1 = 1 - cos_delta1
        ans_expi = -8 * PI * (1 - cos_gamma) * _get_Ei(alpha, z1, 2) * np.exp(-onej_alpha)
    elif delta2_0flag:
        z2 = -1 - cos_delta2
        ans_expi = 8 * PI * (1 - cos_gamma) * _get_Ei(alpha, -2, z2) * np.exp(onej_alpha)
    elif delta2_piflag:
        z2 = -1 - cos_delta1
        ans_expi = 8 * PI * (1 - cos_gamma) * _get_Ei(alpha, -2, z2) * np.exp(-onej_alpha)
    else:
        u = np.sqrt(np.abs(sin_gamma**2 - cos_delta1**2 - cos_delta2**2 + 
                2 * cos_gamma * cos_delta1 * cos_delta2))
        sigmap = (cos_delta1 + cos_delta2 + 1j*u) / (1 + cos_gamma)
        sigmam = np.conj(sigmap)
        z1 = sigmam - 1
        z2 = sigmam - cos_delta1
        ans_expi1 = _get_Ei(alpha, z1, z2)
        z1 = sigmam - cos_delta2
        z2 = sigmam + 1
        ans_expi1 -= _get_Ei(alpha, z1, z2)
        ans_expi1 *= np.exp(onej_alpha * sigmam)

        z1 = sigmap - cos_delta1
        z2 = sigmap + 1
        ans_expi2 = _get_Ei(alpha, z1, z2)
        z1 = sigmap - 1
        z2 = sigmap - cos_delta2
        ans_expi2 -= _get_Ei(alpha, z1, z2)
        ans_expi2 *= np.exp(onej_alpha * sigmap)
    
        ans_expi = 4 * PI * (1 - cos_gamma) * (ans_expi1 - ans_expi2)
    
    ans = np.empty_like(mask, dtype=complex)
    ans[~mask] = ans_expi + ans_noexpi
    if alpha0_flag:
        ans[mask] = ans0
    return ans

def _orfV_oneitem(alpha, proj_u1, proj_u2, gamma, d):
    """One item in ORF_V of oneway tracking.
    
    Parameters
    ----------
    alpha : np.ndarray
        2 * pi * f * d / c.
    delta1 : float
        Angle between d and u1.
    delta2 : float
        Angle between d and u2.
    gamma : float
            Angle between u1 and u2.
    """
    mask = alpha > 1e-5
    ans = np.zeros_like(mask, dtype=complex)
    cos_delta1 = proj_u1 / d
    cos_delta2 = proj_u2 / d
    sin_gamma = np.sin(gamma)

    delta1_flag = cos_delta1 > (1 - 1e-5) or cos_delta1 < (-1 + 1e-5)
    delta2_flag = cos_delta2 > (1 - 1e-5) or cos_delta2 < (-1 + 1e-5)
    gamma_flag = sin_gamma < 1e-5

    if not np.any(mask) or delta1_flag or delta2_flag or gamma_flag:
        return ans

    alpha = alpha[mask]
    cos_alpha = np.cos(alpha)
    sin_alpha = np.sin(alpha)
    onej_alpha = 1j * alpha
    csc2_delta1 = 1. / (1. - cos_delta1**2)
    csc2_delta2 = 1. / (1. - cos_delta2**2)
    cos_gamma = np.cos(gamma)
    
    u = np.sqrt(sin_gamma**2 - cos_delta1**2 - cos_delta2**2 + 
                2 * cos_gamma * cos_delta1 * cos_delta2)
    sigmap = (cos_delta1 + cos_delta2 + 1j*u) / (1 + cos_gamma)
    sigmam = np.conj(sigmap)

    z1 = sigmam - 1
    z2 = sigmam - cos_delta1
    ans1 = _get_Ei(alpha, z1, z2)
    z1 = sigmam - cos_delta2
    z2 = sigmam + 1
    ans1 -= _get_Ei(alpha, z1, z2)
    ans1 *= np.exp(onej_alpha * sigmam)

    z1 = sigmap - cos_delta1
    z2 = sigmap + 1
    ans2 = _get_Ei(alpha, z1, z2)
    z1 = sigmap - 1
    z2 = sigmap - cos_delta2
    ans2 -= _get_Ei(alpha, z1, z2)
    ans2 *= np.exp(onej_alpha * sigmap)

    ans_ = -4 * PI * (1 - cos_gamma) * (ans1 + ans2)

    ans3 = (np.exp(onej_alpha * cos_delta1) * csc2_delta1 + 
            np.exp(onej_alpha * cos_delta2) * csc2_delta2)
    ans3 -= cos_alpha * (csc2_delta1 + csc2_delta2)
    ans3 += cos_alpha - sin_alpha / alpha
    ans3 -= 1j * sin_alpha * (cos_delta1 * csc2_delta1 + cos_delta2 * csc2_delta2)
    ans3 *= -8 * PI * u / alpha

    ans_ += ans3

    ans[mask] = ans_
    return ans

def _orf_oneway(freq, proj_u1, proj_u2, gamma, l1, l2, d, orf_oneitem_fun):
    """ORF of oneway tracking.
    
    Parameters
    ----------
    freq : np.ndarray
        Frequency.
    proj_u1 : float
        Projection of d on u1.
    proj_u2 : float
        Projection of d on u2.
    l1 : float
        Length of path1.
    l2 : float
        Length of path2.
    gamma : float
        Angle between u1 and u2.
    d : float
        Distance between receive points.
    orf_oneitem_fun : callable
        Function calculating one item of orf.
    """
    freq = np.atleast_1d(np.asanyarray(freq))
    coef = TWOPI * freq / C
    cos_gamma = np.cos(gamma)
    alpha = coef * d

    l1_cos_gamma = l1 * cos_gamma
    l2_cos_gamma = l2 * cos_gamma

    ans = orf_oneitem_fun(alpha, proj_u1, proj_u2, gamma, d)

    d_ = np.sqrt(d**2 + l1**2 + 2 * l1 * proj_u1)
    alpha_ = coef * d_ 
    proj_u1_ = proj_u1 + l1
    proj_u2_ = proj_u2 + l1_cos_gamma
    coef_beta1 = np.exp(-1j * coef * l1)
    ans -= coef_beta1 * orf_oneitem_fun(
                alpha_, proj_u1_, proj_u2_, gamma, d_)
    
    d_ = np.sqrt(d**2 + l2**2 - 2 * l2 * proj_u2)
    alpha_ = coef * d_ 
    proj_u1_ = proj_u1 - l2_cos_gamma
    proj_u2_ = proj_u2 - l2
    coef_beta2 = np.exp(1j * coef * l2)
    ans -= coef_beta2 * orf_oneitem_fun(
                alpha_, proj_u1_, proj_u2_, gamma, d_)

    d_ = np.sqrt(max(d**2 + l1**2 + l2**2 + 2 * l1 * proj_u1
                 - 2 * l2 * proj_u2 - 2 * l1 * l2_cos_gamma, 0.))
    alpha_ = coef * d_
    proj_u1_ += l1
    proj_u2_ += l1_cos_gamma
    coef_beta3 = coef_beta2 * coef_beta1 
    ans += coef_beta3 * orf_oneitem_fun(
            alpha_, proj_u1_, proj_u2_, gamma, d_)

    return ans

def calculate_orfI_oneway(freq, proj_u1, proj_u2, gamma, l1, l2, d):
    """ORF_I of oneway tracking.
    
    Parameters
    ----------
    freq : np.ndarray
        Frequency.
    delta1 : float
        Angle between d and u1.
    delta2 : float
        Angle between d and u2.
    l1 : float
        Length of path1.
    l2 : float
        Length of path2.
    gamma : float
        Angle between u1 and u2.
    d : float
        Distance between receive points.
    """
    return _orf_oneway(freq, proj_u1, proj_u2, gamma, l1, l2, d,
                       _orfI_oneitem)

def calculate_orfV_oneway(freq, proj_u1, proj_u2, gamma, l1, l2, d):
    """ORF_I of oneway tracking.
    
    Parameters
    ----------
    freq : np.ndarray
        Frequency.
    delta1 : float
        Angle between d and u1.
    delta2 : float
        Angle between d and u2.
    l1 : float
        Length of path1.
    l2 : float
        Length of path2.
    gamma : float
        Angle between u1 and u2.
    d : float
        Distance between receive points.
    """
    return _orf_oneway(freq, proj_u1, proj_u2, gamma, l1, l2, d,
                       _orfV_oneitem)