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
    return x, y, z, mag_x, mag_y, mag_z


def slice_and_show(data, axis, position=0, result=None):
    draw_plane = list('xyz')
    draw_plane.pop(draw_plane.index(axis))
    horizontal_axis = ord(draw_plane[0]) - ord('x')
    vertical_axis = ord(draw_plane[1]) - ord('x')
    slicer = [slice(None), slice(None), slice(None)]
    slicer[ord(axis) - ord('x')] = position
    slicer = tuple(slicer)
    x, y, z, mag_x, mag_y, mag_z = dataframe_to_matrices(data)
    positions = [x, y, z]
    mags = [mag_x, mag_y, mag_z]
    horizontal_matrix = positions[horizontal_axis][slicer]
    vertical_matrix = positions[vertical_axis][slicer]
    print(horizontal_matrix, vertical_matrix)
    f, ax = plt.subplots(1)
    ax.pcolormesh(horizontal_matrix, vertical_matrix, mags[0][slicer], shading='auto')
