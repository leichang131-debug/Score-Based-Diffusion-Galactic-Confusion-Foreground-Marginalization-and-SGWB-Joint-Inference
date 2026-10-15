from collections import defaultdict
import numpy as np

from .constants import MOSA_LABELS, CYCLIC_RULE
from .data import MOSADict
from ..constants import TWOPI, SQRT2, SQRT3, SQRT6

class DelayPolynomial:
    """Polynomial consists of delay operator.

    Parameters
    ----------
    polynomial : list
        List consists of tuples storing terms of polynomial.
    """
    def __init__(self, polynomial):
        self.polynomial = self._collect(polynomial)

    def __repr__(self):
        return f"{self.polynomial}"

    def __neg__(self):
        polynomial_new = []
        for (coef, op) in self.polynomial:
            polynomial_new.append((-coef, op))
        return DelayPolynomial(polynomial_new)

    def __add__(self, other):
        if np.isscalar(other):
            polynomial_new = self.polynomial + [(other, [])]
        else:
            polynomial_new = self.polynomial + other.polynomial
        return DelayPolynomial(polynomial_new)
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        polynomial_new = []
        if np.isscalar(other):
            for coef, op in self.polynomial:
                polynomial_new.append((coef * other, op))
        else:
            for term1 in self.polynomial:
                coef1, op1 = term1
                for term2 in other.polynomial:
                    coef2, op2 = term2
                    coef_new = coef1 * coef2
                    op_new = op1 + op2
                    polynomial_new.append((coef_new, op_new))
        return DelayPolynomial(polynomial_new)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __truediv__(self, other):
        polynomial_new = []
        if np.isscalar(other):
            for coef, op in self.polynomial:
                polynomial_new.append((coef / other, op))
        else:
            raise ValueError("DelayPolynomial does only support scalar division.")
        return DelayPolynomial(polynomial_new)

    @staticmethod
    def _collect(polynomial):
        """Merge similar terms and delete terms with zero coefficient.
        
        Parameters
        ----------
        polynomials : list
            List consists of tuples storing terms of polynomial. 
        """
        polynomial_dict = defaultdict(float)
        for (coef, op) in polynomial:
            key = tuple(op)
            polynomial_dict[key] += coef
        polynomial_new = [(coef, list(key)) for key, coef in polynomial_dict.items()
                          if coef != 0.]
        return polynomial_new

    def calc_polyop_factor(self, f, ltt):
        """Calculate the coefficients in frequency domain.

        Supposing commutativity and ignore doppler correction.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.
        ltt : dict or float
            Light travel time.
        """
        ans = np.zeros_like(f, dtype=complex)
        if np.isscalar(ltt):
            for coef, op in self.polynomial:
                ltt_sum = ltt * len(op)
                ans += coef * np.exp(-1j * TWOPI * f * ltt_sum)
        else:
            for coef, op in self.polynomial:
                ltt_sum = 0.
                for op_ in op:
                    ltt_sum += ltt[op_]
                # if not op:
                ans = ans + coef * np.exp(-1j * TWOPI * np.multiply.outer(ltt_sum, f))
        return ans

class TDI:
    """TDI.

    Parameters
    ----------
    polynomials : dict
        Each of the items stores delay polynomial.
    """
    def __init__(self, polynomials):
        self.polynomials = {}
        for key, val in polynomials.items():
            if isinstance(val, DelayPolynomial):
                self.polynomials[key] = val
            else: 
                self.polynomials[key] = DelayPolynomial(val)

    def __repr__(self):
        return f"{self.polynomials}"
    
    @property
    def cyclic(self):
        polynomials_new = {}
        for key, val in self.polynomials.items():
            key_new = _replace_string(key, CYCLIC_RULE)
            val_new = []
            for val_ in val.polynomial:
                coef_new, op = val_
                val_new.append((coef_new, _replace_list(op, CYCLIC_RULE)))
            polynomials_new[key_new] = val_new
        return TDI(polynomials_new)
    
    def calc_polyop_factor(self, f, ltt):
        """Calculate the coefficients in frequency domain.
        
        Parameters
        ----------
        f : np.ndarray
            Frequency.
        ltt : dict or float
            Light travel time.
        """
        ans = {}
        for mosa in MOSA_LABELS:
            ans[mosa] = self.polynomials[mosa].calc_polyop_factor(f, ltt)
        return MOSADict(ans)
    

def calc_delayop_factor(f, ltt):
    """Calculate the coefficients of delay operatorin frequency domain.
    
    Parameters
    ----------
    f : np.ndarray
        Frequency.
    ltt : dict or float
        Light travel time.
    """
    if np.isscalar(ltt):
        ans = np.exp(-1j * TWOPI * f * ltt)
        ans = {mosa: ans for mosa in MOSA_LABELS}
    else: 
        ans = {}
        for mosa in MOSA_LABELS:
            ans[mosa] = np.exp(-1j * TWOPI * np.multiply.outer(ltt[mosa], f))
    return MOSADict(ans)

def aet_from_xyz(X, Y, Z):
    """Calculate A, E, T from X, Y, Z.
    
    Parameters
    ----------
    X : np.ndarray
        Data of TDI-X channel.
    Y : np.ndarray
        Data of TDI-Y channel.
    Z: np.ndarray
        Data of TDI-Z channel.
    """
    A = (Z - X) / SQRT2
    E = (X - 2 * Y + Z) / SQRT6
    T = (X + Y + Z) / SQRT3
    return A, E, T

def tdi_aet_from_tdi_x(tdi_X):
    """Generate A, E, T TDI from X TDI.
    
    Parameters
    tdi_X : TDI
        TDI of X channel.
    """
    tdi_Y = tdi_X.cyclic
    tdi_Z = tdi_Y.cyclic
    tdi_A = {}
    tdi_E = {}
    tdi_T = {}
    for mosa in MOSA_LABELS:
        tdi_A[mosa], tdi_E[mosa], tdi_T[mosa] = aet_from_xyz(tdi_X.polynomials[mosa], 
                                                             tdi_Y.polynomials[mosa],
                                                             tdi_Z.polynomials[mosa])
    return TDI(tdi_A), TDI(tdi_E), TDI(tdi_T)

def _replace_string(s, rule):
    """Replace characters of string with a rule.
    
    Parameters
    ----------
    s : str
        String to be replaced.
    rule : dict
        Replace rule.
    """
    return "".join(rule[char] for char in s)

def _replace_list(lst, rule):
    """Replace list of strings with a rule.
    
    Parameters
    ----------
    lst : list
        List of strings.
    rule : dict
        Replace rule.
    """
    return [_replace_string(s, rule) for s in lst]



tdi_X2 = TDI(
    {
        "12": [(1.0, []), (-1.0, ["13", "31"]), (-1.0, ["13", "31", "12", "21"]), (1.0, ["12", "21", "13", "31", "13", "31"])],
        "23": [],
        "31": [(-1.0, ["13"]), (1.0, ["12", "21", "13"]), (1.0, ["12", "21", "13", "31", "13"]), (-1.0, ["13", "31", "12", "21", "12", "21", "13"])],
        "21": [(1.0, ["12"]), (-1.0, ["13", "31", "12"]), (-1.0, ["13", "31", "12", "21", "12"]), (1.0, ["12", "21", "13", "31", "13", "31", "12"])],
        "32": [],
        "13": [(-1.0, []), (1.0, ["12", "21"]), (1.0, ["12", "21", "13", "31"]), (-1.0, ["13", "31", "12", "21", "12", "21"])],
    }
)
tdi_Y2 = tdi_X2.cyclic
tdi_Z2 = tdi_Y2.cyclic