#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
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

""" Run the fixbv unit tests. """
from __future__ import absolute_import
from __future__ import division

import operator
import random
import sys
from copy import copy, deepcopy
from random import randrange
from math import floor, ceil, log

import pytest

from myhdl._compat import integer_types, long
from myhdl import intbv

import sys
sys.path.append('D:\Projects\myhdl-imec\myhdl')
from _fixbv import fixbv

random.seed(2)  # random, but deterministic
maxint = sys.maxsize

# TODO:
# * test getitem, setitem
# * Test or, ror, invert, and other bitwise operations
# * test oct, bin, hex functions

def generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=31, includemin=False, includemax=False):
    val = random.randint(-maxval, maxval - 1)
    if maxshift==0:
        shift =0
    else:
        shift = random.randint(-maxshift, maxshift - 1)
    if includemin:
        if val-1 <= -maxval:
            min = -maxval
        else:
            min = random.randint(-maxval, val - 1)
    else:
        min = None
    if includemax:
        if val+1 >= maxval-1:
            max = maxval-1
        else:
            max = random.randint(val + 1, maxval - 1)
    else:
        max = None
    a = fixbv(val, shift, min, max, rawinit=True)
    # print repr(a)
    return a

class TestFixbvGeneric:
    def testDefaultValue(self):
        a = fixbv()
        assert a == 0         # Same behavior as intbv()

    def testGenerateRandomValidFixbvStoredInteger(self):
        shiftMax = 31
        valMax = 2**99
        for k in xrange(1000):
            # Pick a random value/shift combination
            a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True, includemax=True)
            assert a.minsi <= a.si < a.maxsi
            assert a.minsi >= -valMax
            assert a.maxsi <= valMax
            assert a.shift <= shiftMax

    def testAlignValues_fixbv(self):
        shiftMax = 31
        valMax = 2**99
        for k in xrange(1000):
            # Pick a random value/shift combination
            a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True, includemax=True)
            b = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True, includemax=True)
            (c, d) = a.align(b)
            assert c==a or d==b
            assert c.shift == d.shift

    def testCalcNrBits(self):
        a = fixbv(0, 0, min=-4, max=4, rawinit=True)        #min and max give same number of bits
        assert a.nrbits == 3

        a = fixbv(0, 0, min=-7, max=4, rawinit=True)        #min is dominant
        assert a.nrbits == 4

        a = fixbv(0, 0, min=-1, max=4, rawinit=True)        #max is dominant
        assert a.nrbits == 3
        a = fixbv(0, 0, min=0, max=4, rawinit=True)         #max is dominant
        assert a.nrbits == 3

        # test some other values
        a = fixbv(0, 0, min=0, max=1, rawinit=True)
        assert a.nrbits == 0
        a = fixbv(0, 0, min=0, max=2, rawinit=True)
        assert a.nrbits == 2

        # test values larger than what a IEEE double-precision-floating-point can handle in the mantissa
        a = fixbv(0, 0, min=-2**99, max=1, rawinit=True)
        assert a.nrbits == 100
        a = fixbv(0, 0, min=0, max=2**99, rawinit=True)
        assert a.nrbits == 100

    def testHandleBounds(self):
        shiftMax = 4
        valMax = 15

        # Test handlebound-function when min/max are not None
        a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True,includemax=True)
        # This should work
        a.si = a.maxsi-1
        a._handleBounds()
        # This should not work
        a.si = a.maxsi
        with pytest.raises(ValueError):
            a._handleBounds()
        # This should work
        a.si = a.minsi
        a._handleBounds()
        # This should not work
        a.si = a.minsi-1
        with pytest.raises(ValueError):
            a._handleBounds()

        # Test handlebound-function when min/max both are None
        a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=False, includemax=False)
        a.si = valMax + 100
        a._handleBounds         # No error is expected, because nothing is checked

    @pytest.mark.xfail(reason='Is_integer function only works well for small numbers at this moment')
    def testIsInteger(self):
        a = fixbv(15, -31)
        assert (a.is_integer() == False)
        a = fixbv(15, 0)
        assert (a.is_integer() == True)
        a = fixbv(2**99 + 1, -31)
        assert(a.is_integer() == False)

    @pytest.mark.xfail(reason='values will be different, due to rounding/underflow/overflow errors')
    def testAlignValues_intbv(self):
        shiftMax = 31
        valMax = 2 ** 99
        for k in xrange(10):
            # Pick a random value/shift combination
            a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True, includemax=True)
            b = intbv(random.randint(-valMax, valMax - 1))
            (c, d) = a.align(b)
            assert c == a or d == b

    @pytest.mark.xfail(reason='values will be different, due to rounding/underflow/overflow errors')
    def testAlignValues_int(self):
        shiftMax = 31
        valMax = 2 ** 99
        for k in xrange(10):
            # Pick a random value/shift combination
            a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True,
                                                          includemax=True)
            b = int(random.randint(-valMax, valMax - 1))
            (c, d) = a.align(b)
            assert c == a or d == b

    @pytest.mark.xfail(reason='values will be different, due to rounding/underflow errors')
    def testAlignValues_long(self):
        shiftMax = 31
        valMax = 2 ** 99
        for k in xrange(10):
            # Pick a random value/shift combination
            a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True,
                                                          includemax=True)
            b = long(random.randint(-valMax, valMax - 1))
            (c, d) = a.align(b)
            assert c == a or d == b

    @pytest.mark.xfail(reason='values will be different, due to rounding/underflow/overflow errors')
    def testAlignValues_float(self):
        shiftMax = 31
        valMax = 2 ** 99
        for k in xrange(10):
            # Pick a random value/shift combination
            a = generate_random_valid_fixbv_storedinteger(maxval=valMax, maxshift=shiftMax, includemin=True,
                                                          includemax=True)
            b = float(random.randint(-valMax, valMax - 1))
            (c, d) = a.align(b)
            assert c == a or d == b

