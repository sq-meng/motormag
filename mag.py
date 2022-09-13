# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 16:04:49 2022

@author: npol3he
"""


import numpy as np
import serial
import re


CH3600 = True
PORT_GAUSS = 'COM16'
MOCK = False
DEV = False


# _s_gauss = serial.Serial(PORT_GAUSS, 115200, timeout=1)
# _s_gauss.write(b'DATA?>')

def read_once(flush=True):
    """
    Reads latest reading from CH330 or CH3600 gaussmeter.
    :return: Length-3 ndarray, fields in x, y, z directions.
    """
    while True:
        if MOCK:
            print('read once!')
            return np.array([1, 2, 3])
        if flush:
            gauss_port.read_all()
            gauss_port.read_until(b'\n')
        raw_msg = gauss_port.read_until(b'\n').decode(encoding='ascii')
        if CH3600:
            pattern = '#([-+]?\d*\.{0,1}\d+)/.*?;([-+]?\d*\.{0,1}\d+)/.*?;([-+]?\d*\.{0,1}\d+)/.*?>'
        else:
            pattern = '#([-+]?\d*\.{0,1}\d+)/([-+]?\d*\.{0,1}\d+)/([-+]?\d*\.{0,1}\d+)\>'
        msg = re.findall(pattern, raw_msg)
        if len(msg) != 0:
            break
        else:
            print("invalid message received: %s" % str(raw_msg))
    msg = msg[0]
    if DEV:
        print('raw: %s, trimmedL %s' % (raw_msg, msg))
    return np.array([float(x) for x in msg])


def read_n_times(reps):
    values = [read_once()]
    for i in range(reps-1):
        values.append(read_once(flush=False))
    return np.average(values, axis=0)


def init(port):
    if isinstance(port, int):
        port = "COM%d" % port
    global gauss_port
    gauss_port = serial.Serial(port, 115200, timeout=1)
    gauss_port.write(b'DATA?>')


def close():
    global gauss_port
    gauss_port.close()