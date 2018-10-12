#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Copyright 2018 Bryan Webb

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
    associated documentation files (the "Software"), to deal in the Software without restriction,
    including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all copies
        or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
        INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
        AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
        DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


class CenterPointCalculationResult():
    def __init__(self, count=0, method_str="algebraic"):
        assert isinstance(method_str, str)
        self.__method_str = method_str
        self.__count = count
        self.__center_x = 0.0
        self.__center_y = 0.0
        self.__mean_radius = 0.0
        self.__residuals_sum = 0.0
        self.__squared_residuals_sum = 0.0

    @property
    def method_str(self):
        return self.__method_str

    @property
    def count(self):
        return self.__count

    @count.setter               # number of points
    def count(self, count):
        self.__count = count

    @property
    def center_x(self):
        return self.__center_x

    @center_x.setter
    def center_x(self, x):
        self.__center_x = x

    @property
    def center_y(self):
        return self.__center_y

    @center_y.setter
    def center_y(self, y):
        self.__center_y = y

    @property
    def mean_radius(self):
        return self.__mean_radius

    @mean_radius.setter
    def mean_radius(self, mean_radius):
        self.__mean_radius = mean_radius

    @property
    def residuals_sum(self):    # corresponds to N * Variance
        return self.__residuals_sum

    @residuals_sum.setter
    def residuals_sum(self, residual_sum):
        self.__residuals_sum = residual_sum

    @property
    def squared_residuals_sum(self):
        return self.__squared_residuals_sum

    @squared_residuals_sum.setter
    def squared_residuals_sum(self, squared_residuals_sum):
        self.__squared_residuals_sum = squared_residuals_sum

