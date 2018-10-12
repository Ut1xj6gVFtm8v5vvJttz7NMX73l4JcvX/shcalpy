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


"""
Adapted from:

https://www.scipy.org/Cookbook/Least_Squares_Circle
https://scipy-cookbook.readthedocs.io/items/Least_Squares_Circle.html
"""

from CenterPointCalculationResult import CenterPointCalculationResult
from numpy import array
from numpy import linalg
from numpy import mean
from numpy import r_
from numpy import sqrt
import sys


def circlefit_algebraic(point_list):
    """
    Calculate center of point_list using algebraic method

    :param point_list:  list of points on circle edge

    https://dtcenter.org/met/users/docs/write_ups/circle_fit.pdf

    :return:    instance of CenterPointCalculationResult
    """
    assert isinstance(point_list, list) and 3 <= len(point_list)
    assert all([isinstance(v, tuple) and 2 == len(v) for v in point_list])
    assert all([isinstance(v[0], float) and isinstance(v[1], float) for v in point_list])

    cpc_result = CenterPointCalculationResult(count=len(point_list), method_str="algebraic")

    X_values = [v[0] for v in point_list]
    Y_values = [v[1] for v in point_list]

    x = r_[X_values]
    y = r_[Y_values]

    # coordinates of the barycenter
    x_m = mean(x)
    y_m = mean(y)

    # calculation of the reduced coordinates
    u = x - x_m
    v = y - y_m

    # linear system defining the center in reduced coordinates (uc, vc):
    #    sum_uu * uc +  sum_uv * vc = (sum_uuu + sum_uvv)/2
    #    sum_uv * uc +  sum_vv * vc = (sum_uuv + sum_vvv)/2
    sum_uv = sum(u * v)
    sum_uu = sum(u ** 2)
    sum_vv = sum(v ** 2)
    sum_uuv = sum(u ** 2 * v)
    sum_uvv = sum(u * v ** 2)
    sum_uuu = sum(u ** 3)
    sum_vvv = sum(v ** 3)

    # Solving the linear system
    A = array([[sum_uu, sum_uv], [sum_uv, sum_vv]])
    B = array([sum_uuu + sum_uvv, sum_vvv + sum_uuv]) / 2.0
    uc, vc = linalg.solve(A, B)

    cpc_result.center_x = x_m + uc
    cpc_result.center_y = y_m + vc

    # Calculation of all distances from the center (cpc_result.center_x, cpc_result.center_y)
    point_list_center_distance_list = sqrt((x - cpc_result.center_x) ** 2 + (y - cpc_result.center_y) ** 2)
    cpc_result.mean_radius = mean(point_list_center_distance_list)
    cpc_result.residuals_sum = sum((point_list_center_distance_list - cpc_result.mean_radius) ** 2)
    cpc_result.squared_residuals_sum = sum((point_list_center_distance_list ** 2 - cpc_result.mean_radius ** 2) ** 2)

    return cpc_result


if "__main__" == __name__:

    def get_input_data(hole_data_list):
        """
        Returns a list of (x, y) tuples, corresponding to the values in hole_data_list

        :param hole_data_list:  list of floating point string pairs, in CSV format
                                this list may have an optional Z value, which is ignored on output

        :return:    list of (x, y) points
        """
        assert isinstance(hole_data_list, list) and 3 <= len(hole_data_list)
        assert all([isinstance(line_str, str) for line_str in hole_data_list])
        assert all([2 <= len(line_str.split(",")) for line_str in hole_data_list])

        point_list = []

        for i, line_str in enumerate(hole_data_list):
            str_list = line_str.split(",")
            x_str = str_list[0]
            y_str = str_list[1]
            x = float(x_str)
            y = float(y_str)
            p = (x, y)

            point_list.append(p)

        return point_list

    if len(sys.argv) <= 1:
        print "Usage python circlefit_algebraic.py <holedata_filename>"
        print "where holedata_filename is a .csv file of measured X, Y pairs on circumference of a circle."
        exit(1)

    filename_str = sys.argv[1]
    file_hole_data = open(filename_str, "r")
    hole_data_list = [line_str.strip() for line_str in file_hole_data.readlines()]
    file_hole_data.close()

    point_list = get_input_data(hole_data_list)

    cpc_rslt = circlefit_algebraic(point_list)

    format_str = "{0}: {1}: Center({2:4.4f}, {3:4.4f}), MeanRadius({4:4.4f}), ResidualsSum({5:4.4f}), SquaredResidualsSum({6:4.4f}), Count({7})"
    print format_str.format(filename_str, cpc_rslt.method_str, cpc_rslt.center_x, cpc_rslt.center_y, cpc_rslt.mean_radius,
                            cpc_rslt.residuals_sum, cpc_rslt.squared_residuals_sum, cpc_rslt.count)

