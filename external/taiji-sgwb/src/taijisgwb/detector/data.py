from collections import UserDict
import numpy as np
from .constants import MOSA_LABELS, ADJMOSA_LABELS, SC_LABELS, CYCLIC_RULE

class LabelDict(UserDict):
    """Extend dictionary to support arithmetic.
    """
    def __repr__(self):
        return f"{dict(self)}"

    def __array__(self, dtype=object):
        return np.array(self.data, dtype=dtype)
    
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """
        Handle numpy ufuncs (e.g. np.conj, np.sin, np.add, etc.)
        """
        if method != "__call__":
            raise NotImplementedError
        
        ans = {}
        for key in self.keys():
            proc_inputs = []
            for inp in inputs:
                if isinstance(inp, LabelDict):
                    proc_inputs.append(inp[key])
                else:
                    proc_inputs.append(inp)
            
            res = ufunc(*proc_inputs, **kwargs)
            ans[key] = res
        
        return self.__class__(ans)
    
    def __neg__(self):
        return self.__class__({key: -val for key, val in self.items()})

    def __abs__(self):
        return self.__class__({key: np.abs(val) for key, val in self.items()})
    
    def __add__(self, other):
        dict_new = {}
        if type(self) == type(other):
            for key in self.keys():
                dict_new[key] = self[key] + other[key]
        else:
            for key in self.keys():
                dict_new[key] = self[key] + other
        return self.__class__(dict_new)
    
    def _radd__(self, other):
        return self.__add__(other)
    
    def __mul__(self, other):
        dict_new = {}
        if type(self) == type(other):
            for key in self.keys():
                dict_new[key] = self[key] * other[key]
        else:
            for key in self.keys():
                dict_new[key] = self[key] * other
            # raise TypeError(f"Unsupported operation between '{type(self)}' and '{type(other)}'.")
        return self.__class__(dict_new)

    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __sub__(self, other):
        dict_new = {}
        if type(self) == type(other):
            for key in self.keys():
                dict_new[key] = self[key] - other[key]
        else:
            for key in self.keys():
                dict_new[key] = self[key] - other
        return self.__class__(dict_new)

    def __rsub__(self, other):
        dict_new = {}
        if type(self) == type(other):
            for key in self.keys():
                dict_new[key] = other[key] - self[key]
        else:
            for key in self.keys():
                dict_new[key] = other - self[key]
        return self.__class__(dict_new)
    
    def __truediv__(self, other):
        dict_new = {}
        if type(self) == type(other):
            for key in self.keys():
                dict_new[key] = self[key] / other[key]
        else:
            for key in self.keys():
                dict_new[key] = self[key] / other
        return self.__class__(dict_new)
    
    def __rtruediv__(self, other):
        dict_new = {}
        if type(self) == type(other):
            for key in self.keys():
                dict_new[key] = other[key] / self[key]
        else:
            for key in self.keys():
                dict_new[key] = other / self[key]
        return self.__class__(dict_new)

    def __pow__(self, exponent):
        dict_new = {}
        for key in self.keys():
            dict_new[key] = self[key] ** exponent
        return self.__class__(dict_new)
    
    @property
    def sum(self):
        ans = np.zeros_like(next(iter(self.values())))
        for val in self.values():
            ans += val
        return ans

class MOSADict(LabelDict):
    def __setitem__(self, key, val):
        if key not in MOSA_LABELS:
            raise KeyError(f"'{key}' is not a supported key of MOSADict.")
        super().__setitem__(key, val)

    @property
    def reverse(self):
        """A new MOSADict with reverse labels."""
        dict_new = {}
        for key in self.keys():
            key_re = key[1] + key[0]
            dict_new[key] = self[key_re]
        return MOSADict(dict_new)
    
    @property
    def adjacent(self):
        """A new MOSADict with adjacent labels."""
        dict_new = {}
        for key in self.keys():
            key_ad = ADJMOSA_LABELS[key]
            dict_new[key] = self[key_ad]
        return MOSADict(dict_new)
    
    @property
    def to_array(self):
        """Transform to np.ndarray."""
        arrays = [self[mosa] for mosa in MOSA_LABELS]
        ans = np.stack(arrays)
        return ans


class SCDict(LabelDict):
    def __setitem__(self, key, val):
        if key not in SC_LABELS:
            raise KeyError(f"'{key}' is not a supported key of SCDict.")
        super().__setitem__(key, val)
    
    @property
    def MOSA(self):
        """Transform to MOSADict."""
        ans = {}
        for key in MOSA_LABELS:
            ans[key] = self[key[0]]
        return MOSADict(ans)
    
    @property
    def cyclic(self):
        """New SCDict with index cyclic."""
        ans = {}
        for key in SC_LABELS:
            ans[key] = self[CYCLIC_RULE[key]]
        return ans

        
    

        
    
               
