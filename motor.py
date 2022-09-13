# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 10:00:40 2022

A wrapper module for WNMC400 stepper controller
@author: Siqin Meng
"""


import clr
clr.AddReference("./res/MCC4DLL")
# noinspection PyUnresolvedReferences
from clr import SerialPortLibrary
import System
import time
import signal
import log


def init(port):
    """
    Opens serial port.
    :param port:(int, str), int X means COMX, or str 'COM8'
    :return: status code from dll library
    """
    if isinstance(port, int):
        port = "COM%d" % port
    result = motor_port.MoCtrCard_Initial(System.String(port))
    if result == 1:
        log.log("Motor serial port %s opened." % port)
    else:
        log.fail("Motor serial port %s failed to open." % port)
    return result


def close():
    """
    Closes serial port.
    :return: status code
    """
    result = motor_port.MoCtrCard_Unload()
    if result == 1:
        log.log("Motor serial port closed.")
    else:
        log.fail("Motor serial port failed to close.")
    return result


def relative_move_raw(axis_id, distance, block=True):
    """
    Relative movement using the non-gcode built-in method.
    :param axis_id: (0, 1, 2) for x, y and z respectively.
    :param distance: distance in mm.
    :param block: if block until finished.
    :return: status code
    """
    result = motor_port.MoCtrCard_MCrlAxisRelMove(System.Byte(axis_id), System.Single(distance))
    if block:
        wait()
    return result


def set_position(axis_id, value):
    """
    Overrides current position value with given value, not driving.
    :param axis_id: (0, 1, 2) for x, y and z respectively.
    :param value: value in mm.
    :return: status code
    """
    return motor_port.MoCtrCard_ResetCoordinate(System.Byte(axis_id), System.Single(value))


def zero():
    """
    Set current position as zero for all axes.
    :return: None
    """
    set_position(0, 0.0)
    set_position(1, 0.0)
    set_position(2, 0.0)


def stop():
    """
    Gracefully stops all axis movements.
    :return: None
    """
    motor_port.MoCtrCard_StopAxisMov(System.Byte(0))
    motor_port.MoCtrCard_StopAxisMov(System.Byte(1))
    motor_port.MoCtrCard_StopAxisMov(System.Byte(2))


def mdi_command(command):
    """
    Sends GCode to controller.
    :param command: str, GCode
    :return: status code
    """
    result = motor_port.MoCtrCard_SendMDICommand(System.String(command))
    if result != 1:
        log.warn("Gcode returned an error.")
    return result


def relative_move(axis_id, distance, speed=25, acceleration=0.3, block=True, delay=0.0):
    """
    Single-axis relative move using Gcode (G80)
    :param axis_id: (0, 1, 2) for x, y and z respectively.
    :param distance: distance in mm.
    :param speed: speed in mm/s
    :param acceleration: acceleration in arbitrary units.
    :param block: block until finished moving.
    :param delay: block even more seconds after finishing.
    :return: status code
    """
    if axis_id == 0:
        axis = 'X'
    elif axis_id == 1:
        axis = 'Y'
    elif axis_id == 2:
        axis = 'Z'
    else:
        raise ValueError('axis not in [0, 1, 2]')
        
    gcode = "G80{ax}{dist}F{ax}{spd}A{ax}{acc}D0".format(ax=axis, dist=distance, spd=speed, acc= acceleration)
    result = mdi_command(gcode)
    if block:
        wait(delay)
    return result


def multi_relative_move(distance, speed=25, acceleration=0.3, coordinated=True, block=True, delay=0.0):
    """
    3-axis relative move using Gcode (G80)
    :param distance: [x, y, z] distance in mm.
    :param speed: spd or [spd_x, spd_y, spd_z]speed in mm/s. Scalar value is interpreted as total speed when
    coordinated, and as speed for each axis when not coordinated. 1st value in list is used as coordinated speed.
    :param acceleration: acceleration in arbitrary units.
    :param coordinated: If all 3 axes move in sync.
    :param block: block until finished moving.
    :param delay: block even more seconds after finishing.
    :return: status code
    """
    try:
        _, _, _ = distance
    except (TypeError, ValueError, IndexError):
        raise ValueError("distance should be a length-3 list")
    try:
        _, _, _ = speed
    except TypeError:
        speed = [speed, speed, speed]        
    acceleration = [acceleration, acceleration, acceleration]
    
    if coordinated:
        gcode_template = "G81X{d[0]:.1f}Y{d[1]:.1f}Z{d[2]:.1f}F{s[0]:.1f}A{a[0]:.1f}D0"
    else:    
        gcode_template = "G80X{d[0]:.1f}FX{s[0]:.1f}AX{a[0]:.1f}Y{d[1]:.1f}FY{s[1]:.1f}AY{a[1]:.1f}Z{d[2]:.1f}FZ{s[2]:.1f}AZ{a[2]:.1f}D0"
    
    gcode = gcode_template.format(d=distance, s=speed, a=acceleration)
    mdi_command(gcode)
    if block:
        wait(delay)
    

def multi_absolute_move(target, speed=25, acceleration=0.3, coordinated=True, block=True, delay=0.0):
    """
    See relative version.
    :param target:
    :param speed:
    :param acceleration:
    :param coordinated:
    :param block:
    :param delay:
    :return:
    """
    try:
        _, _, _ = target
    except (TypeError, ValueError, IndexError):
        raise ValueError("distance should be a length-3 list")
    try:
        _, _, _ = speed
    except TypeError:
        speed = [speed, speed, speed]
    acceleration = [acceleration, acceleration, acceleration]
    if coordinated:
        gcode_template = "G01X{d[0]:.1f}Y{d[1]:.1f}Z{d[2]:.1f}F{s[0]:.1f}A{a[0]:.1f}D0"
    else:    
        gcode_template = "G00X{d[0]:.1f}FX{s[0]:.1f}AX{a[0]:.1f}Y{d[1]:.1f}FY{s[1]:.1f}AY{a[1]:.1f}Z{d[2]:.1f}FZ{s[2]:.1f}AZ{a[2]:.1f}D0"
        
    gcode = gcode_template.format(d=target, s=speed, a=acceleration)
    mdi_command(gcode)
    if block:
        wait(delay)


def get_position():
    """
    Gets current [x, y, z].
    :return: [x, y, z] in mm.
    """
    arr = System.Array.CreateInstance(System.Single, 4)
    motor_port.MoCtrCard_GetAxisPos(System.Byte(255), arr)
    return [arr[0], arr[1], arr[2]]


def is_running():
    """
    Query if any axis is in movement.
    :return: bool
    """
    arr = System.Array.CreateInstance(System.Int32, 1)
    motor_port.MoCtrCard_GetRunState(arr)
    return arr[0] % 2 == 1


def wait(delay=0.0):
    """
    Blocks until all axes stop moving.
    :param delay: further wait after stopping.
    :return: None
    """
    while True:
        if is_running():
            time.sleep(0.2)
        else:
            break
    time.sleep(delay)


motor_port = SerialPortLibrary.SPLibClass()
              
if __name__ == "__main__":
    init('COM8')
