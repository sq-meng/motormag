import numpy as np
import pytest
from motormag import scan


def test_range_to_points():
    assert np.all(scan.range_to_points([-10, 10], steps=5) == np.linspace(-10, 10, 5))
    assert np.all(scan.range_to_points(30, steps=5, step_size=3) == np.array([30]))
    assert np.all(scan.range_to_points([20, 50], step_size=2) == np.linspace(20, 50, 16))
    with pytest.raises(ValueError) as e:
        _ = scan.range_to_points([20, 30], step_size=3)
