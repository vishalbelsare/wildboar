# cython: language_level=3

# Authors: Isak Samsten
# License: BSD 3 clause

cdef class List:
    cdef list py_list
    cdef readonly Py_ssize_t size

    cdef void* get(self, Py_ssize_t i) noexcept nogil


ctypedef fused double_or_int:
    Py_ssize_t
    double

cdef void argsort(double_or_int *values, Py_ssize_t *order, Py_ssize_t length) noexcept nogil

cdef int realloc_array(void** a, Py_ssize_t p, Py_ssize_t size, Py_ssize_t *cap) except -1 nogil

cdef int safe_realloc(void** ptr, Py_ssize_t new_size) except -1 nogil

cdef object to_ndarray_int(Py_ssize_t *arr, Py_ssize_t n)

cdef object to_ndarray_double(double *arr, Py_ssize_t n)
