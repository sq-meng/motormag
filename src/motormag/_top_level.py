import motormag.motor as motor
import motormag.mag as mag


def init(motor_port=8, mag_port=16):
    motor.init(motor_port)
    mag.init(mag_port)


def close():
    motor.close()
    mag.close()

