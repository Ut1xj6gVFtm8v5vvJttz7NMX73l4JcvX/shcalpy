import math
import numpy as np
import sys


EPSILON = 0.0001

LFTMOST_X = -420.0
RGTMOST_X = 0.0
BACKMOST_Y = 0.0
FRNTMOST_Y = -370.0

RGTMOST_MOUNT_OFFSET_X = 112.0
LFTMOST_MOUNT_OFFSET_X = -109.0
BACKMOST_MOUNT_OFFSET_Y = 194.5
FRNTMOST_MOUNT_OFFSET_Y = 5.0

def get_z(coeffs, x, y):
    """
    Calculate and return the height z given the coefficients and ordinates of ax + by + c = z

    :param coeffs:  numpy ndarray of coefficients a, b, c, in the order (c, a, b)
    :param x:       x value
    :param y:       y vakye

    :return:    the calculated z value
    """
    assert isinstance(coeffs, tuple) and 3 == len(coeffs)
    assert all([isinstance(v, float) for v in coeffs])
    assert isinstance(x, float)
    assert isinstance(y, float)

    a, b, c = coeffs
    z = a*x + b*y + c
    # print z

    return z


def get_z_by_name(name_str):
    """
    Get z adjust value for mount hole (x, y) tuple matching name_str

    :param name_str:    str matching one of table_mount_point_list's 2nd arg

    Note: table_mount_point_list should already be defined by the time
            this function is called.

    :return:    z
    """
    assert isinstance(name_str, str)
    match_list = [v[0] for v in table_mount_point_list if v[1] == name_str]
    assert 1 == len(match_list)
    x, y = match_list[0]
    z = abs(get_z(coeffs, x, y))
    return z


def get_inputs(depthdata_str_list):
    """
    Given a list of strings composed of 3 floating pt nbrs x, y, z separated by commas,
    convert them to floats and return them as 3 individual lists.

    :param depthdata_str_list: list of floating point string pairs, separated by a comma (think .csv file)

    :return:    lists of x values, y values, and corresponding z values
    """
    assert isinstance(depthdata_str_list, list)
    assert all([isinstance(s, str) for s in depthdata_str_list])
    assert all([3 == len(v.split(",")) for v in depthdata_str_list])

    x_list = []
    y_list = []
    z_list = []

    for i, line_str in enumerate(depthdata_str_list):
        str_list = line_str.split(",")
        x_str, y_str, z_str = str_list
        x = float(x_str)
        y = float(y_str)
        z = float(z_str)
        x_list.append(x)
        y_list.append(y)
        z_list.append(z)

    return x_list, y_list, z_list


def read_data_file(filename_str):
    """
    Read the given file, and return a stripped list of its records

    :param filename_str:    file name

    :return:    list of stripped records
    """
    assert isinstance(filename_str, str)

    record_list = []

    try:

        file_depth_data = open(filename_str, "r")
        record_list = [line_str.strip() for line_str in file_depth_data.readlines()]
        file_depth_data.close()

    except IOError:
        print "Could not open file named {0}".format(filename_str)
        exit()

    return record_list


def planar_least_sqauares_fit(x_list, y_list, z_list):
    determinant = np.column_stack((np.ones(len(x_list)), x_list, y_list))
    coeffs, residuals, rank, sigma = np.linalg.lstsq(determinant, z_list)

    c, a, b = coeffs
    coeffs = (a, b, c)      # I don't like the coefficients in the original order

    return coeffs


