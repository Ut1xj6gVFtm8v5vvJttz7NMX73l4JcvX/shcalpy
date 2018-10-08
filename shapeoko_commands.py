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
import serial
import time


class ToolPosition:
    """
    Structure for defining a Shapeoko tool position as an (X, Y, Z) point.
    """
    def __init__(self, x, y, z):
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)
        self.__x = x
        self.__y = y
        self.__z = z

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def z(self):
        return self.__z

    @x.setter
    def x(self, x):
        assert isinstance(x, float)
        self.__x = x

    @y.setter
    def y(self, y):
        assert isinstance(y, float)
        self.__y = y

    @z.setter
    def z(self, z):
        assert isinstance(z, float)
        self.__z = z


# GLOBALS INCLUDE:
#   curpos
#   __cmd_count
#   __shapeoko_port

curpos = ToolPosition(x=0.0, y=0.0, z=0.0)    # current position

__shapeoko_port = None          # used to communicate with the Shapeoko over the USB serial port
__cmd_count = 0                 # normally unused, helpful for debugging; see COMMAND_LOGGING_ENABLED

VERIFY_NEGATIVE_VALUES = True   # If True, verifies move() and goto() values are between XMIN, XMAX, YMIN, YMAX
COMMAND_LOGGING_ENABLED = False # If True, module prints each GCODE command with its sequence nbr
SLEEP_BEFORE_ESTOP = 5          # Allows user to examine situation, set breakpoint in debugger (e.g. use 30)
STEP_DISTANCE_MM = 0.025        # Shapeoko moves the same minimal step distance in X, Y, and Z

# Since our coordinate system is defined from (0, 0), it is common to think of that as the minimum value.
# However, the useful range of motion is only in the negative range of x and y values.  For the purposes
# of this program therefor, XMAX and YMAX will be negative values.
XMIN, XMAX, XINC = 0.0, -420.0, STEP_DISTANCE_MM
YMIN, YMAX, YINC = 0.0, -370.0, STEP_DISTANCE_MM
# These are very slightly less than the actual range of the machine.

# While ZMIN can be fixed to be 0, ZMAX depends upon the size of the tool.  It must be overridden by
# user of the module if used.
ZMIN, ZMAX, ZINC = 0.0, None, STEP_DISTANCE_MM


def is_x_valid(x):
    """
    (If VERIFY_NEGATIVE_VALUES is True,) validate x value

    Note, the XINC extra little bit of slop allows the jiggle_xy() calls to execute on the edges

    :param x:   position on the X axis

    :return:    True if Valid, False otherwise
    """
    assert isinstance(x, float)

    return (XMAX - XINC) <= x <= (XMIN + XINC)


def is_y_valid(y):
    """
    (If VERIFY_NEGATIVE_VALUES is True), validate y value

    Note: the YINC extra little bit of slop allows the jiggle_xy() calls to execute on the edges

    :param y: position on the Y axis

    :return:    True if Valid, False otherrwise
    """
    assert isinstance(y, float)
    return (YMAX - YINC) <= y <= (YMIN + YINC)


def read_3_reset_startup_lines():
    """
    Connect to the Shapeoko, printing and returning the 1st 3 lines.

    :return:    3 strings: the 1st 3 lines from the initial Shapeoko connect
    """
    global __shapeoko_port

    time.sleep(0.01)
    line1_str = __shapeoko_port.readline().strip()
    time.sleep(0.01)
    line2_str = __shapeoko_port.readline().strip()
    time.sleep(0.01)
    line3_str = __shapeoko_port.readline().strip()

    print line1_str  # blank line
    print line2_str  # "Grbl 1.1f ['$' for help]"
    print line3_str  # "[MSG:'$H'|'$X' to unlock]"

    return line1_str, line2_str, line3_str


def connect_and_synchronize():
    """
    Connect to the Shapeoko/GRBL via the USB port.  Verify that the connection is established.

    :return:    nothing
    """
    global __shapeoko_port

    __shapeoko_port = serial.Serial("/dev/ttyACM0",
                                    baudrate=115200,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE,
                                    bytesize=serial.EIGHTBITS,
                                    writeTimeout=0,
                                    timeout=30,
                                    rtscts=False,
                                    dsrdtr=False,
                                    xonxoff=False)

    line1_str, line2_str, line3_str = read_3_reset_startup_lines()

    while "[MSG:'$H'|'$X' to unlock]" != line3_str and "Grbl 1.1f ['$' for help]" != line2_str:
        ctrl_x_int = 0x18
        ctrl_x_chstr = chr(ctrl_x_int)
        output_and_log(ctrl_x_chstr)
        time.sleep(1)
        line1_str, line2_str, line3_str = read_3_reset_startup_lines()


