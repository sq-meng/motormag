from motormag import log
from motormag import motor
from motormag import mag
import numpy as np
import pandas as pd


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


def get_step_size(points):
    try:
        return points[1] - points[0]
    except IndexError:
        return np.NaN


def test_corners(x_points, y_points, z_points, speed=10):
    x_min, x_max = min(x_points), max(x_points)
    y_min, y_max = min(y_points), max(y_points)
    z_min, z_max = min(z_points), max(z_points)
    log.log('Driving to 8 corners of test volume.')
    motor.multi_absolute_move([x_min, y_min, z_min])
    motor.multi_absolute_move([x_max, y_min, z_min])
    motor.multi_absolute_move(([x_max, y_max, z_min]))
    motor.multi_absolute_move([x_max, y_min, z_min])
    motor.multi_absolute_move([x_min, y_min, z_max])
    motor.multi_absolute_move([x_max, y_min, z_max])
    motor.multi_absolute_move(([x_max, y_max, z_max]))
    motor.multi_absolute_move([x_max, y_min, z_max])


def box_scan(x_range, y_range, z_range, x_steps=None, y_steps=None, z_steps=None, step_size=5, order='zxy',
             n_reps=3):
    motor.zero()
    x_points = range_to_points(x_range, x_steps, step_size)
    y_points = range_to_points(y_range, y_steps, step_size)
    z_points = range_to_points(z_range, z_steps, step_size)
    test_corners(x_points, y_points, z_points)
    # Un-flattening xm, ym and zm by shape (x_steps, y_steps, z_steps) returns them to the matrix form.
    xm, ym, zm = np.meshgrid(x_points, y_points, z_points, indexing='ij')
    data = np.vstack([xm.flatten(), ym.flatten(), zm.flatten(), np.zeros([6, len(xm.flatten())])]).T
    df = pd.DataFrame(data, columns=['x', 'y', 'z', 'mag_x', 'mag_y', 'mag_z', 'temp_x', 'temp_y', 'temp_z'])
    # Motor movement order sorting: y-axis should move the most and z the least.
    df.sort_values([*order], inplace=True)
    for i in df.index:
        x, y, z = df.loc[i, ['x', 'y', 'z']]
        motor.multi_absolute_move([x, y, z])
        df.loc[i, ['mag_x', 'mag_y', 'mag_z', 'temp_x', 'temp_y', 'temp_z']] = mag.read_n_times(n_reps)
    df.sort_index(inplace=True)
    df.attrs['lengths'] = [len(x_points), len(y_points), len(z_points)]
    df.attrs['step_sizes'] = [get_step_size(x_points), get_step_size(y_points), get_step_size(z_points)]
    return df
