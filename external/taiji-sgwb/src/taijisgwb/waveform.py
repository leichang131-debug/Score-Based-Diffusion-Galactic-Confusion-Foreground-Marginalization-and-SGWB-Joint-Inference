#Energy spectrum of SGWB.
import numpy as np

def calc_omega_powerlaw(freq, omega0, alpha, freq0=1e-3):
    """Power law SGWB.
    
    Parameters
    ----------
    freq : np.ndarray
        Frequency.
    omega0 : float
        Strength at reference frequency.
    alpha : float
        Exponent.
    freq0 : float
        Reference frequency.
    """
    ans = omega0 * (freq / freq0)**alpha
    return ans

def calc_omega_dbpowerlaw(freq, amp_pt, f_pt, rb, b):
    """Double broken power law SGWB.
    
    Used for phase transition.

    Parameters
    ----------
    freq : np.ndarray
        Frequency.
    ...
    """
    s = freq / f_pt
    rb4 = rb**4
    bplus4 = b + 4
    m = (9 * rb4 + b) / (rb4 + 1)
    ans = amp_pt * s**9 * ((1 + rb4) / (rb4 + s**4))**((9-b)/4) * (
        bplus4 / (bplus4 - m + m * s**2))**(bplus4/2)
    return ans