class TestFixbvCast:
    def testBool(self):
        a = fixbv(0, 0, min=-4, max=4, rawinit=True)
        assert(bool(a) == bool(0))                      # check same behavior as integer

        a = fixbv(1, 0, min=-7, max=4, rawinit=True)
        assert (bool(a) == bool(1))                     # check same behavior as integer

        a = fixbv(-1, 0, min=-7, max=4, rawinit=True)
        assert (bool(a) == bool(-1))                    # check same behavior as integer

class TestFixbvCompare:
    def testNEq_fixbv(self):
        # Verify == and != implementation
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            assert(a == a)
            assert(not(a!=a))

    def testGTLE_fixbv(self):
        # Verify == and != implementation
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            b = a + 1
            assert(b > a)
            assert(not(b <= a))

    def testLTGE_fixbv(self):
        # Verify == and != implementation
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            b = a - 1
            assert(b < a)
            assert(not(b >= a))

    @pytest.mark.xfail(reason='overflow, underflow and rounding errors will cause mismatch between numbers')
    def testNEq_intbv(self):
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            b = intbv(int(a))

            # check regular order
            assert(a == b)
            assert(not(a!=b))
            # it should also work in reverse order
            assert(b == a)
            assert (not (b != a))

    @pytest.mark.xfail(reason='overflow, underflow and rounding errors will cause mismatch between numbers')
    def testNEq_int(self):
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            b = int(a)            # in this operation there might be rounding errors.

            # check regular order
            assert(a == b)
            assert(not(a!=b))
            # it should also work in reverse order
            assert(b == a)
            assert (not (b != a))

    @pytest.mark.xfail(reason='underflow and rounding errors will cause mismatch between numbers')
    def testNEq_long(self):
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            b = long(a)            # in this operation there might be rounding errors.

            # check regular order
            assert(a == b)
            assert(not(a!=b))
            # it should also work in reverse order
            assert(b == a)
            assert (not (b != a))

    @pytest.mark.xfail(reason='overflow, underflow and rounding errors will cause mismatch between numbers')
    def testNEq_float(self):
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**99, maxshift=31, includemin=True, includemax=True)
            b = float(a)            # in this operation there might be rounding errors and/or overflow/underflow.

            # check regular order
            assert(a == b)
            assert(not(a!=b))
            # it should also work in reverse order
            assert(b == a)
            assert (not (b != a))

