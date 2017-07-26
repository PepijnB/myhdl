#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2013 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module with the intbv class """
from __future__ import absolute_import, division
from math import floor, ceil, log
import operator

from myhdl._compat import long, integer_types, string_types, builtins
from myhdl._bin import bin
from myhdl._intbv import intbv


# Any fixed-point is a scaled integer, and can therefore be represented by a integer-value and a scaling factor,
# where the scaling-factor must be a integer-power of 2: scaling-factor = 2^shift, where the shift-factor can be any
# integer value (positive and negative). The shift factor is related to the fractionlength by the relation:
# fractionlength=-shift.
# By definition: RealWorldValue = StoredInteger * 2**shift
#
# Because a fixed-point number is a scaled integer, all fixed-point numbers lie on a 'grid' determined by the
# shift-factor. When the fixbv is initialized, the initialization-value might not lie on the grid. When this happens, the
# initialization-value is rounded to the nearest grid-point. The same holds for the 'min'- and 'max'-value.
#
# Eventhough all operations are performed in full-precision, without overflow handling or rounding, the 'min'- and 'max'-value
# can be provided. These values are used to determine the number of bits (nrbits) and when assigning the fixbv to a Signal.next 
# 'register'. During this assignment, the selected rounding mode and overflow mode is used (TODO: to be implemented).

# Guidelines
# -------------------------------------------------------
# * Precision:
#    Because (a) every fixed-point number is represented by an stored-integer and (b) python can handle integers of
#    infinite length, all operations within the fixbv-class can be (and are!) done with infinite precision.
#    Casting the fixbv to a float, might therefore cause for round-off errors or over-/underflow errors.
# * Quantization and overflow handling
#    The fixbv-class will do all operations in full-precision, therefore quantization and overflow handling will not be done.
#    These operations only make sense when the actual number is stored into a register. Therefore this should be handled by the
#    Signal-class. Unfortunately this choice was not made. Therefore the following behavior is used:
#     * at initialization: the min/max and nrbits values are optional, unless it is used to initiate a Signal, then it
#       is mandatory
#     * After any operation (add/sub/mult/etc) a fixbv without these fields, will be returned. This is done because one
#       can only make worstcase estimates about the min/max value and the nr-bits. Internal arithmetic is infinite
#       precision, the rounding and overflowhandling will be handled at assignment to Signal.next

#
# Food for thought:
#----------------------
# * Initialization:
#    When a floating-point-value is used as init-value, the shift-value is used to create a stored-integer-value. In this
#    process the nearest integer is taken, thus a round-to-nearest scheme is used.
# * Division:
#    In principle divisions are not defined for integers (and therefore also not for fixed-point-numbers), because N/K
#    does not result in an integer for all N and K combinations.
#    Python makes a distinction between a true-division and a floor-division. A true-division is what we normally use in
#    a mathematical operations in the real-world. The floor-division rounds the true-division to the integer
#    closest to -infinity.
# * Fraction-length and Word-length
#    the fraction-length equals -shift. The word-length is not known by the fixbv, since no overflow or quantization
#    will be performed. All operations are don in infinite precision and therefore overflow-handling and quantization
#    are not needed.


def alignvalues(a, b):
    # Example: a=100*2^10, b=10*2^2
    # After alignment, the values become: a' = 25600 * 2^2 and b'=b
    # This operation must happen without loss of resolution, which means that all values must remain integer at all time.

    assert isinstance(a, tuple) and len(a) == 2, 'It is assumed that the first input it a tuple of length 2'
    assert isinstance(b, tuple) and len(b) == 2, 'It is assumed that the second input it a tuple of length 2'
    a_val = a[0]
    a_shift = a[1]
    b_val = b[0]
    b_shift = b[1]

    if a_shift >= b_shift:
        diff_shift = a_shift - b_shift
        a_val = a_val * 2**diff_shift
        a_shift = b_shift
        return (a_val, a_shift),(b_val, b_shift)
    else:
        b, a = alignvalues(b, a)
        return a, b