def read_port_await_str(expected_response_str):
    """
    It appears that the Shapeoko responds with the string "ok" (or an "err nn" string) when
    a command is processed.  Read the shapeoko_port and verify the response string in this routine.
    If an error occurs, a message.

    :param expected_response_str:   a string, typically "ok"

    :return:    True if "ok" received, otherwise False
    """
    assert isinstance(expected_response_str, str)
    global __shapeoko_port

    response_str = __shapeoko_port.readline().strip()

    if expected_response_str != response_str:
        print "RESPONSE_STR_LEN({0}), RESPONSE_STR({1})".format(len(response_str), response_str)

    return expected_response_str == response_str


def output_and_log(cmd_str):
    """
    Write the command string to the Shapeoko shapeoko_port, logging it to console if enabled.

    :param cmd_str: Shapeoko command string

    :return:    nothing
    """
    assert isinstance(cmd_str, str)
    global __shapeoko_port
    global __cmd_count

    __cmd_count += 1    # Use this help track down problems
    if COMMAND_LOGGING_ENABLED:
        print "{0:5d}: '{1}'".format(__cmd_count, cmd_str)

    __shapeoko_port.write("{0}\n".format(cmd_str))


def home_system():
    """
    Issue a Home command to the Shapeoko.  After this, the machine's coordinate system is usable.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert home_system(), "Useful message indicating where failure occurred"

    :return:    True -> success, False -> not so much
    """
    output_and_log("$H")

    responded = read_port_await_str("ok")

    if not responded:
        print "home_system() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)

    return responded


def define_wcs2_to_current_mcs_in_eprom():
    """
    Set a coordinate system named "2" to the machine's current X, Y, and Z; record it in EPROM.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert define_wcs2_to_current_mcs_in_eprom(), "Useful message indicating where failure occurred"

    :return:    True -> success, False -> failure
    """
    output_and_log("G10 L20 P2 X0 Y0 Z0")

    responded = read_port_await_str("ok")

    if not responded:
        print "define_wcs2_to_current_mcs() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)

    return responded


def set_wcs_to_wcs2():
    """
    Start using the coordinate system name "2" for subsequent G00 and G01 X, Y, Z commands.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert set_wcs_to_wcs2(), "Useful message indicating where failure occurred"

    :return:    True -> success, False -> failure
    """
    output_and_log("G55")

    responded = read_port_await_str("ok")

    if not responded:
        print "set_wcs_to_current_mcs() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)

    return responded


def move_x(new_x, speed_mm_s=1000.0):
    """
    Move tool to the new_x position at speed_mm_s.  Update curpos.x with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert move_x(new_x_value), "Useful message indicating where failure occurred"

    :param new_x:       new X position of tool
    :param speed_mm_s:  speed in mm/s

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_x, float)
    if VERIFY_NEGATIVE_VALUES:
        assert is_x_valid(new_x)
    assert isinstance(speed_mm_s, float) and 1. <= speed_mm_s <= 1000.
    global curpos

    output_and_log("G01 X{0:3.3f} F{1:3.3f}".format(new_x, speed_mm_s))

    responded = read_port_await_str("ok")

    if not responded:
        print "move_x() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.x = new_x

    return responded


def move_y(new_y, speed_mm_s=1000.0):
    """
    Move tool to the new_y position at speed_mm_s.  Update curpos.y with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert move_y(new_y_value), "Useful message indicating where failure occurred"

    :param new_y:       new Y position of tool
    :param speed_mm_s:  speed in mm/s

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_y, float)
    if VERIFY_NEGATIVE_VALUES:
        assert is_y_valid(new_y)
    assert isinstance(speed_mm_s, float) and 1. <= speed_mm_s <= 1000.
    global curpos

    output_and_log("G01 Y{0:3.3f} F{1:3.3f}".format(new_y, speed_mm_s))

    responded = read_port_await_str("ok")

    if not responded:
        print "move_y() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.y = new_y

    return responded


