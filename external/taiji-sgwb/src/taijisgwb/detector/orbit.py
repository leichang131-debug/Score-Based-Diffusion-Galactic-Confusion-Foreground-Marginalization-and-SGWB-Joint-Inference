import numpy as np
from scipy.interpolate import interp1d
import h5py

from .constants import L_ARM, MOSA_LABELS, SC_LABELS
from ..constants import SQRT3, C, TWOPI, YRSID, AU
from .data import SCDict

class InterpolationOrbit:
    """Orbit from file.
    
    Parameters
    ----------
    orbit_filename : str
    """
    def __init__(self, orbit_filename):
        self.sc_position_sample = {}
        with h5py.File(orbit_filename, "r") as h5file:
            self.ltt_sample = {mosa: h5file["tcb"][f"l_{mosa}"][()] for mosa in MOSA_LABELS}
            for sc in SC_LABELS:
                sc_position_sample = h5file["tcb"][f"sc_{sc}"][()]
                self.sc_position_sample[sc] = np.stack(
                    [sc_position_sample['x'], sc_position_sample['y'], sc_position_sample['z']], 
                    axis=-1) 
            self.t_sample = h5file["tcb"]["t"][()]
        self.ltt_interp = {mosa: interp1d(self.t_sample, self.ltt_sample[mosa], kind="cubic") 
                           for mosa in MOSA_LABELS}
        self.sc_position_interp = {sc: interp1d(self.t_sample, self.sc_position_sample[sc], axis=0, kind="cubic")
                                   for sc in SC_LABELS}


    def calc_ltt(self, t):
        """Calculate light travel times.
        
        Parameters
        ----------
        t : float or np.ndarray
            Time to evaluate at.
        """
        ans = {mosa: self.ltt_interp[mosa](t) for mosa in MOSA_LABELS}
        return ans

    def calc_sc_position(self, t):
        """Calculate position of SC.
        """
        ans = {sc: self.sc_position_interp[sc](t) for sc in SC_LABELS}
        return SCDict(ans)

    def calc_arm_vector(self, t):
        """Calculate arm vector."""
        mosa_position = self.calc_sc_position(t).MOSA
        ans = mosa_position - mosa_position.reverse
        return ans

class EqualArmOrbit:
    """Equal arm analytic orbit from LISA data challenge manual.
    
    Parameters
    ----------
    l_arm : float
        Armlength.
    alpha0 : float
        Initial ecliptic angle.
    beta0 : float
        Inital self rotation angle.
    """
    def __init__(self, l_arm=L_ARM, alpha0=1.40281201, beta0=4.54255889):
        self.l_arm = L_ARM
        self.alpha0 = alpha0
        self.beta0 = beta0

    def calc_ltt(self, t):
        ltt = self.l_arm / C
        ans = {mosa: np.full_like(t, ltt, dtype=np.float64) for mosa in MOSA_LABELS}
        return ans
    
    def calc_sc_position(self, t):
        t = np.asarray(t)
        l_arm_div_twosqrtthree = .5 * self.l_arm / SQRT3 
        alpha = TWOPI * t / YRSID + self.alpha0
        sin_alpha = np.sin(alpha)
        cos_alpha = np.cos(alpha)
        sin_cos_alpha = sin_alpha * cos_alpha
        ans = {}
        for sc in SC_LABELS:
            beta = TWOPI / 3 * (int(sc) - 1) + self.beta0
            sin_beta = np.sin(beta)
            cos_beta = np.cos(beta)
            x = AU * cos_alpha + l_arm_div_twosqrtthree * (
                sin_cos_alpha * sin_beta - (1 + sin_alpha**2) * cos_beta
            )
            y = AU * sin_alpha + l_arm_div_twosqrtthree * (
                sin_cos_alpha * cos_beta - (1 + cos_alpha**2) * sin_beta
            )
            z = -.5 * self.l_arm * np.cos(alpha - beta)
            sc_position = np.stack([x, y, z], axis=-1)
            ans[sc] = sc_position
        return SCDict(ans)
    
    def calc_arm_vector(self, t):
        mosa_position = self.calc_sc_position(t).MOSA
        ans = mosa_position - mosa_position.reverse
        return ans