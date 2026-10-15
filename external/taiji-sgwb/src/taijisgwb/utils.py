import numpy as np
from .constants import PI, HUBBLE0

def calc_sphere_frame(theta, phi):
    """Calculate vector frame on unitsphere.
    
    Parameters
    ----------
    theta :
        Polar angle.
    phi : 
        Azimuth angle.

    Returns
    -------
    tuple
        Shape of items is [..., coords].
    """
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)

    vec_r = np.stack([sin_theta*cos_phi, sin_theta*sin_phi, cos_theta], axis=-1)
    vec_theta = np.stack([cos_theta*cos_phi, cos_theta*sin_phi, -sin_theta], axis=-1)
    vec_phi = np.stack([-sin_phi, cos_phi, np.zeros_like(sin_theta)], axis=-1)
    return vec_r, vec_theta, vec_phi

def calc_tensor_basis(u, v):
    """Calculate tensor basis of GW.
    
    Parameters
    ----------
    u, v : 
        The last axis denotes x, y, z components.

    Returns
    -------
    tuple
        Shape of items is [..., coords, coords]
    """
    e_plus = np.multiply.outer(u, u) - np.multiply.outer(v, v)
    e_cross = np.multiply.outer(u, v) + np.multiply.outer(v, u)
    return e_plus, e_cross

def psd_from_omega(f, omega):
    """ Convert omega of SGWB to PSD.
    
    Parameters
    ----------
    f : float or np.ndarray
        Frequency.
    omega : float | np.ndarray
        Omega.
    
    Returns
    -------
    float or np.ndarray
        PSD of SGWB.
    """
    return 3 * HUBBLE0**2 / 2 / PI**2 / f**3 * omega

def omega_from_psd(f, psd):
    """ Convert PSD to omega."""
    return 2 * PI**2 * f**3 / 3 / HUBBLE0**2 * psd