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


# https://glowingpython.blogspot.com/2012/03/linear-regression-with-numpy.html


import numpy as np


def linear_least_squares_fit_xy_lists(x_list, y_list):
    """
    Calculate the least squares fit of corresponding lists of X and Y values
    as in:

        y = mx + b

    :param x_list: list of x values
    :param y_list: list of y values to be LS Fit to the list of x values

    :return:    (slope, y-intercept) list
    """
    assert isinstance(x_list, list) and 2 <= len(x_list)
    assert isinstance(y_list, list) and 2 <= len(y_list)
    assert len(x_list) == len(y_list)
    assert all([isinstance(v, float) for v in x_list])
    assert all([isinstance(v, float) for v in y_list])

    try:
        x_matrix = np.array([x_list, np.ones(len(x_list))])
        mb_list = np.linalg.lstsq(x_matrix.T, y_list)[0]
    except:
        mb_list = [None for i in range(len(x_list))]

    return mb_list


def linear_least_squares_fit_tup_list(v_list):
    """
    Calculate the least squares fit of a list of (X, Y) tuples, as in:

        y = mx + b

    :param v_list:  a list of (x, y) tuples, where x and y are floats

    :return:    (slope, y-intercept) tuple
    """
    assert isinstance(v_list, list) and 2 <=len(v_list)
    assert all([isinstance(v, (list, tuple)) and 2 == len(v) for v in v_list])

    x_list = [v[0] for v in v_list]
    y_list = [v[1] for v in v_list]

    assert all([isinstance(v, float) for v in x_list])
    assert all([isinstance(v, float) for v in y_list])

    mb_list = linear_least_squares_fit_xy_lists(x_list, y_list)

    return mb_list


if "__main__" == __name__:
    # Nominal test case
    x_list = []
    y_list = []
    tup_list = []

    for i in range(10):
        x = float(i)
        for j in range(i):
            y = float(j)
            x_list.append(x)
            y_list.append(y)
            tup = (x, y)
            tup_list.append(tup)

    print linear_least_squares_fit_xy_lists(x_list, y_list)
    print linear_least_squares_fit_tup_list(tup_list)

    # Reasonable result
    tup_list = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]
    x_list = [v[0] for v in tup_list]
    y_list = [v[1] for v in tup_list]

    print linear_least_squares_fit_xy_lists(x_list, y_list)
    print linear_least_squares_fit_tup_list(tup_list)

    # This test case should have yielded infinite slope m
    # If the data is set so that it always yields an ~ 45deg angle, this slope of 0.0 will never happen
    x_list = []
    y_list = []
    tup_list = []

    for i in range(10):
        x = 0.0
        y = float(i)
        x_list.append(x)
        y_list.append(y)
        tup = (x, y)
        tup_list.append(tup)

    print linear_least_squares_fit_xy_lists(x_list, y_list)
    print linear_least_squares_fit_tup_list(tup_list)
