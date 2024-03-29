from . import log
from . import motor
from . import mag
import numpy as np
import pandas as pd


class BoxScan(object):
    def __init__(self, x_range, y_range, z_range, x_steps=None, y_steps=None, z_steps=None, step_size=5, order='zxy',
             time_wait=0.5, n_discards=0, n_reps=3):
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.x_steps = x_steps
        self.y_steps = y_steps
        self.z_steps = z_steps
        self.step_size = step_size
        self.order = order
        self.time_wait = time_wait
        self.n_discards=n_discards
        self.n_reps = n_reps

        self.data = None

    def run(self):
        pass


def range_to_points(range_def, steps=None, step_size=5):
    """
    Converts a scan range definition into list of points.
    :param range_def: [start, end] or a single number.
    :param steps: Number of steps, ignored if range_def is a single number.
    :param step_size: Difference between steps, ignored if total number of steps given.
    :return: A list of numbers.
    """
    if step_size == 0:
        raise ValueError('Step size cannot be zero')
    try:
        start = range_def[0]
        end = range_def[1]
    except TypeError:
        return np.array([range_def])
    if steps is not None:
        if start == end:
            return np.array([start])
        return np.linspace(start, end, steps)
    else:
        if abs(end - start) % step_size > 0.1:
            raise ValueError("Span of scan is not a multiple of step size")
        return np.linspace(start, end, int(abs(end - start) / step_size) + 1)


def _order_sanity(order):
    try:
        if 'x' in order and 'y' in order and 'z' in order and len(order) == 3:
            return True
        else:
            return False
    except (ValueError, TypeError):
        return False


def _get_step_size(points):
    try:
        return points[1] - points[0]
    except IndexError:
        return np.NaN


def _test_corners(x_points, y_points, z_points, speed=10):
    """
    Drives the motor stage to all 8 corners of the scan before actually scanning to avoid crashing with no one around.
    :param x_points: a list of all x axis points to be scanned.
    :param y_points: see x
    :param z_points: see x
    :param speed: speed to do the test
    :return: None. Ctrl + C to abort.
    """
    x_min, x_max = min(x_points), max(x_points)
    y_min, y_max = min(y_points), max(y_points)
    z_min, z_max = min(z_points), max(z_points)
    log.log('Driving to 8 corners of test volume.')
    motor.multi_absolute_move([x_min, y_min, z_min], speed=speed)
    motor.multi_absolute_move([x_max, y_min, z_min], speed=speed)
    motor.multi_absolute_move([x_max, y_max, z_min], speed=speed)
    motor.multi_absolute_move([x_max, y_min, z_min], speed=speed)
    motor.multi_absolute_move([x_min, y_min, z_max], speed=speed)
    motor.multi_absolute_move([x_max, y_min, z_max], speed=speed)
    motor.multi_absolute_move([x_max, y_max, z_max], speed=speed)
    motor.multi_absolute_move([x_max, y_min, z_max], speed=speed)


def box_scan(x_range, y_range, z_range, x_steps=None, y_steps=None, z_steps=None, step_size=5, order='zxy',
             n_discards=1, n_reps=3):
    """
    Does a scan in a cubic volume.
    :param x_range: [start, end] or single value. Give a single value if the axis is not to be scanned.
    :param y_range: see x
    :param z_range: see x
    :param x_steps: number of x direction steps
    :param y_steps: see x
    :param z_steps: see x
    :param step_size: [x_step, y_step, z_step] or single value. Single value will be used for all 3 axes.
    :param order: length-3 string consisting of letters x, y and z. 1st axis is moved the least - defaults to z as it's
    the heaviest.
    :param n_discards: Drop first n mag field readings to give the probe time to settle.
    :param n_reps: Number of readings to take and average over.
    :return: pd.DataFrame containing data.
    """
    if not all(np.abs(np.array(motor.get_position())) < 0.1):
        raise RuntimeError('Motor stage not at zero - manually drive to zero before scanning.')
    if not _order_sanity(order):
        raise ValueError('Got invalid scan order: %s' % str(order))
    x_points = range_to_points(x_range, x_steps, step_size)
    y_points = range_to_points(y_range, y_steps, step_size)
    z_points = range_to_points(z_range, z_steps, step_size)
    _test_corners(x_points, y_points, z_points)
    # Un-flattening xm, ym and zm by shape (x_steps, y_steps, z_steps) returns them to the matrix form.
    xm, ym, zm = np.meshgrid(x_points, y_points, z_points, indexing='ij')
    data = np.vstack([xm.flatten(), ym.flatten(), zm.flatten(), np.zeros([6, len(xm.flatten())])]).T
    df = pd.DataFrame(data, columns=['x', 'y', 'z', 'mag_x', 'mag_y', 'mag_z', 'temp_x', 'temp_y', 'temp_z'])
    # Motor movement order sorting: y-axis should move the most and z the least.
    df.sort_values([*order], inplace=True)
    log.log('Starting box scan.')
    total_points = len(df.index)
    for nth, i in enumerate(df.index):
        x, y, z = df.loc[i, ['x', 'y', 'z']]
        motor.multi_absolute_move([x, y, z])
        for _ in range(n_discards):
            mag.read_once()
        df.loc[i, ['mag_x', 'mag_y', 'mag_z', 'temp_x', 'temp_y', 'temp_z']] = mag.read_n_times(n_reps)
        log.log('%d/%d, field at %.2f, %.2f, %.2f: %.2fmT, %.2fmT, %.2fmT' % (nth + 1, total_points, x, y, z,
                                                                              *df.loc[i, ['mag_x', 'mag_y', 'mag_z']]))
    motor.multi_absolute_move([0, 0, 0])
    df.sort_index(inplace=True)
    df.attrs['lengths'] = [len(x_points), len(y_points), len(z_points)]
    df.attrs['step_sizes'] = [_get_step_size(x_points), _get_step_size(y_points), _get_step_size(z_points)]
    return df
