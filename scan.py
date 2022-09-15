import motor
import mag
import numpy as np
import pandas as pd

def range_to_points(range_def, steps=None, step_size=None):
    if steps is None and step_size is None:
        raise ValueError("Either number steps or step size needs to be given")
    try:
        start = range_def[0]
        end = range_def[1]
    except TypeError:
        return np.array([range_def])
    if steps is not None:
        return np.linspace(start, end, steps)
    else:
        if abs(end - start) % step_size > 0.1:
            raise ValueError("Span of scan is not a multiple of step size")
        return np.linspace(start, end, int(abs(end - start) / step_size) + 1)


def box_scan(x_range, y_range, z_range, x_steps=None, y_steps=None, z_steps=None, step_size=5, order='zxy',
             n_reps=3):
    x_points = range_to_points(x_range, x_steps, step_size)
    y_points = range_to_points(y_range, y_steps, step_size)
    z_points = range_to_points(z_range, z_steps, step_size)
    xm, ym, zm = np.meshgrid(x_points, y_points, z_points, indexing='ij')
    data = np.vstack([xm.flatten(), ym.flatten(), zm.flatten(), np.zeros(len(xm.flatten()))]).T
    df = pd.DataFrame(data, columns=['x', 'y', 'z', 'value'])
    df.sort_values([*order], inplace=True)
    