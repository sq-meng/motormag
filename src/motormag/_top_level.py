# import motormag.motor as motor
# import motormag.mag as mag
# import motormag.draw as draw
# import motormag.scan as scan
from . import motor
from . import mag
from . import draw
from . import scan


def init(motor_port=8, mag_port=16):
    motor.init(motor_port)
    mag.init(mag_port)


def close():
    motor.close()
    mag.close()