class TestFixbvArithmetic:
    def testAdd_fixbv(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**30, maxshift=3, includemin=False, includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2**30, maxshift=3, includemin=False, includemax=False)
            c = a+b
            c_float = float(a) + float(b)
            assert(float(c) == c_float)

    def testAdd_int(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**30, maxshift=3, includemin=False, includemax=False)
            b = random.randint(-2**30, 2**30 - 1)
            c = a+b
            d = b+a #//test radd
            c_float = float(a) + float(b)
            assert(float(c) == c_float)
            assert(c == d)

    def testSub_fixbv(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            c = a - b
            c_float = float(a) - float(b)
            assert (float(c) == c_float)

    def testSub_int(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            b = random.randint(-2 ** 30, 2 ** 30 - 1)
            c = a - b
            d = b - a
            c_float = float(a) - float(b)
            assert (float(c) == c_float)
            assert (c == -d)

    def testMul_fixbv(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 17, maxshift=3, includemin=False,
                                                          includemax=False)
            c = a * b
            c_float = float(a) * float(b)
            assert (float(c) == c_float)

    def testMul_int(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            b = random.randint(-2 ** 20, 2 ** 20 - 1)
            c = a * b
            d = b * a
            c_float = float(a) * float(b)
            assert (float(c) == c_float)
            assert(c == d)

    def testPow(self):
        N = random.randint(-99, 99)
        a = fixbv(15, -31)
        b = fixbv(N, 0)
        aN = fixbv(15**N, -31 * N)
        assert (a**N == aN)
        assert (a**float(N) == aN)
        assert (a**b == aN)
        with pytest.raises(TypeError):
            a**float(N+0.1)
        with pytest.raises(TypeError):
            b**a

        # Test rpow-function
        # TODO: Implement rpow function and its tests
        with pytest.raises(NotImplementedError):
            N ** a

    def testTrueDiv_fixbv(self):
        a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=31, includemin=False,
                                                          includemax=False)
        with pytest.raises(NotImplementedError):
            c = a / a

        with pytest.raises(NotImplementedError):
            c = 1 / a

    def testFloorDiv_fixbv(self):
        #TODO: work in progress
        for k in xrange(100):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=31, includemin=False, includemax=False)
            c = a // a
            assert(c == 1)
        for k in xrange(100):       # Test with shift=0
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=0, includemin=False, includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=0, includemin=False, includemax=False)

            c = a // b
            d = long(a) // long(b)
            assert(long(c) == d)
        for k in xrange(100):       # test 'small', arbitrary numbers, which fit fully in a floating point (also after division).
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 20, maxshift=31, includemin=False, includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 20, maxshift=31, includemin=False, includemax=False)

            c = a // b
            d = float(a) // float(b)
            assert(float(c) == d)

    def testFloorDiv_long(self):
        # TODO: work in progress
        for k in xrange(100):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=31, includemin=False, includemax=False)
            a.shift = abs(a.shift)      # Make sure shift is positive, such that casting to long will result in no rounding errors
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=31, includemin=False, includemax=False)
            b.shift = abs(b.shift)
            b = long(b)

            c = a // b
            d = long(a) // long(b)
            assert (long(c) == d)

            e = b // a      # test rfloordiv
            f = b // long(a)
            assert (long(e) == f)

    def testMod_fixbv(self):
        for k in xrange(10):        # check for fixbv containing just integers
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=0, includemin=False, includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=0, includemin=False, includemax=False)

            c = a % b
            d = long(a) % long(b)
            assert(long(c) == d)
        for k in xrange(1000):        # check for 'small' numbers that fit in a float
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 40, maxshift=10, includemin=False, includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 40, maxshift=10, includemin=False, includemax=False)

            c = a % b
            d = float(a) % float(b)
            assert(float(c) == d)

    def testMod_long(self):
        for k in xrange(10):        # check for fixbv containing just integers
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=0, includemin=False, includemax=False)
            b = long(generate_random_valid_fixbv_storedinteger(maxval=2 ** 99, maxshift=0, includemin=False, includemax=False))

            c = a % b
            d = long(a) % long(b)
            assert(long(c) == d)

            # Test __rmod__
            e = b % a
            f = long(b) % long(a)
            assert (long(e) == f)
        for k in xrange(1000):        # check for 'small' numbers that fit in a float
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 40, maxshift=10, includemin=False, includemax=False)
            b = generate_random_valid_fixbv_storedinteger(maxval=2 ** 40, maxshift=10, includemin=False, includemax=False)
            b.shift = abs(b.shift)
            b = long(b)

            c = a % b
            d = float(a) % float(b)
            assert(float(c) == d)

            # Test __rmod__
            e = b % a
            f = float(b) % float(a)
            assert (float(e) == f)

    @pytest.mark.xfail(reason='Conversion from float is not implemented correctly yet')
    def testMod_long(self):
        # No implementation yet, because it will fail anyway
        assert(False)

    @pytest.mark.xfail(reason='Conversion from float is not implemented correctly yet')
    def testAdd_float(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2**30, maxshift=3, includemin=False, includemax=False)
            b = float(generate_random_valid_fixbv_storedinteger(maxval=2**30, maxshift=3, includemin=False, includemax=False))
            c = a+b
            d = b+a
            c_float = float(a) + b
            assert(float(c) == c_float)
            assert(c == d)

    @pytest.mark.xfail(reason='Conversion from float is not implemented correctly yet')
    def testSub_float(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            b = float(generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                                includemax=False))
            c = a - b
            d = b - a
            c_float = float(a) + b
            assert (float(c) == c_float)
            assert(c == -d)

    @pytest.mark.xfail(reason='Conversion from float is not implemented correctly yet')
    def testMul_float(self):
        # test with 'small' numbers, that will fit within the mantissa of a floating point number
        for k in xrange(1000):
            a = generate_random_valid_fixbv_storedinteger(maxval=2 ** 30, maxshift=3, includemin=False,
                                                          includemax=False)
            b = float(generate_random_valid_fixbv_storedinteger(maxval=2 ** 17, maxshift=3, includemin=False,
                                                          includemax=False))
            c = a * b
            d = b * a
            c_float = float(a) * float(b)
            assert (float(c) == c_float)
            assert (c == d)

    # def testInit_correct(self):
    #     val = []
    #     val.append(fixbv(0.75))
    #     val.append(fixbv(0.75, shift=0.0))
    #     val.append(fixbv(0.75, min=-10.0))
    #     val.append(fixbv(0.75, max=+15.0))
    #     val.append(fixbv(0.75, _nrbits=5.0))
    #     val.append(fixbv(0.75, shift=0))
    #     val.append(fixbv(0.75, min=-10))
    #     val.append(fixbv(0.75, max=+15))
    #     val.append(fixbv(0.75, _nrbits=5))
    #     # check whether they are all the same
    #     for item in val:
    #         assert val[0] == item, 'Item %s is not identical to %s' % (repr(item), repr(val[0]))


