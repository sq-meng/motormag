import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import griddata


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


def join_dataframes(dataframes):
    pass


def calculate_mag_field_amplitude(data, axes='xyz'):
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


def mag_field_gradient(data, field_axes='xyz', directions='xyz'):
    """
    Calculates field gradients along specified axes.
    :param data: input dataframe
    :param field_axes: Which magnetic field components to calculate.
    :param directions: Which spatial directions to include, throws error if provided with size-1 array.
    :return: dict with structure d['bx']['y'] for dBx/dy etc.
    """
    coords, mags = dataframe_to_matrices(data)
    results = {}
    for field_axis in field_axes:
        results['b'+field_axis] = {}
        step_size = data.attrs['step_sizes']['xyz'.index(field_axis)]
        for direction in directions:
            axis = 'xyz'.index(direction)
            try:
                results['b'+field_axis][direction] = np.gradient(mags[field_axis], step_size, axis=axis)
            except ValueError:
                raise ValueError('Gradient cannot be computed along axis %s' % direction)
    return results


def field_gradient_squared(data, field_axes='xy', directions='xyz'):
    gradients = mag_field_gradient(data, field_axes, directions)
    components = []
    for field_axis in field_axes:
        for direction in directions:
            components.append(gradients['b'+field_axis][direction] ** 2)
    return sum(components)


def relative_field_gradient_squared(data, field_axes='xy', directions='xyz', b_zero=None, center_position=None):
    if center_position is None:
        center_position = np.asarray(((data.max() + data.min()) / 2).loc[['x', 'y', 'z']])
    if b_zero is None:
        b_zero_components = griddata(data.loc[:, ['x', 'y', 'z']], data.loc[:, ['mag_x', 'mag_y', 'mag_z']], center_position)
        b_zero_components = b_zero_components[0]
        b_zero_squared = b_zero_components[0] ** 2 + b_zero_components[1] ** 2 + b_zero_components[2] ** 2
    else:
        b_zero_squared = b_zero ** 2
    absolute_gradient_squared = field_gradient_squared(data, field_axes, directions)
    relative_gradient_squared = absolute_gradient_squared / b_zero_squared
    return relative_gradient_squared


def slice_2d_scalar(coordinates, values, cut_axis, cut_index=None, cut_position=None):
    cut_index, cut_position = determine_2d_cut_index(coordinates, cut_axis, cut_index, cut_position)
    draw_plane = [ax for ax in 'xyz' if ax != cut_axis]
    slicer = tuple([slice(None) if ax != cut_axis else cut_index for ax in 'xyz'])
    horizontal_matrix = coordinates[draw_plane[0]][slicer]
    vertical_matrix = coordinates[draw_plane[1]][slicer]
    values_matrix = values[slicer]
    return horizontal_matrix, vertical_matrix, values_matrix


def slice_1d_scalar(positions, values, axis, ):
    pass


def determine_2d_cut_index(coordinates, cut_axis, cut_index, cut_position):
    positions_slicer = tuple([slice(0, 1, 1) if ax != cut_axis else slice(None) for ax in 'xyz'])
    values = coordinates[cut_axis][positions_slicer].flatten()
    if cut_index is not None:
        return cut_index, values[cut_index]
    elif cut_index is None and cut_position is None:
        return 0, values[0]
    else:
        truth = np.isclose(values, cut_position)
        for i, t in enumerate(truth):
            if t:
                return i, values[i]
        raise ValueError("Requested cut plane position not in scanned data")


def determine_2d_cut_axis(data_frame):
    fixed_axes = determine_fixed_axes(data_frame)
    if len(fixed_axes) == 1:
        return fixed_axes[0]
    elif len(fixed_axes) == 0:
        raise ValueError('Failed to resolve cut axis automatically: all 3 axes changed.')
    elif len(fixed_axes) == 2:
        raise ValueError('2-D data required to plot 2-D plot, got 1-D data.')
    else:
        raise ValueError('Somehow got 3 or more fixed axes...')