def move_xy(new_x, new_y, speed_mm_s=1000.0):
    """
    Move tool to the (new_x, new_y) position at speed_mm_s.  Update curpos.x and curpos.y with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert move_xy(new_x_value, new_y_value), "Useful message indicating where failure occurred"

    :param new_x:       new X position of tool
    :param new_y:       new Y position of tool
    :param speed_mm_s:  speed in mm/s

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_x, float)
    assert isinstance(new_y, float)
    if VERIFY_NEGATIVE_VALUES:
        assert is_x_valid(new_x)
        assert is_y_valid(new_y)
    assert isinstance(speed_mm_s, float) and 1. <= speed_mm_s <= 1000.
    global curpos

    output_and_log("G01 X{0:3.3f} Y{1:3.3f} F{2:3.3f}".format(new_x, new_y, speed_mm_s))

    responded = read_port_await_str("ok")

    if not responded:
        print "move_xy() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.x = new_x
        curpos.y = new_y

    return responded


def move_z(new_z, speed_mm_s=1000.0):
    """
    Move tool to the new_z position at speed_mm_s.  Update curpos.z with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert move_z(new_z_value), "Useful message indicating where failure occurred"

    :param new_z:       new Z position of tool
    :param speed_mm_s:  speed in mm/s

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_z, float)
    if VERIFY_NEGATIVE_VALUES:
        assert new_z <= XMIN
    assert isinstance(speed_mm_s, float) and 1. <= speed_mm_s <= 1000.
    global curpos

    output_and_log("G01 Z{0:3.3f} F{1:3.3f}".format(new_z, speed_mm_s))

    responded = read_port_await_str("ok")

    if not responded:
        print "move_z() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.z = new_z

    return responded


def goto_x(new_x):
    """
    Move tool to the new_x position at speed_mm_s at high speed.    Update curpos.x with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert goto_x(new_x_value), "Useful message indicating where failure occurred"

    :param new_x:       new X position of tool

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_x, float)
    if VERIFY_NEGATIVE_VALUES:
        assert is_x_valid(new_x)
    global curpos

    output_and_log("G00 X{0:3.3f}".format(new_x))

    responded = read_port_await_str("ok")

    if not responded:
        print "goto_x() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.x = new_x

    return responded


def goto_y(new_y):
    """
    Move tool to the new_y position at speed_mm_s at high speed.    Update curpos.y with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert goto_y(new_y_value), "Useful message indicating where failure occurred"

    :param new_y:       new Y position of tool

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_y, float)
    if VERIFY_NEGATIVE_VALUES:
        assert is_y_valid(new_y)
    global curpos

    output_and_log("G00 Y{0:3.3f}".format(new_y))

    responded = read_port_await_str("ok")

    if not responded:
        print "goto_y() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.y = new_y

    return responded


