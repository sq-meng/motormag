# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 16:04:49 2022

@author: npol3he
"""


import numpy as np
import serial
import re

from motormag import log
from motormag._mode import MOCK, CH3600

DEV = False


# _s_gauss = serial.Serial(PORT_GAUSS, 115200, timeout=1)
# _s_gauss.write(b'DATA?>')


def parse_ch3600_serial(string):
    # pattern = '#([-+]?\d*\.{0,1}\d+)/([-+]?\d*\.{0,1}\d+)/([-+]?\d*\.{0,1}\d+)\>' for CH330
    pattern = r'#([-+]?\d*\.?\d+)/.*?([-+]?\d+);([-+]?\d*\.?\d+)/.*?([-+]?\d+);([-+]?\d*\.?\d+)/.*?([-+]?\d+)>'
    mag_x, temp_x, mag_y, temp_y, mag_z, temp_z = re.findall(pattern, string)[0]
    return [mag_x, mag_y, mag_z, temp_x, temp_y, temp_z]


def read_once(flush=True):
    """
    Reads latest reading from CH330 or CH3600 gaussmeter.
    :flush: if the serial port buffer should be flushed
    :return: Length-6 ndarray, fields in x, y, z directions, followed by temp reading of x, y, z probes.
    """
    while True:
        if MOCK:
            log.mock('Read gaussmeter.')
            raw_msg = r'#00000.0097/000/+0256;-00000.0003/000/+0256;-00000.0027/000/+256>'
        else:
            if flush:
                serial_port.read_all()
                serial_port.read_until(b'\n')
            raw_msg = serial_port.read_until(b'\n').decode(encoding='ascii')
        if CH3600:
            try:
                mags_and_temps = parse_ch3600_serial(raw_msg)
                break
            except (IndexError, ValueError):
                log.warn('Invalid message received: %s' % raw_msg)
    #         pattern = '#([-+]?\d*\.{0,1}\d+)/.*?;([-+]?\d*\.{0,1}\d+)/.*?;([-+]?\d*\.{0,1}\d+)/.*?>'
    #     msg = re.findall(pattern, raw_msg)
    #     if len(msg) != 0:
    #         break
    #     else:
    #         log.warn("invalid message received: %s" % str(raw_msg))
    # msg = msg[0]

    mags_and_temps_array = np.array([float(x) for x in mags_and_temps])
    mags_and_temps_array[3:] = mags_and_temps_array[3:] / 10
    if MOCK:
        mags_and_temps_array = mags_and_temps_array + np.random.random(6)* 5 - 2.5
    return mags_and_temps_array


def read_n_times(reps):
    values = [read_once()]
    for i in range(reps-1):
        values.append(read_once(flush=False))
    return np.average(values, axis=0)


def init(port):
    if isinstance(port, int):
        port = "COM%d" % port
    global serial_port
    serial_port = serial.Serial(port, 115200, timeout=5)
    serial_port.write(b'DATA?>')


def close():
    global serial_port
    serial_port.close()
