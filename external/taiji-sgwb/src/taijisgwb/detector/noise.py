import numpy as np

from .constants import *
from ..constants import TWOPI, C

class InterferometerNoisePSD:
    """Grouping noise PSD of interferometer.
    """
    @staticmethod
    def calc_psd_las(f):
        """PSD function of laser noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of laser noise.
        """
        return np.zeros_like(f)

    @staticmethod
    def calc_psd_acc(f):
        """PSD function of TM acceleration noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of TM acceleration noise.
        """
        return np.zeros_like(f)
    
    @staticmethod
    def calc_psd_ro(f):
        """PSD function of readout noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of readout noise.
        """
        return np.zeros_like(f)
    
    @staticmethod
    def calc_psd_ob(f):
        """PSD function of optical bench noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of optical bench noise.
        """
        return np.zeros_like(f)
    
    @staticmethod
    def calc_psd_bl(f):
        """PSD function of backlink noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of backlink noise.
        """
        return np.zeros_like(f)
    
    @staticmethod
    def calc_psd_op(f):
        """PSD function of optical path noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of optical path noise.
        """
        return np.zeros_like(f)
    
class TaijiNoisePSD(InterferometerNoisePSD):
    """Grouping noise PSD of taiji.
    """
    @staticmethod
    def calc_psd_acc(f, a_acc=A_ACC):
        """PSD function of TM acceleration noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of TM acceleration noise.
        """
        u = TWOPI * f * C
        ans = (a_acc / u)**2 * (1 + (.4e-3 / f)**2) * (1 + (f / 8e-3)**4)
        return ans
    
    @staticmethod
    def calc_psd_ro(f, a_ro=A_RO):
        """PSD function of readout noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of readout noise.
        """
        u = TWOPI * f / C
        ans = (a_ro * u)**2 * (1 + (2e-3 / f)**4)
        return ans
    
    @staticmethod
    def calc_psd_bl(f, a_bl=A_BL):
        """PSD function of backlink noise.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.

        Returns
        -------
        np.ndarray
            PSD of backlink noise.
        """
        u = TWOPI * f / C
        ans = (a_bl * u)**2 * (1 + (2e-3 / f)**4)
        return ans