def plot_strength_2d(data_frame, cut_axis=None, cut_index=None, cut_position=None, field_axis='xyz',
                     vmin=None, vmax=None, ax=None):
    if cut_axis is None:
        cut_axis = determine_2d_cut_axis(data_frame)
    coordinates, values = calculate_mag_field_amplitude(data_frame, axes=field_axis)
    horizontal_matrix, vertical_matrix, values_matrix = slice_2d_scalar(coordinates, values, cut_axis, cut_index, cut_position)
    cut_index, cut_position = determine_2d_cut_index(coordinates, cut_axis, cut_index, cut_position)
    f, ax, pcm = plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin, vmax, ax)
    ax.set_title('Field: %s, cut position: %s=%.1f(i=%d)' % (field_axis, cut_axis, cut_position, cut_index))

    return f, ax, pcm


def plot_relative_gradient_2d(data_frame, cut_axis=None, cut_index=None, cut_position=None, field_axes='xy',
                              spatial_axes='xyz', b_zero=None, center_position=None, vmin=None, vmax=None, ax=None):
    if cut_axis is None:
        cut_axis = determine_2d_cut_axis(data_frame)
    coordinates, _ = dataframe_to_matrices(data_frame)
    values = np.sqrt(relative_field_gradient_squared(data_frame, field_axes, directions=spatial_axes,
                                                     b_zero=b_zero, center_position=center_position))
    horizontal_matrix, vertical_matrix, values_matrix = slice_2d_scalar(coordinates, values, cut_axis, cut_index,
                                                                        cut_position)
    cut_index, cut_position = determine_2d_cut_index(coordinates, cut_axis, cut_index, cut_position)
    f, ax, pcm = plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin, vmax, ax)
    ax.set_title('B components: %s, cut position: %s=%.1f(i=%d)' % (field_axes, cut_axis, cut_position, cut_index))
    return f, ax, pcm


# noinspection PyTypeChecker
def determine_fixed_axes(data_frame):
    fixed = [all(data_frame.loc[:, 'x'] == data_frame.loc[0, 'x']),
            all(data_frame.loc[:, 'y'] == data_frame.loc[0, 'y']),
            all(data_frame.loc[:, 'z'] == data_frame.loc[0, 'z'])]
    return [ax for (ax, t) in zip('xyz', fixed) if t]


def plot_scalar_matrix(horizontal_matrix, vertical_matrix, values_matrix, vmin=None, vmax=None, ax=None):
    if ax is None:
        f, ax = plt.subplots(1)
    else:
        f = ax.figure
    ax.axis('equal')
    pcm = ax.pcolormesh(horizontal_matrix, vertical_matrix, values_matrix, shading='auto', vmin=vmin, vmax=vmax)
    f.colorbar(pcm, ax=ax)
    return f, ax, pcm


def sub(field: pd.DataFrame, background: pd.DataFrame):
    """
    Subtract background from field. Interpolates if coordinates do not match perfectly.
    :param field: Measured magnetic field.
    :param background: Background field with current source turned off.
    :return: Field with background removed.
    """
    if all(field.x == background.x) and all(field.y == background.y) and all(field.z == background.z):
        field = field.copy()
        field.loc[:, ['mag_x', 'mag_y', 'mag_z']] = field.loc[:, ['mag_x', 'mag_y', 'mag_z']] - \
                                                    background.loc[:, ['mag_x', 'mag_y', 'mag_z']]
        return field
    else:
        field = field.copy()
        bg_interp = field.copy()
        bg_interp.loc[:, ['mag_x', 'mag_y', 'mag_z']] = griddata(background.loc[:, ['x', 'y', 'z']],
                                                                 background.loc[:, ['mag_x', 'mag_y', 'mag_z']],
                                                                 bg_interp.loc[:, ['x', 'y', 'z']])
        field.loc[:, ['mag_x', 'mag_y', 'mag_z']] = field.loc[:, ['mag_x', 'mag_y', 'mag_z']] - \
                                                   bg_interp.loc[:, ['mag_x', 'mag_y', 'mag_z']]
        return field