#
#     def testInitValueTooLarge(self):
#         with pytest.raises(ValueError):
#             a = fixbv(1.1)
#
#     def testInitValueTooSmall(self):
#         with pytest.raises(ValueError):
#             b = fixbv(-0.75, datatype=('s', 15, 15))
#
#     def testInitValRangeTooLarge(self):
#         # test for valrange outside of datatype range (expect to raise AssertionError)
#         with pytest.raises(AssertionError):
#             b = fixbv(0.75, datatype=('s', 16, 15), valrange=(0.25, 1.25))
#
#     def testInitValRangeNotOnGrid(self):
#         # test for valrange not on fixed-point-grid (expect to raise AssertionError)
#         with pytest.raises(AssertionError):
#             b = fixbv(0.75, datatype=('s', 16, 15), valrange=(0.25, 0.9))
#
#     def testInitDataTypeNotSigned(self):
#         # test for unsigned data-type (expect to raise AssertionError)
#         with pytest.raises(AssertionError):
#             d = fixbv(0.75, datatype=('u', 16, 15), valrange=(0.25, 0.875))
#
#     def testDataTypeString2TupleConversion_correct(self):
#         # test the conversion from string to tuple
#         str = 's16,15'
#         T = fixbv.datatypestr2tuple(str)
#         assert T == ('s', 16, 15)
#         str = 's23.-5'
#         T = fixbv.datatypestr2tuple(str)
#         assert T == ('s', 23, -5)
#         str = 'S23.-5'
#         T = fixbv.datatypestr2tuple(str)
#         assert T == ('s', 23, -5)
#
#     def testDataTypeString2TupleConversion_faulty(self):
#         # test the conversion from string to tuple
#         with pytest.raises(AssertionError):
#             str = 'u16,15'      # wrong signedness
#             T = fixbv.datatypestr2tuple(str)
#         with pytest.raises(AssertionError):
#             str = 's16_15'      # wrong delimiter
#             T = fixbv.datatypestr2tuple(str)
#
# class TestFixbvRepr:
#     def testReprStr(self):
#         # just check whether these functions work (no errors)
#         # implicitly checks eps-, val-, valrange- and range-function
#         a = fixbv(1.25, datatype='auto')
#         s1 = repr(a)
#         s2 = str(a)
#
# class TestFixbvComparison:
#     def testEqual(self):
#         import numpy as np
#         from _intbv import intbv
#         a = fixbv(0)
#         b = fixbv(0.0)
#
#         c = fixbv(13, datatype='auto')
#         d = intbv(13)
#         e = 13.0
#         f = long(13)    # no separate test for 'int', assume they behave the same
#         g = np.float64(13)     # no separate test for float16, float32, float80, float128, float256, assume they behave the same
#
#         assert a == b
#         assert c == d
#         assert c == e
#         assert c == f
#         assert c == g
#
#         assert d == c
#         assert e == c
#         assert f == c
#         assert g == c
#
#     def testNotEqual(self):
#         import numpy as np
#         from _intbv import intbv
#
#         a = fixbv(13.25, datatype='auto')
#
#         c = fixbv(13, datatype='auto')
#         d = intbv(13)
#         e = 13.0
#         f = long(13)    # no separate test for 'int', assume they behave the same
#         g = np.float64(13)     # no separate test for float16, float32, float80, float128, float256, assume they behave the same
#
#         assert a != c
#         assert a != d
#         assert a != e
#         assert a != f
#         assert a != g
#
#         assert c != a
#         assert d != a
#         assert e != a
#         assert f != a
#         assert g != a
#
#     def testLessThan(self):
#         import numpy as np
#         from _intbv import intbv
#
#         a = fixbv(13 - 2**-49, datatype='auto')
#
#         c = fixbv(13, datatype='auto')
#         d = intbv(13)
#         e = 13.0
#         f = long(13)    # no separate test for 'int', assume they behave the same
#         g = np.float64(13)     # no separate test for float16, float32, float80, float128, float256, assume they behave the same
#
#         assert a < c
#         assert a < d
#         assert a < e
#         assert a < f
#         assert a < g
#
#     def testLessThanEqual(self):
#         import numpy as np
#         from _intbv import intbv
#
#         a = fixbv(13 - 2 ** -49, datatype='auto')
#
#         c = fixbv(13, datatype='auto')
#         d = intbv(13)
#         e = 13.0
#         f = long(13)  # no separate test for 'int', assume they behave the same
#         g = np.float64(13)  # no separate test for float16, float32, float80, float128, float256, assume they behave the same
#
#         h = np.float64(13 - 2**-49)
#
#         assert a <= c
#         assert a <= d
#         assert a <= e
#         assert a <= f
#         assert a <= g
#         assert a <= h
#
#         assert a <= a
#         # FIXME: statement below does not work yet
#         assert h <= a
#
#     def testGreaterThan(self):
#         import numpy as np
#         from _intbv import intbv
#
#         a = fixbv(13 + 2**-49, datatype='auto')
#
#         c = fixbv(13, datatype='auto')
#         d = intbv(13)
#         e = 13.0
#         f = long(13)    # no separate test for 'int', assume they behave the same
#         g = np.float64(13)     # no separate test for float16, float32, float80, float128, float256, assume they behave the same
#
#         assert a > c
#         assert a > d
#         assert a > e
#         assert a > f
#         assert a > g
#
#     def testGreaterThanEqual(self):
#         import numpy as np
#         from _intbv import intbv
#
#         a = fixbv(13 + 2 ** -49, datatype='auto')
#
#         c = fixbv(13, datatype='auto')
#         d = intbv(13)
#         e = 13.0
#         f = long(13)  # no separate test for 'int', assume they behave the same
#         g = np.float64(13)  # no separate test for float16, float32, float80, float128, float256, assume they behave the same
#
#         h = np.float64(13 + 2**-49)
#
#         assert a >= c
#         assert a >= d
#         assert a >= e
#         assert a >= f
#         assert a >= g
#         assert a >= h
#
#         assert a >= a
#         # FIXME: statement below does not work yet
#         assert h >= a
#
# class TestFixbvOperations:
#     def testAlign(self):
#         a = fixbv(3, datatype='s3,0')
#         b = fixbv(4, datatype='s7,3')
#         (c, d) = a.align(b)                  # a.fractionlength < b.fractionlength
#         assert c.val == a.val
#         assert d.val == b.val
#         assert c.fractionlength == d.fractionlength
#         assert c.valrange == a.valrange
#         assert d.valrange == b.valrange
#
#         (c, d) = a.align(a)                  # a.fractionlength == b.fractionlength
#         assert c.val == a.val
#         assert d.val == a.val
#         assert c.fractionlength == d.fractionlength
#         assert c.valrange == a.valrange
#         assert d.valrange == a.valrange
#
#         a = fixbv(3, datatype='s3,0')
#         b = fixbv(122, datatype='s3,-6')
#         (c, d) = a.align(b)                   # a.fractionlength > b.fractionlength
#         assert c.val == a.val
#         assert d.val == b.val
#         assert c.fractionlength == d.fractionlength
#         assert c.valrange == a.valrange
#         assert d.valrange == b.valrange
#
#     def testAdd(self):
#         # additions should happen in full-precision, the result should have the same fractionlength and a wordlength matching the valrange.
#         # additions of the following classes are supported: fixbv, float, np.float, int, long, intbv
#         import numpy as np
#         from _intbv import intbv
#         a = fixbv(3, datatype='auto')
#         b = fixbv(4, datatype='s19,15')
#         ab = a + b
#         assert float(ab) == float(a) + float(b)
#         assert ab.fractionlength == max(a.fractionlength, b.fractionlength)
#         assert ab.valrange[0] == a.valrange[0] + b.valrange[0]
#         assert ab.valrange[1] == a.valrange[1]-a.eps() + b.valrange[1]-b.eps() + ab.eps()
#         # print repr(a)
#         # print repr(b)
#         # print repr(ab)
#
#         a = fixbv(3, datatype='auto', valrange=(-2, 4))
#         b = fixbv(4, datatype='s19,15', valrange=(-6, 7.5))
#         ab = a + b
#         assert float(ab) == float(a) + float(b)
#         assert ab.fractionlength == max(a.fractionlength, b.fractionlength)
#         assert ab.valrange[0] == a.valrange[0] + b.valrange[0]
#         assert ab.valrange[1] == a.valrange[1] - a.eps() + b.valrange[1] - b.eps() + ab.eps()
#         # print repr(a)
#         # print repr(b)
#         # print repr(ab)
#
#         a = fixbv(-2, datatype='s9,6', valrange=(-2, 4))
#         b = fixbv(-6, datatype='s19,15', valrange=(-6, 7.75))
#         ab = a + b
#         assert float(ab) == float(a) + float(b)
#         assert ab.fractionlength == max(a.fractionlength, b.fractionlength)
#         assert ab.valrange[0] == a.valrange[0] + b.valrange[0]
#         assert ab.valrange[1] == a.valrange[1] - a.eps() + b.valrange[1] - b.eps() + ab.eps()
#         # print repr(a)
#         # print repr(b)
#         # print repr(ab)
#
#         #TODO: do randomized testing; generate randon-fixbv
#         #TODO: test additions of other types: intbv, float, int, long, etc
#
#
    # def testSub(self)