def calc_nr_bits(val):
    if val == 0:
        a = 0
        nrbits = long(0)        # A bit arbitrary value; I chose to use same behavior as bit_length()-function
    elif val < 0:
        a = len(bin(val))
        nrbits = long(ceil(log(-val, 2)) + 1)
    else:
        a = len(bin(val)) + 1
        nrbits = long(ceil(log(val + 1, 2)) + 1)
    return nrbits

def fixbvstr_from_tuple(si, shift):
    return '%d * 2^%d' % (si, shift)

class fixbv(object):
    #__slots__ = ('_val', '_min', '_max', _shift'_handleBounds')

    # ------------------------------------------------------------------------------
    #                          ATTRIBUTES
    # ------------------------------------------------------------------------------
    _val = 0            # the stored integer value
    _shift = 0          # the shift value to obtain a real-world value
    _min = None
    _max = None

    # ------------------------------------------------------------------------------
    #                          PROPERTIES
    # ------------------------------------------------------------------------------
    # create the properties:
    #   * maxfloat       - the maximum value as integer (when the value does not have a fraction) or floating point number (when the value has a fraction)
    #   * minfloat       - the minimum value as integer (when the value does not have a fraction) or floating point number (when the value has a fraction)
    #   * maxsi          - the stored integer part of the maximum value
    #   * minsi          - the stored integer part of the minimum value
    #   * si             - stored integer value
    #   * shift          - shift value to obtain a real-world value
    #   * fractionlength - number of bits before/after the binary point
    #   * nrbits         - number of bits needed to store the value, is calculated based on maxsi and minsi. Returns 0 when either is not set.
    @property
    def maxfloat(self):
        return self.maxsi * 2**self.shift

    @property
    def minfloat(self):
        return self.minsi * 2**self.shift

    def getsi(self):
        return self._val
    def setsi(self, val):
        self._val = long(val)
    si = property(getsi, setsi)

    def getshift(self):
        return self._shift
    def setshift(self, shift):
        self._shift = long(shift)
    shift = property(getshift, setshift)

    def getfractionlength(self):
        return -self.shift
    fractionlength = property(getfractionlength)

    def getminsi(self):
        return self._min
    def setminsi(self, minsi):
        self._min = long(minsi)
    minsi = property(getminsi, setminsi)

    def getmaxsi(self):
        return self._max
    def setmaxsi(self, maxsi):
        self._max = long(maxsi)
    maxsi = property(getmaxsi, setmaxsi)

    def getnrbits(self):
        if self.minsi is None:
            return 0
        else:
            NrBitsMin = calc_nr_bits(self.minsi)
            NrBitsMax = calc_nr_bits(self.maxsi-1)
            return max(NrBitsMin, NrBitsMax)
    nrbits = property(getnrbits)

    # ------------------------------------------------------------------------------
    #                          GENERIC CLASS-METHODS
    # ------------------------------------------------------------------------------
    def __init__(self, val=0, shift=0, min=None, max=None, rawinit=True):
        # INPUT:
        # OUTPUT:
        assert (min is None and max is None) or (min is not None and max is not None), 'Expected either min AND max equal to None or min and max not equal to None'
        if not rawinit:
            assert False, 'To be implemented'
            # self.shift = -shift
            # self.val = floor(val * 2**(-self.shift) + 0.5)
            # if min is not None:
            #     self.minsi = floor(min * 2**(-self.shift) + 0.5)
            # if max is not None:
            #     assert min < max, 'Exptected min < max, but got min=%.15e and max=%.15e instead' % (min, max)
            #     self.maxsi = floor(max * 2**(-self.shift) + 0.5)
        else:
            self.shift = shift
            self.si = long(val)
            if min is not None:
                self.minsi = min
            if max is not None:
                assert min < max, 'Exptected min < max, but got min=%d and max=%d instead' % (min, max)
                self.maxsi = max

        # if _nrbits:
        #     self.minsi = 0
        #     self.maxsi = 2**_nrbits
        # else:
        #     if isinstance(min, float):
        #         self.minsi = long(floor(min*2**(-shift) + 0.5))
        #     elif isinstance(min, tuple):
        #         # align with shift-value of val, then store min-value
        #
        #         self.minsi = min
        #     # elif
        #
        #     if isinstance(max, float):
        #         self.maxsi = int(floor(max*2**(-shift) + 0.5))
        #     else:
        #         self.maxsi = max
        #     if self.maxsi is not None and self.minsi is not None:
        #         if self.minsi >= 0:
        #             _nrbits = len(bin(self.maxsi-1))
        #         elif self.maxsi <= 1:
        #             _nrbits = len(bin(self.minsi))
        #         else:
        #             # make sure there is a leading zero bit in positive numbers
        #             _nrbits = builtins.max(len(bin(self.maxsi-1))+1, len(bin(self.minsi)))
        # if isinstance(val, float):
        #     self.si = int(floor(val*2**(-shift) + 0.5))
        #     self.shift = shift
        # elif isinstance(val, integer_types):
        #     self.si = val
        #     self.shift = shift
        # elif isinstance(val, string_types):
        #     mval = val.replace('_', '')
        #     self.si = long(mval, 2)
        #     _nrbits = len(mval)
        #     self.shift = shift
        # elif isinstance(val, fixbv):
        #     self.si = val._val*2**(val._shift-shift)
        #     self.minsi = val._min
        #     self.maxsi = val._max
        #     self.shift = val._shift
        #     _nrbits = val._nrbits
        # elif isinstance(val, intbv):
        #     self.si = val._val
        #     self.minsi = val._min
        #     self.maxsi = val._max
        #     self.shift = shift
        #     _nrbits = val._nrbits
        # else:
        #     raise TypeError("fixbv constructor arg should be inbv, int or string")
        # self.nrbits = _nrbits
        self._handleBounds()

    #
    # function : _isfixbv
    # brief    : Check if the 'other' is a fixbv or a signal containing a fixbv, return true is this
    #            is the case
    #
    def _isfixbv(self, other):
        if isinstance(other, fixbv):
            return True
        if hasattr(other, '_val'):
            if isinstance(other._val, fixbv):
                return True
        return False
        
    #
    # function : align
    # brief    : Align the input variable "val" to the fixbv object. This
    #            function supports different input types:
    #            o fixbv
    #            o intbv
    #            o integer
    #            o float
    #
    def align(self, other):
        # This function aligns the fixbv 'self' and 'other', such that they have the same shift factor.
        # The function returns two fixbv-objects.
        if isinstance(other, fixbv):
            a = (self.si, self.shift)
            b = (other.si, other.shift)
            (c, d) = alignvalues(a, b)
            x = fixbv(c[0], c[1])
            y = fixbv(d[0], d[1])
            return (x, y)
        else:
            raise TypeError("fixbv align arg should be fixbv")

    def _handleBounds(self):
        # either _min AND _max are None, or both are not None
        if  self.maxsi is not None and self.minsi is not None:
            if (self.minsi > self.si) or (self.si >= self.maxsi):
                Ssi = fixbvstr_from_tuple(self.si, self.shift)
                Smin = fixbvstr_from_tuple(self.minsi, self.shift)
                Smax = fixbvstr_from_tuple(self.maxsi, self.shift)
                raise ValueError("Value %s out of range [%s, %s>" % (Ssi, Smin, Smax))

    # def _hasFullRange(self):
    #     min, max = self.minsi, self.maxsi
    #     if max <= 0:
    #         return False
    #     if min not in (0, -max):
    #         return False
    #     return max & max-1 == 0

    # hash
    def __hash__(self):
        raise TypeError("fixbv objects are unhashable")
        
    # copy methods
    def __copy__(self):
        c = type(self)(self.si, self.shift, self.minsi, self.maxsi)
        return c

    __deepcopy__ = __copy__

    # logical testing
    def __bool__(self):
        return bool(self.si)

    __nonzero__ = __bool__

    # length
    def __len__(self):
        return self.nrbits

    def is_integer(self):
        #FIXME: this implementation has precision issues; a = fixbv(2**99+1, -31); a.is_integer() returns True, but should be False
        # Idea to fix it:
        #  if shift>=0:
        #     return True
        #  else:
        #     binstr = bin(self.si)
        #     k = number of LSB's equal to 0
        #     if k > self.shift     # or >= ??
        #        return True
        #     else:
        #        return False
        return float(self).is_integer()
    #------------------------------------------------------------------------------
    #                          INDEXING AND SLICING METHODS
    #------------------------------------------------------------------------------
    def __iter__(self):
        if not self.nrbits:
            raise TypeError("Cannot iterate over unsized fixbv")
        return iter([self[i+self.shift] for i in range(self.nrbits-1, -1, -1)])

    def __getitem__(self, key):
        if isinstance(key, slice):
            i, j = key.start-self.shift, key.stop-self.shift
            if j is None: # default
                j = self.shift
            j = int(j)
            if j < 0:
                raise ValueError("fixbv[i:j] requires j >= {}\n" \
                      "            j == {}".format(self.shift, j))
            if i is None: # default
                return intbv(self.si >> j)
            i = int(i)
            if i <= j:
                raise ValueError("fixbv[i:j] requires i > j\n" \
                      "            i, j == {}, {}".format(i, j))
            res = intbv((self.si & (long(1) << i)-1) >> j, _nrbits=i-j)
            return res
        else:
            i = int(key-self.shift)
            res = bool((self.si >> i) & 0x1)
            return res

    def __setitem__(self, key, val):
        # convert val to int to avoid confusion with intbv or Signals
        val = int(val)
        if isinstance(key, slice):
            i, j = key.start, key.stop
            if j is None: # default
                j = 0
            j = int(j)
            if j < 0:
                raise ValueError("intbv[i:j] = v requires j >= 0\n" \
                      "            j == %s" % j)
            if i is None: # default
                q = self.si % (long(1) << j)
                self.si = val * (long(1) << j) + q
                self._handleBounds()
                return
            i = int(i)
            if i <= j:
                raise ValueError("intbv[i:j] = v requires i > j\n" \
                      "            i, j, v == %s, %s, %s" % (i, j, val))
            lim = (long(1) << (i-j))
            if val >= lim or val < -lim:
                raise ValueError("intbv[i:j] = v abs(v) too large\n" \
                      "            i, j, v == %s, %s, %s" % (i, j, val))
            mask = (lim-1) << j
            self.si &= ~mask
            self.si |= (val << j)
            self._handleBounds()
        else:
            i = int(key)
            if val == 1:
                self.si |= (long(1) << i)
            elif val == 0:
                self.si &= ~(long(1) << i)
            else:
                raise ValueError("intbv[i] = v requires v in (0, 1)\n" \
                      "            i == %s " % i)
               
            self._handleBounds()

    def __index__(self):
        return int(self)

    #------------------------------------------------------------------------------
    #                          ARITHMETIC OPERATIONS
    #------------------------------------------------------------------------------
    def __add__(self, other):
        if self._isfixbv(other):
            (c, d) = self.align(other)
            return fixbv(c.si + d.si, c.shift)
        else:
            x = fixbv(other)
            return self + x

    __radd__=__add__
    
    def __sub__(self, other):
        if self._isfixbv(other):
            (c, d) = self.align(other)
            return fixbv(c.si - d.si, c.shift)
        else:
            x = fixbv(other)
            return self - x

    def __rsub__(self, other):
        # other will never be a fixbv, therefore cast it to s fixbv and subtract again.
        x = fixbv(other)
        return x - self

    def __mul__(self, other):
        if self._isfixbv(other):
            return fixbv(self.si * other.si, self.shift + other.shift)
        else:
            x = fixbv(other)
            return self * x

    __rmul__=__mul__
    
    def __truediv__(self, other):
        # # The result is either stored in an integer or in a floating point data-type.
        # # To achieve highest accuracy, the integer parts are treated separately from the shift-factors.
        # if self._isfixbv(other):
        #     return (self.si / other.si) * 2**(self.shift - other.shift)
        # else:
        #     x = fixbv(other)
        #     return self / x

        # The result might be very inprecise, depending on the values of a and b. Therefore it is chosen not to support
        # this function for now.
        raise NotImplementedError('The truediv function is not implemented yet')

    def __rtruediv__(self, other):
        x = fixbv(other)
        return x / self

    def __floordiv__(self, other):
        if self._isfixbv(other):
            (c, d) = self.align(other)
            return fixbv(c.si // d.si, 0)
        else:
            x = fixbv(other)
            return self // x

    def __rfloordiv__(self, other):
        if isinstance(other, intbv):
            return int(float(other._val) // float(self.si*2**self.shift))
        else:
            return int(float(other) // float(self.si*2**self.shift))
        
    def __mod__(self, other):
        if self._isfixbv(other):
            (c,d) = self.align(other)
            return fixbv(c.si % d.si, c.shift)
        else:
            x = fixbv(other)
            return self % x

    def __rmod__(self, other):
        x = fixbv(other)
        return x % self

    def __pow__(self, other):
        # other must be an integer value
        if isinstance(other, float):
            if not other.is_integer():
                raise TypeError('Second argument must be an integer value')
        elif self._isfixbv(other):
            if not other.is_integer():
                raise TypeError('Second argument must be an integer value')
        elif not isinstance(other, intbv) and not isinstance(other, integer_types):
            raise TypeError('Second argument must be an integer value')
        powerval = int(other)
        return fixbv(self.si**powerval, self.shift * powerval)

    def __rpow__(self, other):
        raise NotImplementedError('the rpow-function is not yet implemented')

    def __iadd__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__add__(other)
        result._handleBounds()
        return result

    def __isub__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__sub__(other)
        result._handleBounds()
        return result

    def __imul__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__mul__(other)
        result._handleBounds()
        return result

    def __ifloordiv__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__floordiv__(other)
        result._handleBounds()
        return result

    def __idiv__(self, other):
        raise TypeError("fixbv: Augmented classic division not supported")

    def __itruediv__(self, other):
        raise TypeError("fixbv: Augmented true division not supported")

    def __imod__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__mod__(other)
        result._handleBounds()
        return result

    def __ipow__(self, other, modulo=None):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        # XXX why 3rd param required?
        # unused but needed in 2.2, not in 2.3
        result = self.__pow__(other)
        result._handleBounds()
        return result

    def __neg__(self):
        return fixbv(-self.si, self.shift)

    def __pos__(self):
        return fixbv(self.si, self.shift)

    def __abs__(self):
        return fixbv(abs(self.si), self.shift)

    #------------------------------------------------------------------------------
    #                          BITWISE OPERATIONS
    #------------------------------------------------------------------------------
    def __and__(self, other):
        raise TypeError("unsupported operand type(s) for &: 'fixbv' and '%s'" % type(other))

    def __rand__ (self, other):
        raise TypeError("unsupported operand type(s) for &: 'fixbv' and '%s'" % type(other))

    def __or__(self, other):
        raise TypeError("unsupported operand type(s) for |: 'fixbv' and '%s'" % type(other))

    def __ror__(self, other):
        raise TypeError("unsupported operand type(s) for |: '%s' and 'fixbv'" % type(other))

    def __xor__(self, other):
        raise TypeError("unsupported operand type(s) for ^: 'fixbv' and '%s'" % type(other))

    def __rxor__(self, other):
        raise TypeError("unsupported operand type(s) for ^: '%s' and 'fixbv'" % type(other))

    def __lshift__(self, other):
        if self._isfixbv(other):
            if other.is_integer():
                return fixbv(self.si, self.shift + long(other))
            else:
                raise TypeError("Cannot shift value by an none-integer value")
        else:
            x = fixbv(other)
            return self << x

    def __rlshift__(self, other):
        x = fixbv(other)
        return x << self

    def __rshift__(self, other):
        if self._isfixbv(other):
            if other.is_integer():
                return fixbv(self.si, self.shift - long(other))
            else:
                raise TypeError("Cannot shift value by an none-integer value")
        else:
            x = fixbv(other)
            return self >> x

    def __rrshift__(self, other):
        x = fixbv(other)
        return x >> self

    def __iand__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__and__(other)
        result._handleBounds()
        return result

    def __ior__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__or__(other)
        result._handleBounds()
        return result

    def __ixor__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__xor__(other)
        result._handleBounds()
        return result

    def __ilshift__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__lshift__(other)
        result._handleBounds()
        return result

    def __irshift__(self, other):
        # FIXME: change implementation, because result should be stored in self (not in 'result')
        result = self.__rshift__(other)
        result._handleBounds()
        return result

    def __invert__(self):
        if self.nrbits and self.minsi >= 0:
            return type(self)(~self.si & (long(1) << self.nrbits)-1)
        else:
            return type(self)(~self.si)

    # ------------------------------------------------------------------------------
    #                          COMPARISONS
    # ------------------------------------------------------------------------------
    def __eq__(self, other):
        # Only fixbv's can be compared in full-precision.
        # Other types are converted to fixbv first.
        if self._isfixbv(other):
            (c, d) = self.align(other)
            return (c.si == d.si) # and (c.shift == d.shift)
        else:
            other_fixbv = fixbv(other)  # convert to fixbv
            return self == other_fixbv

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if self._isfixbv(other):
            (c, d) = self.align(other)
            return c.si < d.si
        else:
            other_fixbv = fixbv(other)
            return self < other_fixbv

    def __le__(self, other):
        if self._isfixbv(other):
            (c, d) = self.align(other)
            return c.si <= d.si
        else:
            other_fixbv = fixbv(other)
            return self <= other_fixbv

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    #------------------------------------------------------------------------------
    #                          REPRESENTATION
    #------------------------------------------------------------------------------
    def __float__(self):
        return float(self.si*2**self.shift)

    def __int__(self):
        return int(self.si*2**self.shift)
    
    def __long__(self):
        return long(self.si*2**self.shift)

    def __oct__(self):
        return oct(int(self))

    def __hex__(self):
        return hex(int(self))

    def __str__(self):
        S = fixbvstr_from_tuple(self.si, self.shift)
        return S
    
    def __repr__(self):
        if self.minsi is None:
            return "fixbv({})".format(str(self))
        else:
            return "fixbv({}, min={}, max={}, nrbits={})".format(str(self),
                                                                        fixbvstr_from_tuple(self.minsi, self.shift),
                                                                        fixbvstr_from_tuple(self.maxsi, self.shift),
                                                                        repr(self.nrbits))

    # ------------------------------------------------------------------------------
    #                          OTHER
    # ------------------------------------------------------------------------------
    def signed(self):
      ''' return integer with the signed value of the intbv instance

      The intbv.signed() function will classify the value of the intbv
      instance either as signed or unsigned. If the value is classified
      as signed it will be returned unchanged as integer value. If the
      value is considered unsigned, the bits as specified by _nrbits
      will be considered as 2's complement number and returned. This
      feature will allow to create slices and have the sliced bits be
      considered a 2's complement number.

      The classification is based on the following possible combinations
      of the min and max value.
          
        ----+----+----+----+----+----+----+----
           -3   -2   -1    0    1    2    3
      1                   min  max
      2                        min  max
      3              min       max
      4              min            max
      5         min            max
      6         min       max
      7         min  max
      8   neither min nor max is set
      9   only max is set
      10  only min is set

      From the above cases, # 1 and 2 are considered unsigned and the
      signed() function will convert the value to a signed number.
      Decision about the sign will be done based on the msb. The msb is
      based on the _nrbits value.
      
      So the test will be if min >= 0 and _nrbits > 0. Then the instance
      is considered unsigned and the value is returned as 2's complement
      number.
      '''

      # value is considered unsigned
      if self.min is not None and self.min >= 0 and self.nrbits > 0:

        # get 2's complement value of bits
        msb = self.nrbits-1

        sign = ((self.si >> msb) & 0x1) > 0
        
        # mask off the bits msb-1:lsb, they are always positive
        mask = (1<<msb) - 1
        retVal = self.si & mask
        # if sign bit is set, subtract the value of the sign bit
        if sign:
          retVal -= 1<<msb

      else: # value is returned just as is
        retVal = self.si

      return retVal

#-- end of class '_fixbv.py' ------------------------------------------------------------------------

if __name__ == "__main__":
    # import random
    # for k in xrange(10):
    #     val = random.randint(-2**31, 2**31)
    #     N = random.randint(-31, 31)
    #     a = fixbv(val, N)
    #     print '%s / %s = %.15f' % (a, a, a/a)
    #     assert (a / a == 1)

    a = fixbv(11, -3)
    b = fixbv(1, -2)

    (c, d) = a.align(b)

    print c
    print d

    # c = a % b
    # print c
    # print float(a)
    # print float(b)
    # print float(a) % float(b)