def goto_xy(new_x, new_y):
    """
    Move tool to the (new_x, new_y) position at speed_mm_s at high speed.
    Update curpos.x and curpos.y with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert goto_xy(new_z_value, new_y_value), "Useful message indicating where failure occurred"

    :param new_x:       new X position of tool
    :param new_y:       new Y position of tool

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_x, float)
    assert isinstance(new_y, float)
    if VERIFY_NEGATIVE_VALUES:
        assert is_x_valid(new_x)
        assert is_y_valid(new_y)
    global curpos

    output_and_log("G00 X{0:3.3f} Y{1:3.3f}".format(new_x, new_y))

    responded = read_port_await_str("ok")

    if not responded:
        print "goto_x() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.x = new_x
        curpos.y = new_y

    return responded


def goto_z(new_z):
    """
    Move tool to the new_z position at speed_mm_s at high speed.    Update curpos.z with new position.

    If a failure is detected, sleep so the operator can examine the situation.
    Since the loss of expected responses to commands indicates that the program does not know
    the exact position of the device, the caller should immediately abort on a failure.

    Call this function like this:

        assert goto_z(new_z_value), "Useful message indicating where failure occurred"

    :param new_z:       new Z position of tool

    :return:    True -> success, False -> failure
    """
    assert isinstance(new_z, float)
    if VERIFY_NEGATIVE_VALUES:
        assert new_z <= ZMIN
    global curpos

    output_and_log("G00 Z{0:3.3f}".format(new_z))

    responded = read_port_await_str("ok")

    if not responded:
        print "goto_z() RESPONSE STRING({0}) NOT RECEIVED".format("ok")
        time.sleep(SLEEP_BEFORE_ESTOP)
    else:
        curpos.z = new_z

    return responded


def jiggle_xy(iterations=1):
    """
    Move tool around the current tool position in X and Y by minimal step distance

    The Shapeoko/GRBL has a buffered input mechanism.  It receives the USB/Serial commands, and
    can issue its OK response immediately, but schedules them as it chooses.  It also appears that
    the G00 and G01 commands may sometimes be elided?!
    Calling jiggle_xy() can help the caller maintain synchronization between the large command move
    requests and the OK responses; this is useful when using the tool to take sensor readings at
    commanded locations.

    :return:    True
    """
    x1 = curpos.x
    y1 = curpos.y
    for i in range(iterations):
        assert move_xy(x1 + STEP_DISTANCE_MM, y1 + STEP_DISTANCE_MM), "Failed to jiggle_xy() step 1"
        assert move_x(x1 - STEP_DISTANCE_MM), "Failed to jiggle_xy() step 2"
        assert move_y(y1 - STEP_DISTANCE_MM), "Failed to jiggle_xy() step 3"
        assert move_x(x1 + STEP_DISTANCE_MM), "Failed to jiggle_xy() step 4"
        assert move_xy(x1, y1), "Failed to jiggle_xy() step 5"
    return True


if "__main__" == __name__:
    connect_and_synchronize()   # Initializes __shapeoko_port and curpos for subsequent commands
    assert home_system()        # This moves the tool to the back-right corner of the table

    # Since this is the "home" position determined by the sensor switches, let's call it (0, 0, 0)
    assert move_x(0.0)          # Shouldn't be a whole lot of motion here :-)
    assert move_y(0.0)
    assert move_z(0.0)

    # The Coordinate System frame of reference is easy to imagine if you're standing in front of the machine.
    # The X axis moves left-right.  Since 0 on the X axis is on the far right, the moving to the left means giving
    # a negative X value.
    # Similarly, the Y axis moves front-back.  Since 0 on the Y axis is away from you in the far back of the machine,
    # all moves will be in the region toward you, toward the "front" of the machine.  So all Y commands will have
    # negative values (or 0).
    # After the machine is homed, the 0 Z axis position is pretty high off the table.  Moving upward would be
    # a more positive value than the current position, so all useful Z axis moves will have negative Z values.

    # From what I understand, a GRBL machine has it's own "machine coordinate system" that it never forgets and
    # always uses internally.  The GRBL model allows the user to define a few user-friendly coordinate systems,
    # and commands can be given using this user-specified coordinate system.  For user coordinate systems, GRBL
    # maintains an x, y, and z difference vector to map a user command to the machine coordinate system, which
    # it does invisibly and automatically.  (No axis rotations are allowed, only translations.)

    assert define_wcs2_to_current_mcs_in_eprom()    # set the user coordinate system up using the current MCS as (0,0,0)

    print "Issuing the move_xy() calls to move to the 4 corners."
    assert move_xy(XMIN, YMIN)  # back right (home)
    jiggle_xy()
    assert move_xy(XMAX, YMIN)  # back left
    jiggle_xy()
    assert move_xy(XMAX, YMAX)  # front left
    jiggle_xy()
    assert move_xy(XMIN, YMAX)  # front right
    jiggle_xy()
    assert move_xy(XMIN, YMIN)  # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the goto_xy() calls to move to the 4 corners."
    assert goto_xy(XMIN, YMIN)  # back right (home)
    jiggle_xy()
    assert goto_xy(XMAX, YMIN)  # back left
    jiggle_xy()
    assert goto_xy(XMAX, YMAX)  # front left
    jiggle_xy()
    assert goto_xy(XMIN, YMAX)  # front right
    jiggle_xy()
    assert goto_xy(XMIN, YMIN)  # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the move_x() calls to move to the X-axis extents."
    assert move_x(XMIN)     # back right (home)
    jiggle_xy()
    assert move_x(XMAX)     # back left
    jiggle_xy()
    assert move_x(XMIN)     # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the goto_x() calls to move to the X-axis extents."
    assert goto_x(XMIN)     # back right (home)
    jiggle_xy()
    assert goto_x(XMAX)     # back left
    jiggle_xy()
    assert goto_x(XMIN)     # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the move_y() calls to move to the Y-axis extents."
    assert move_y(YMIN)     # back right (home)
    jiggle_xy()
    assert move_y(YMAX)     # front right
    jiggle_xy()
    assert move_y(YMIN)     # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the goto_y() calls to move to the Y-axis extents."
    assert goto_y(YMIN)     # back right (home)
    jiggle_xy()
    assert goto_y(YMAX)     # front right
    jiggle_xy()
    assert goto_y(YMIN)     # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the move_z() calls to move along the Z-axis by 10 mm."
    assert move_z(ZMIN)     # back right (home)
    jiggle_xy()             # when manipulating Z, still use jiggle_xy()
    assert move_z(ZMIN - 10.0)
    jiggle_xy()
    assert move_z(ZMIN)     # back right (home)
    jiggle_xy()
    time.sleep(1)
    print "Issuing the goto_z() calls to move along the Z-axis by 10 mm."
    assert goto_z(ZMIN)     # back right (home)
    jiggle_xy()
    assert goto_z(ZMIN - 10.0)
    jiggle_xy()
    assert goto_z(ZMIN)     # back right (home)
    jiggle_xy()
    print "Test Complete."