class TestFixbvBitOperations:
    def testAnd_fixbv(self):
        a = fixbv(10,2)
        b = fixbv(12,4)
        with pytest.raises(TypeError):      # test implementation of __and__
            c = a & b
        with pytest.raises(TypeError):      # test implementation of __rand__
            c = 10 & a

    # TODO: add testcases for OR and XOR


    def testLShift(self):
        # test with fixbv as shiftfactor
        a = fixbv(1,-5)
        largeShiftFactor = fixbv(2**99 + 1, 0)          # cannot be represented, without loss of accuracy, by float
        b = a << largeShiftFactor
        assert(b.si == a.si)
        assert(b.shift == a.shift + long(largeShiftFactor))

        # test with long as shiftfactor
        a = fixbv(1,10)
        largeShiftFactor = -2**99 + 1          # cannot be represented, without loss of accuracy, by float
        b = a << largeShiftFactor
        assert(b.si == a.si)
        assert(b.shift == a.shift + largeShiftFactor)

        # test __rlshift__
        a = fixbv(-2**99+1,0)
        largeShiftFactor = fixbv(-2**199 + 1, 0)          # cannot be represented, without loss of accuracy, by float
        b = a << largeShiftFactor
        assert(b.si == a.si)
        assert(b.shift == long(largeShiftFactor))

    def testRShift(self):
        # test with fixbv as shiftfactor
        a = fixbv(1,-5)
        largeShiftFactor = fixbv(2**99 + 1, 0)          # cannot be represented, without loss of accuracy, by float
        b = a >> largeShiftFactor
        assert(b.si == a.si)
        assert(b.shift == a.shift - long(largeShiftFactor))

        # test with long as shiftfactor
        a = fixbv(1,10)
        largeShiftFactor = -2**99 + 1          # cannot be represented, without loss of accuracy, by float
        b = a >> largeShiftFactor
        assert(b.si == a.si)
        assert(b.shift == a.shift - largeShiftFactor)

        # test __rlshift__
        a = fixbv(-2**99+1,0)
        largeShiftFactor = fixbv(-2**199 + 1, 0)          # cannot be represented, without loss of accuracy, by float
        b = a >> largeShiftFactor
        assert(b.si == a.si)
        assert(b.shift == -long(largeShiftFactor))

