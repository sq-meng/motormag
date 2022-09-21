import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def dataframe_to_matrices(data: pd.DataFrame, lengths=None):
    if lengths is None:
        try:
            lengths = data.attrs['lengths']
        except KeyError:
            raise ValueError('no matrix size data available')
    x, y, z, mag_x, mag_y, mag_z = np.asarray([data.x, data.y, data.z, data.mag_x, data.mag_y, data.mag_z])
    x = x.reshape(*lengths)
    y = y.reshape(*lengths)
    z = z.reshape(*lengths)
    mag_x = mag_x.reshape(*lengths)
    mag_y = mag_y.reshape(*lengths)
    mag_z = mag_z.reshape(*lengths)
    return {'x': x, 'y': y, 'z': z}, {'x': mag_x, 'y': mag_y, 'z': mag_z}


def get_mag_field_amplitude(data, axes='xyz'):
    """
    Returns [positions, 3-d scalar matrix] for magnetic field strength.
    :param data: input DataFrame
    :param axes: output is the vector sum of specified components. 'xyz', 'xy', 'y', etc.
    :return: [positions, value]
    positions is a 3-matrix dict, values is a matrix.
    """
    positions, mags = dataframe_to_matrices(data)
    if len(axes) == 1:
        return [positions, mags[axes]]
    else:
        return [positions, np.sqrt(sum([np.power(mags[ax], 2) for ax in axes]))]


def get_mag_field_relative_gradient(data, ):
    pass


def slice_2d_scalar(positions, values, axis, position=0):
    draw_plane = [ax for ax in 'xyz' if ax != axis]
    slicer = tuple([slice(None) if ax != axis else position for ax in 'xyz'])
    horizontal_matrix = positions[draw_plane[0]][slicer]
    vertical_matrix = positions[draw_plane[1]][slicer]
    values_matrix = values[slicer]
    return horizontal_matrix, vertical_matrix, values_matrix


def slice_1d_scalar():
    pass


def slice_and_show_strength(data_frame, axis, position=0, field_axis='xyz', vmin=None, vmax=None):
    positions, values = get_mag_field_amplitude(data_frame, axes=field_axis)
    horizontal_matrix, vertical_matrix, values_matrix = slice_2d_scalar(positions, values, axis, position)
    f, ax = plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin, vmax)
    return f, ax


def plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin=None, vmax=None):
    f, ax = plt.subplots(1)
    ax.axis('equal')
    pcm = ax.pcolormesh(horizontal_matrix, vertical_matrix, values_matrix, shading='auto', vmin=vmin, vmax=vmax)
    f.colorbar(pcm, ax=ax)
    return f, ax
