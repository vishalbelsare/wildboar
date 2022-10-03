# Authors: Isak Samsten
# License: BSD 3 clause

import numpy as np
import pytest

from wildboar.utils.validation import check_array


def test_check_array_multivariate():
    x = np.arange(10 * 3 * 10).reshape(10, 3, 10)
    x_checked = check_array(x, allow_3d=True)
    assert x.dtype == x_checked.dtype

    with pytest.raises(ValueError):
        check_array(x, allow_3d=False)


def test_check_array_contiguous():
    x = np.arange(10 * 3 * 10).reshape(10, 3, 10, order="f")
    x_checked = check_array(x, allow_3d=True)
    assert x_checked.flags.carray

    x_checked = check_array(x, allow_3d=True, contiguous=False)
    assert not x_checked.flags.carray
