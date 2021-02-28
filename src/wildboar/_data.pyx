# cython: language_level=3

# This file is part of wildboar
#
# wildboar is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wildboar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see
# <http://www.gnu.org/licenses/>.
#
# Authors: Isak Samsten
cimport numpy as np

from ._utils import check_array_fast

cdef TSDatabase ts_database_new(np.ndarray data):
    """Construct a new time series database from a ndarray """
    data = check_array_fast(data, allow_nd=True)
    if data.ndim < 2 or data.ndim > 3:
        raise ValueError("ndim {0} < 2 or {0} > 3".format(data.ndim))

    cdef TSDatabase sd
    sd.n_samples = <Py_ssize_t> data.shape[0]
    sd.n_timestep = <Py_ssize_t> data.shape[data.ndim - 1]
    sd.data = <double*> data.data
    sd.sample_stride = <Py_ssize_t> (data.strides[0] / <Py_ssize_t> data.itemsize)
    sd.timestep_stride = <Py_ssize_t> (data.strides[data.ndim - 1] / <Py_ssize_t> data.itemsize)

    if data.ndim == 3:
        sd.n_dims = <Py_ssize_t> data.shape[data.ndim - 2]
        sd.dim_stride = <Py_ssize_t> (data.strides[data.ndim - 2] / <Py_ssize_t> data.itemsize)
    else:
        sd.n_dims = 1
        sd.dim_stride = 0

    return sd