if "__main__" == __name__:
    filename_str = sys.argv[1] if 1 < len(sys.argv) else "depth_data.csv"

    record_list = read_data_file(filename_str)

    x_list, y_list, z_list = get_inputs(record_list)

    measured_coeffs = planar_least_sqauares_fit(x_list, y_list, z_list)
    a, b, c = measured_coeffs

    print
    print "Tool Travel Corner Locations:"
    print
    print "back-left: (-420,    0)                             back-right: (0,    0)"
    print "front-left:(-420, -370)                             front-right:(0, -370)"
    print
    print
    print "Least Squares Fit Formula for the measured data:"
    print
    print "{:.16f} * x  +  {:.16f} * y  +  {:.16f}  =  height (mm)".format(a, b, c)
    print
    print
    print "Measurement minima and maxima:"
    print
    print "X: min({:.3f}), max({:.3f})".format(min(x_list), max(x_list))
    print "Y: min({:.3f}), max({:.3f})".format(min(y_list), max(y_list))
    print "Z: min({:.3f}), max({:.3f})".format(min(z_list), max(z_list))
    print

    if abs(LFTMOST_X - min(x_list)) > EPSILON:
        print "Warning: No measurement taken at left extrema (:.3f).".format(LFTMOST_X)
    if abs(RGTMOST_X - max(x_list)) > EPSILON:
        print "Warning: No measurement taken at right extrema ({:.3f}).".format(RGTMOST_X)
    if abs(BACKMOST_Y - max(y_list)) > EPSILON:
        print "Warning: No measurement taken at back extrema (:.3f).".format(BACKMOST_Y)
    if abs(FRNTMOST_Y - min(y_list)) > EPSILON:
        print "Warning: No measurement taken at front extrema. (:.3f)".format(FRNTMOST_Y)

    # Calculate the locations of the mounting holes in the table's 4 corners
    frnt_rgt = ((RGTMOST_X + RGTMOST_MOUNT_OFFSET_X, FRNTMOST_Y + FRNTMOST_MOUNT_OFFSET_Y), "front-right")
    back_rgt = ((RGTMOST_X + RGTMOST_MOUNT_OFFSET_X, BACKMOST_Y + BACKMOST_MOUNT_OFFSET_Y), "back-right")
    back_lft = ((LFTMOST_X + LFTMOST_MOUNT_OFFSET_X, BACKMOST_Y + BACKMOST_MOUNT_OFFSET_Y), "back-left")
    frnt_lft = ((LFTMOST_X + LFTMOST_MOUNT_OFFSET_X, FRNTMOST_Y + FRNTMOST_MOUNT_OFFSET_Y), "front-left")

    # The maximum height of the 4 corner mounting points is used as the basis for adjustment,
    # since we assume that we can't lower the highest point, only raise the lower mounting points.
    #
    z_fr = get_z(measured_coeffs, frnt_rgt[0][0], frnt_rgt[0][1])
    z_br = get_z(measured_coeffs, back_rgt[0][0], back_rgt[0][1])
    z_bl = get_z(measured_coeffs, back_lft[0][0], back_lft[0][1])
    z_fl = get_z(measured_coeffs, frnt_lft[0][0], frnt_lft[0][1])

    diff_rl_100mm = 100.0 * max(abs(z_fl - z_fr), abs(z_bl - z_br)) / abs(LFTMOST_X - RGTMOST_X)
    diff_fb_100mm = 100.0 * max(abs(z_fl - z_bl), abs(z_fr - z_br)) / abs(FRNTMOST_Y - BACKMOST_Y)
    diff_diag_100 = math.sqrt(diff_rl_100mm**2 + diff_fb_100mm**2)

    print
    print
    print "A 100 mm diameter round part made with the current table will have different thicknesses."
    print "In the X direction (left-right), there will be a {:.3f} mm thickness difference.".format(diff_rl_100mm)
    print "In the Y direction (back-front), there will be a {:.3f} mm thickness difference.".format(diff_fb_100mm)
    print "In a diagonal direction, there will be a {:.3f} mm thickness difference.".format(diff_diag_100)

    max_mount_z = max(z_bl, z_br, z_fr, z_fl)

    # Adjust the measured coefficients, creating a new coeff set relative to the highest mount point
    c = c - max_mount_z
    coeffs = (a, b, c)

    print
    print
    print "Least Squares Fit Formula relative to the highest corner mount location:"
    print
    print "{:.16f} * x  +  {:.16f} * y  +  {:.16f}  =  height (mm)".format(a, b, c)
    print
    print
    print "Below is a table of the errors relative to the higest table mount position."
    print

    # Calculate the rest of the mount hole (pair) locations
    midl_rgt = ((RGTMOST_X + RGTMOST_MOUNT_OFFSET_X, (back_rgt[0][1] + frnt_rgt[0][1]) / 2.0), "middle-right")
    midl_lft = ((LFTMOST_X + LFTMOST_MOUNT_OFFSET_X, (back_lft[0][1] + frnt_lft[0][1]) / 2.0), "middle-left")
    midl_frnt = (((frnt_lft[0][0] + frnt_rgt[0][0]) / 2.0, FRNTMOST_Y + FRNTMOST_MOUNT_OFFSET_Y), "middle-front")
    midl_back = (((back_lft[0][0] + back_rgt[0][0]) / 2.0, BACKMOST_Y + BACKMOST_MOUNT_OFFSET_Y), "middle-back")
    middle = (((midl_back[0][0] + midl_frnt[0][0])/2.0, (midl_lft[0][1] + midl_rgt[0][1]) / 2.0), "table-middle")

    table_mount_point_list = [back_rgt, midl_back, back_lft, midl_lft, frnt_lft, midl_frnt, frnt_rgt, midl_rgt, middle]

    print
    for corner in table_mount_point_list:
        (x, y), desc_str = corner
        z = get_z(coeffs, x, y)
        print "{0:12s}: X({1:8.3f}), Y({2:8.3f}), Z({3:8.3f})".format(desc_str, x, y, z)

    print
    print
    print
    print
    print "To minimize milled thickness differences, raise the table at its mounting holes "
    print " by the amounts (in mm) indicated below:"
    print
    print
    print "                BACK"
    print
    print "        {0:.3f}   {1:.3f}   {2:.3f}".format(get_z_by_name("back-left"),
                                                       get_z_by_name("middle-back"),
                                                       get_z_by_name("back-right"))
    print
    print "LEFT    {0:.3f}   {1:.3f}   {2:.3f}    RIGHT".format(get_z_by_name("middle-left"),
                                                                get_z_by_name("table-middle"),
                                                                get_z_by_name("middle-right"))
    print
    print "        {0:.3f}   {1:.3f}   {2:.3f}".format(get_z_by_name("front-left"),
                                                       get_z_by_name("middle-front"),
                                                       get_z_by_name("front-right"))
    print
    print "                FRONT"
