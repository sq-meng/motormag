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
    Returns [coordinates, 3-d scalar matrix] for magnetic field strength.
    :param data: input DataFrame
    :param axes: output is the vector sum of specified components. 'xyz', 'xy', 'y', etc.
    :return: [coordinates, value]
    coordinates is a 3-matrix dict, values is a matrix.
    """
    coordinates, mags = dataframe_to_matrices(data)
    if len(axes) == 1:
        return [coordinates, mags[axes]]
    else:
        return [coordinates, np.sqrt(sum([np.power(mags[ax], 2) for ax in axes]))]


def get_mag_field_relative_gradient(data, ):
    pass


def resolve_2d_cut_index(positions, cut_axis, cut_position):
    positions_slicer = tuple([slice(0, 1, 1) if ax != cut_axis else slice(None) for ax in 'xyz'])
    values = positions[cut_axis][positions_slicer]
    truth = np.isclose(values.flatten(), cut_position)
    for i, t in enumerate(truth):
        if t:
            return i
    raise ValueError("Requested cut plane position not in scanned data")


def slice_2d_scalar(positions, values, cut_axis, cut_index=None, cut_position=None):
    if cut_index is None and cut_position is None:
        cut_index = 0
    elif cut_index is None and cut_position is not None:
        cut_index = resolve_2d_cut_index(positions, cut_axis, cut_position)
    else:
        pass
    draw_plane = [ax for ax in 'xyz' if ax != cut_axis]
    slicer = tuple([slice(None) if ax != cut_axis else cut_index for ax in 'xyz'])
    horizontal_matrix = positions[draw_plane[0]][slicer]
    vertical_matrix = positions[draw_plane[1]][slicer]
    values_matrix = values[slicer]
    return horizontal_matrix, vertical_matrix, values_matrix


def slice_1d_scalar(positions, values, axis, ):
    pass


def strength_2d(data_frame, axis=None, cut_index=None, cut_position=None, field_axis='xyz', vmin=None, vmax=None):
    if axis is None:
        fixed_axes = get_fixed_axes(data_frame)
        if len(fixed_axes) == 1:
            axis = fixed_axes[0]
        elif len(fixed_axes) == 0:
            raise ValueError('Failed to resolve cut axis automatically: all 3 axes changed.')
        elif len(fixed_axes) == 2:
            raise ValueError('2-D data required to plot 2-D plot, got 1-D data.')

    coordinates, values = get_mag_field_amplitude(data_frame, axes=field_axis)
    horizontal_matrix, vertical_matrix, values_matrix = slice_2d_scalar(coordinates, values, axis, cut_index, cut_position)
    f, ax = plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin, vmax)
    return f, ax


# noinspection PyTypeChecker
def get_fixed_axes(data_frame):
    fixed = [all(data_frame.loc[:, 'x'] == data_frame.loc[0, 'x']),
            all(data_frame.loc[:, 'y'] == data_frame.loc[0, 'y']),
            all(data_frame.loc[:, 'z'] == data_frame.loc[0, 'z'])]
    return [ax for (ax, t) in zip('xyz', fixed) if t]


def plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin=None, vmax=None):
    f, ax = plt.subplots(1)
    ax.axis('equal')
    pcm = ax.pcolormesh(horizontal_matrix, vertical_matrix, values_matrix, shading='auto', vmin=vmin, vmax=vmax)
    f.colorbar(pcm, ax=ax)
    return f, ax