# def getItem(s, i):
#     ext = '0' * (i-len(s)+1)
#     exts = ext + s
#     si = len(exts)-1-i
#     return exts[si]
#
#
# def getSlice(s, i, j):
#     ext = '0' * (i-len(s)+1)
#     exts = ext + s
#     si = len(exts)-i
#     sj = len(exts)-j
#     return exts[si:sj]
#
#
# def getSliceLeftOpen(s, j):
#     ext = '0' * (j-len(s)+1)
#     exts = ext + s
#     if j:
#         return exts[:-j]
#     else:
#         return exts
#
#
# def setItem(s, i, val):
#     ext = '0' * (i-len(s)+1)
#     exts = ext + s
#     si = len(exts)-1-i
#     return exts[:si] + val + exts[si+1:]
#
#
# def setSlice(s, i, j, val):
#     ext = '0' * (i-len(s)+1)
#     exts = ext + s
#     si = len(exts)-i
#     sj = len(exts)-j
#     return exts[:si] + val[si-sj:] + exts[sj:]
#
#
# def setSliceLeftOpen(s, j, val):
#     ext = '0' * (j-len(s)+1)
#     exts = ext + s
#     if j:
#         return val + exts[-j:]
#     else:
#         return val
#
#
# class TestIntBvIndexing:
#
#     def seqsSetup(self):
#         seqs = ["0", "1", "000", "111", "010001", "110010010", "011010001110010"]
#         seqs.extend(["0101010101", "1010101010", "00000000000", "11111111111111"])
#         seqs.append("11100101001001101000101011011101001101")
#         seqs.append("00101011101001011111010100010100100101010001001")
#         self.seqs = seqs
#         seqv = ["0", "1", "10", "101", "1111", "1010"]
#         seqv.extend(["11001", "00111010", "100111100"])
#         seqv.append("0110101001111010101110011010011")
#         seqv.append("1101101010101101010101011001101101001100110011")
#         self.seqv = seqv
#
#     def testGetItem(self):
#         self.seqsSetup()
#         for s in self.seqs:
#             n = long(s, 2)
#             bv = intbv(n)
#             bvi = intbv(~n)
#             for i in range(len(s)+20):
#                 ref = long(getItem(s, i), 2)
#                 res = bv[i]
#                 resi = bvi[i]
#                 assert res == ref
#                 assert type(res) == bool
#                 assert resi == ref^1
#                 assert type(resi) == bool
#
#     def testGetSlice(self):
#         self.seqsSetup()
#         for s in self.seqs:
#             n = long(s, 2)
#             bv = intbv(n)
#             bvi = intbv(~n)
#             for i in range(1, len(s)+20):
#                 for j in range(0,len(s)+20):
#                     try:
#                         res = bv[i:j]
#                         resi = bvi[i:j]
#                     except ValueError:
#                         assert i<=j
#                         continue
#                     ref = long(getSlice(s, i, j), 2)
#                     assert res == ref
#                     assert type(res) == intbv
#                     mask = (2**(i-j))-1
#                     assert resi == ref ^ mask
#                     assert type(resi) == intbv
#
#     def testGetSliceLeftOpen(self):
#         self.seqsSetup()
#         for s in self.seqs:
#             n = long(s, 2)
#             bv = intbv(n)
#             bvi = intbv(~n)
#             for j in range(0,len(s)+20):
#                 res = bv[:j]
#                 resi = bvi[:j]
#                 ref = long(getSliceLeftOpen(s, j), 2)
#                 assert res == ref
#                 assert type(res) == intbv
#                 assert resi+ref == -1
#                 assert type(res) == intbv
#
#     def testSetItem(self):
#         self.seqsSetup()
#         for s in self.seqs:
#             n = long(s, 2)
#             for it in (int, intbv):
#                 for i in range(len(s)+20):
#                     # print i
#                     bv0 = intbv(n)
#                     bv1 = intbv(n)
#                     bv0i = intbv(~n)
#                     bv1i = intbv(~n)
#                     bv0[i] = it(0)
#                     bv1[i] = it(1)
#                     bv0i[i] = it(0)
#                     bv1i[i] = it(1)
#                     ref0 = long(setItem(s, i, '0'), 2)
#                     ref1 = long(setItem(s, i, '1'), 2)
#                     ref0i = ~long(setItem(s, i, '1'), 2)
#                     ref1i = ~long(setItem(s, i, '0'), 2)
#                     assert bv0 == ref0
#                     assert bv1 == ref1
#                     assert bv0i == ref0i
#                     assert bv1i == ref1i
#
#     def testSetSlice(self):
#         self.seqsSetup()
#         toggle = 0
#         for s in self.seqs:
#             n = long(s, 2)
#             for i in range(1, len(s)+5):
#                 for j in range(0, len(s)+5):
#                     for v in self.seqv:
#                         ext = '0' * (i-j -len(v))
#                         extv = ext + v
#                         bv = intbv(n)
#                         bvi = intbv(~n)
#                         val = long(v, 2)
#                         toggle ^= 1
#                         if toggle:
#                             val = intbv(val)
#                         try:
#                             bv[i:j] = val
#                         except ValueError:
#                             assert i<=j or val >= 2**(i-j)
#                             continue
#                         else:
#                             ref = long(setSlice(s, i, j, extv), 2)
#                             assert bv == ref
#                         mask = (2**(i-j))-1
#                         vali = val ^ mask
#                         try:
#                             bvi[i:j] = vali
#                         except ValueError:
#                             assert vali >= 2**(i-j)
#                             continue
#                         else:
#                             refi = ~long(setSlice(s, i, j, extv), 2)
#                             assert bvi == refi
#
#     def testSetSliceLeftOpen(self):
#         self.seqsSetup()
#         toggle = 0
#         for s in self.seqs:
#             n = long(s, 2)
#             for j in range(0, len(s)+5):
#                 for v in self.seqv:
#                     bv = intbv(n)
#                     bvi = intbv(~n)
#                     val = long(v, 2)
#                     toggle ^= 1
#                     if toggle:
#                         val = intbv(val)
#                     bv[:j] = val
#                     bvi[:j] = -1-val
#                     ref = long(setSliceLeftOpen(s, j, v), 2)
#                     assert bv == ref
#                     refi = ~long(setSliceLeftOpen(s, j, v), 2)
#                     assert bvi == refi
#
#
# class TestIntBvAsInt:
#
#     def seqSetup(self, imin, imax, jmin=0, jmax=None):
#         seqi = [imin, imin,   12, 34]
#         seqj = [jmin, 12  , jmin, 34]
#         if not imax and not jmax:
#             l = 2222222222222222222222222222
#             seqi.append(l)
#             seqj.append(l)
#         # first some smaller ints
#         for n in range(100):
#             ifirstmax = jfirstmax = 100000
#             if imax:
#                 ifirstmax = min(imax, ifirstmax)
#             if jmax:
#                 jfirstmax = min(jmax, jfirstmax)
#             i = randrange(imin, ifirstmax)
#             j = randrange(jmin, jfirstmax)
#             seqi.append(i)
#             seqj.append(j)
#         # then some potentially longs
#         for n in range(100):
#             if not imax:
#                 i = randrange(maxint) + randrange(maxint)
#             else:
#                 i = randrange(imin, imax)
#             if not jmax:
#                 j = randrange(maxint) + randrange(maxint)
#             else:
#                 j = randrange(jmin, jmax)
#             seqi.append(i)
#             seqj.append(j)
#         self.seqi = seqi
#         self.seqj = seqj
#
#     def binaryCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
#         self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
#         for i, j in zip(self.seqi, self.seqj):
#             bi = intbv(long(i))
#             bj = intbv(j)
#             ref = op(long(i), j)
#             r1 = op(bi, j)
#             r2 = op(long(i), bj)
#             r3 = op(bi, bj)
#             #self.assertEqual(type(r1), intbv)
#             #self.assertEqual(type(r2), intbv)
#             #self.assertEqual(type(r3), intbv)
#             assert r1 == ref
#             assert r2 == ref
#             assert r3 == ref
#
#     def augmentedAssignCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
#         self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
#         for i, j in zip(self.seqi, self.seqj):
#             bj = intbv(j)
#             ref = long(i)
#             ref = op(ref, j)
#             r1 = bi1 = intbv(long(i))
#             r1 = op(r1, j)
#             r2 = long(i)
#             r2 = op(r2, bj)
#             r3 = bi3 = intbv(long(i))
#             r3 = op(r3, bj)
#             assert type(r1) == intbv
#             assert type(r3) == intbv
#             assert r1 == ref
#             assert r2 == ref
#             assert r3 == ref
#             assert r1 is bi1
#             assert r3 is bi3
#
#     def unaryCheck(self, op, imin=0, imax=None):
#         self.seqSetup(imin=imin, imax=imax)
#         for i in self.seqi:
#             bi = intbv(i)
#             ref = op(i)
#             r1 = op(bi)
#             #self.assertEqual(type(r1), intbv)
#             assert r1 == ref
#
#     def conversionCheck(self, op, imin=0, imax=None):
#         self.seqSetup(imin=imin, imax=imax)
#         for i in self.seqi:
#             bi = intbv(i)
#             ref = op(i)
#             r1 = op(bi)
#             assert type(r1) == type(ref)
#             assert r1 == ref
#
#     def comparisonCheck(self, op, imin=0, imax=None, jmin=0, jmax=None):
#         self.seqSetup(imin=imin, imax=imax, jmin=jmin, jmax=jmax)
#         for i, j in zip(self.seqi, self.seqj):
#             bi = intbv(i)
#             bj = intbv(j)
#             ref = op(i, j)
#             r1 = op(bi, j)
#             r2 = op(i, bj)
#             r3 = op(bi, bj)
#             assert r1 == ref
#             assert r2 == ref
#             assert r3 == ref
#
#     def testAdd(self):
#         self.binaryCheck(operator.add)
#
#     def testSub(self):
#         self.binaryCheck(operator.sub)
#
#     def testMul(self):
#         self.binaryCheck(operator.mul, imax=maxint)  # XXX doesn't work for long i???
#
#     def testTrueDiv(self):
#         self.binaryCheck(operator.truediv, jmin=1)
#
#     def testFloorDiv(self):
#         self.binaryCheck(operator.floordiv, jmin=1)
#
#     def testMod(self):
#         self.binaryCheck(operator.mod, jmin=1)
#
#     def testPow(self):
#         self.binaryCheck(pow, jmax=64)
#
#     def testLShift(self):
#         self.binaryCheck(operator.lshift, jmax=256)
#
#     def testRShift(self):
#         self.binaryCheck(operator.rshift, jmax=256)
#
#     def testAnd(self):
#         self.binaryCheck(operator.and_)
#
#     def testOr(self):
#         self.binaryCheck(operator.or_)
#
#     def testXor(self):
#         self.binaryCheck(operator.xor)
#
#     def testIAdd(self):
#         self.augmentedAssignCheck(operator.iadd)
#
#     def testISub(self):
#         self.augmentedAssignCheck(operator.isub)
#
#     def testIMul(self):
#         self.augmentedAssignCheck(operator.imul, imax=maxint)  # XXX doesn't work for long i???
#
#     def testIFloorDiv(self):
#         self.augmentedAssignCheck(operator.ifloordiv, jmin=1)
#
#     def testIMod(self):
#         self.augmentedAssignCheck(operator.imod, jmin=1)
#
#     def testIPow(self):
#         self.augmentedAssignCheck(operator.ipow, jmax=64)
#
#     def testIAnd(self):
#         self.augmentedAssignCheck(operator.iand)
#
#     def testIOr(self):
#         self.augmentedAssignCheck(operator.ior)
#
#     def testIXor(self):
#         self.augmentedAssignCheck(operator.ixor)
#
#     def testILShift(self):
#         self.augmentedAssignCheck(operator.ilshift, jmax=256)
#
#     def testIRShift(self):
#         self.augmentedAssignCheck(operator.irshift, jmax=256)
#
#     def testNeg(self):
#         self.unaryCheck(operator.neg)
#
#     def testNeg(self):
#         self.unaryCheck(operator.pos)
#
#     def testAbs(self):
#         self.unaryCheck(operator.abs)
#
#     def testInvert(self):
#         self.unaryCheck(operator.inv)
#
#     def testInt(self):
#         self.conversionCheck(int, imax=maxint)
#
#     def testLong(self):
#         self.conversionCheck(long)
#
#     def testFloat(self):
#         self.conversionCheck(float)
#
#     # XXX __complex__ seems redundant ??? (complex() works as such?)
#
#     def testOct(self):
#         self.conversionCheck(oct)
#
#     def testHex(self):
#         self.conversionCheck(hex)
#
#     def testLt(self):
#         self.comparisonCheck(operator.lt)
#
#     def testLe(self):
#         self.comparisonCheck(operator.le)
#
#     def testGt(self):
#         self.comparisonCheck(operator.gt)
#
#     def testGe(self):
#         self.comparisonCheck(operator.ge)
#
#     def testEq(self):
#         self.comparisonCheck(operator.eq)
#
#     def testNe(self):
#         self.comparisonCheck(operator.ne)
#
#
# class TestIntbvBounds:
#
#     def testConstructor(self):
#         assert intbv(40, max=54) == 40
#         with pytest.raises(ValueError):
#             intbv(40, max=27)
#
#         assert intbv(25, min=16) == 25
#         with pytest.raises(ValueError):
#             intbv(25, min=27)
#
#     def testSliceAssign(self):
#         a = intbv(min=-24, max=34)
#         for i in (-24, -2, 13, 33):
#             for k in (6, 9, 10):
#                 a[:] = 0
#                 a[k:] = i
#                 assert a == i
#         for i in (-25, -128, 34, 35, 229):
#             for k in (0, 9, 10):
#                 with pytest.raises(ValueError):
#                     a[k:] = i
#
#         a = intbv(5)[8:]
#         for v in (0, 2**8-1, 100):
#             a[:] = v
#         for v in (-1, 2**8, -10, 1000):
#             with pytest.raises(ValueError):
#                 a[:] = v
#
#     def checkBounds(self, i, j, op):
#         a = intbv(i)
#         assert a == i  # just to be sure
#         try:
#             exec("a %s long(j)" % op)
#         except (ZeroDivisionError, ValueError):
#             return  # prune
#         if not isinstance(a._val, integer_types):
#             return  # prune
#         if abs(a) > maxint * maxint:
#             return  # keep it reasonable
#         if a > i:
#             b = intbv(i, min=i, max=a+1)
#             for m in (i+1, a):
#                 b = intbv(i, min=i, max=m)
#                 with pytest.raises(ValueError):
#                     exec("b %s long(j)" % op)
#         elif a < i :
#             b = intbv(i, min=a, max=i+1)
#             exec("b %s long(j)" % op)  # should be ok
#             for m in (a+1, i):
#                 b = intbv(i, min=m, max=i+1)
#                 with pytest.raises(ValueError):
#                     exec("b %s long(j)" % op)
#         else:  # a == i
#             b = intbv(i, min=i, max=i+1)
#             exec("b %s long(j)" % op)  # should be ok
#
#     def checkOp(self, op):
#         for i in (0, 1, -1, 2, -2, 16, -24, 129, -234, 1025, -15660):
#             for j in (0, 1, -1, 2, -2, 9, -15, 123, -312, 2340, -23144):
#                 self.checkBounds(i, j, op)
#
#     def testIAdd(self):
#         self.checkOp("+=")
#
#     def testISub(self):
#         self.checkOp("-=")
#
#     def testIMul(self):
#         self.checkOp("*=")
#
#     def testIFloorDiv(self):
#         self.checkOp("//=")
#
#     def testIMod(self):
#         self.checkOp("%=")
#
#     def testIPow(self):
#         self.checkOp("**=")
#
#     def testIAnd(self):
#         self.checkOp("&=")
#
#     def testIOr(self):
#         self.checkOp("|=")
#
#     def testIXor(self):
#         self.checkOp("^=")
#
#     def testILShift(self):
#         self.checkOp("<<=")
#
#     def testIRShift(self):
#         self.checkOp(">>=")
#
#
# class TestIntbvCopy:
#
#     def testCopy(self):
#
#         for n in (intbv(), intbv(34), intbv(-12, min=-15), intbv(45, max=65),
#                   intbv(23, min=2, max=47), intbv(35)[3:]):
#             a = intbv(n)
#             b = copy(n)
#             c = deepcopy(n)
#             for m in (a, b, c):
#                 assert n == m
#                 assert n._val == m._val
#                 assert n.min == m.min
#                 assert n.max == m.max
#                 assert len(n) == len(m)


