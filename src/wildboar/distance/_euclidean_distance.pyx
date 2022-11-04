# cython: cdivision=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: language_level=3

# Authors: Isak Samsten
# License: BSD 3 clause

import numpy as np

cimport numpy as np
from libc.math cimport INFINITY, sqrt
from libc.stdlib cimport free, malloc

from ..utils.data cimport Dataset
from ..utils.misc cimport realloc_array
from ..utils.stats cimport IncStats, inc_stats_add, inc_stats_init, inc_stats_variance
from ._distance cimport (
    DistanceMeasure,
    ScaledSubsequenceDistanceMeasure,
    Subsequence,
    SubsequenceDistanceMeasure,
    SubsequenceView,
)


cdef class EuclideanSubsequenceDistanceMeasure(SubsequenceDistanceMeasure):

    cdef double transient_distance(
        self,
        SubsequenceView *s,
        Dataset dataset,
        Py_ssize_t index,
        Py_ssize_t *return_index=NULL,
    ) nogil:
        return euclidean_distance(
            dataset.get_sample(s.index, s.dim) + s.start,
            s.length,
            dataset.get_sample(index, s.dim),
            dataset.n_timestep,
            return_index,
        )

    cdef double persistent_distance(
        self,
        Subsequence *s,
        Dataset dataset,
        Py_ssize_t index,
        Py_ssize_t *return_index=NULL,
    ) nogil:
        return euclidean_distance(
            s.data,
            s.length,
            dataset.get_sample(index, s.dim),
            dataset.n_timestep,
            return_index,
        )

    cdef Py_ssize_t transient_matches(
        self,
        SubsequenceView *v,
        Dataset dataset,
        Py_ssize_t index,
        double threshold,
        double **distances,
        Py_ssize_t **indicies,
    ) nogil:
       return euclidean_distance_matches(
            dataset.get_sample(v.index, v.dim) + v.start,
            v.length,
            dataset.get_sample(index, v.dim),
            dataset.n_timestep,
            threshold,
            distances,
            indicies,
        )

    cdef Py_ssize_t persistent_matches(
        self,
        Subsequence *s,
        Dataset dataset,
        Py_ssize_t index,
        double threshold,
        double **distances,
        Py_ssize_t **indicies,
    ) nogil:
        return euclidean_distance_matches(
            s.data,
            s.length,
            dataset.get_sample(index, s.dim),
            dataset.n_timestep,
            threshold,
            distances,
            indicies,
        )


cdef class ScaledEuclideanSubsequenceDistanceMeasure(ScaledSubsequenceDistanceMeasure):
    cdef double *X_buffer

    def __cinit__(self):
        self.X_buffer = NULL
    
    def __dealloc__(self):
        if self.X_buffer != NULL:
            free(self.X_buffer)
            self.X_buffer = NULL

    def __reduce__(self):
        return self.__class__, ()
    
    cdef int reset(self, Dataset dataset) nogil:
        if self.X_buffer != NULL:
            free(self.X_buffer)        
        self.X_buffer = <double*> malloc(sizeof(double) * dataset.n_timestep * 2)
        if self.X_buffer == NULL:
            return -1
        return 0

    cdef double transient_distance(
        self,
        SubsequenceView *s,
        Dataset dataset,
        Py_ssize_t index,
        Py_ssize_t *return_index=NULL,
    ) nogil:
        return scaled_euclidean_distance(
            dataset.get_sample(s.index, s.dim) + s.start,
            s.length,
            s.mean,
            s.std if s.std != 0.0 else 1.0,
            dataset.get_sample(index, s.dim),
            dataset.n_timestep,
            self.X_buffer,
            return_index,
        )

    cdef double persistent_distance(
        self,
        Subsequence *s,
        Dataset dataset,
        Py_ssize_t index,
        Py_ssize_t *return_index=NULL,
    ) nogil:
        return scaled_euclidean_distance(
            s.data,
            s.length,
            s.mean,
            s.std if s.std != 0.0 else 1.0,
            dataset.get_sample(index, s.dim),
            dataset.n_timestep,
            self.X_buffer,
            return_index,
        )

    cdef Py_ssize_t transient_matches(
        self,
        SubsequenceView *v,
        Dataset dataset,
        Py_ssize_t index,
        double threshold,
        double **distances,
        Py_ssize_t **indicies,
    ) nogil:
        return scaled_euclidean_distance_matches(
            dataset.get_sample(v.index, v.dim) + v.start,
            v.length,
            v.mean,
            v.std if v.std != 0.0 else 1.0,
            dataset.get_sample(index, v.dim),
            dataset.n_timestep,
            self.X_buffer,
            threshold,
            distances,
            indicies,
        )

    cdef Py_ssize_t persistent_matches(
        self,
        Subsequence *s,
        Dataset dataset,
        Py_ssize_t index,
        double threshold,
        double **distances,
        Py_ssize_t **indicies,
    ) nogil:
        return scaled_euclidean_distance_matches(
            s.data,
            s.length,
            s.mean,
            s.std if s.std != 0.0 else 1.0,
            dataset.get_sample(index, s.dim),
            dataset.n_timestep,
            self.X_buffer,
            threshold,
            distances,
            indicies,
        )


cdef class EuclideanDistanceMeasure(DistanceMeasure):

    cdef double distance(
        self,
        Dataset x,
        Py_ssize_t x_index,
        Dataset y,
        Py_ssize_t y_index,
        Py_ssize_t dim,
    ) nogil:
        return self._distance(
            x.get_sample(x_index, dim=dim),
            x.n_timestep,
            y.get_sample(y_index, dim=dim),
            y.n_timestep,
        )

    cdef double _distance(
        self,
        double *x,
        Py_ssize_t x_len,
        double *y,
        Py_ssize_t y_len
    ) nogil:
        return euclidean_distance(x, x_len, y, y_len, NULL)


cdef class NormalizedEuclideanDistanceMeasure(EuclideanDistanceMeasure):


    cdef double _distance(
        self,
        double *x,
        Py_ssize_t x_len,
        double *y,
        Py_ssize_t y_len
    ) nogil:
        return normalized_euclidean_distance(x, x_len, y, y_len, NULL)


cdef double scaled_euclidean_distance(
    double *S,
    Py_ssize_t s_length,
    double s_mean,
    double s_std,
    double *T,
    Py_ssize_t t_length,
    double *X_buffer,
    Py_ssize_t *index,
) nogil:
    cdef double current_value = 0
    cdef double mean = 0
    cdef double std = 0
    cdef double dist = 0
    cdef double min_dist = INFINITY

    cdef double ex = 0
    cdef double ex2 = 0
    cdef double tmp

    cdef Py_ssize_t i
    cdef Py_ssize_t j
    cdef Py_ssize_t buffer_pos

    for i in range(t_length):
        current_value = T[i]
        ex += current_value
        ex2 += current_value * current_value

        buffer_pos = i % s_length
        X_buffer[buffer_pos] = current_value
        X_buffer[buffer_pos + s_length] = current_value
        if i >= s_length - 1:
            j = (i + 1) % s_length
            mean = ex / s_length
            tmp = ex2 / s_length - mean * mean
            if tmp > 0:
                std = sqrt(tmp)
            else:
                std = 1.0
            dist = inner_scaled_euclidean_distance(
                s_length, 
                s_mean, 
                s_std,
                j, 
                mean,
                std, 
                S, 
                X_buffer, 
                min_dist,
            )

            if dist < min_dist:
                min_dist = dist
                if index != NULL:
                    index[0] = (i + 1) - s_length

            current_value = X_buffer[j]
            ex -= current_value
            ex2 -= current_value * current_value

    return sqrt(min_dist)


cdef double inner_scaled_euclidean_distance(
    Py_ssize_t length,
    double s_mean,
    double s_std,
    Py_ssize_t j,
    double mean,
    double std,
    double *X,
    double *X_buffer,
    double min_dist,
) nogil:
    # Compute the distance between the shapelet (starting at `offset`
    # and ending at `offset + length` normalized with `s_mean` and
    # `s_std` with the shapelet in `X_buffer` starting at `0` and
    # ending at `length` normalized with `mean` and `std`
    cdef double dist = 0
    cdef double x
    cdef Py_ssize_t i

    for i in range(length):
        if dist >= min_dist:
            break
        x = (X[i] - s_mean) / s_std
        x -= (X_buffer[i + j] - mean) / std
        dist += x * x

    return dist


cdef double euclidean_distance(
    double *S,
    Py_ssize_t s_length,
    double *T,
    Py_ssize_t t_length,
    Py_ssize_t *index,
) nogil:
    cdef double dist = 0
    cdef double min_dist = INFINITY

    cdef Py_ssize_t i
    cdef Py_ssize_t j
    cdef double x
    for i in range(t_length - s_length + 1):
        dist = 0
        for j in range(s_length):
            if dist >= min_dist:
                break

            x = T[i + j]
            x -= S[j]
            dist += x * x

        if dist < min_dist:
            min_dist = dist
            if index != NULL:
                index[0] = i

    return sqrt(min_dist)

# PTDS (https://stats.stackexchange.com/users/68112/ptds), 
#   Definition of normalized Euclidean distance, URL (version: 2021-09-27): 
#   https://stats.stackexchange.com/q/498753
cdef double normalized_euclidean_distance(
    double *S,
    Py_ssize_t s_length,
    double *T,
    Py_ssize_t t_length,
    Py_ssize_t *index,
) nogil:
    cdef IncStats S_stats, T_stats, ST_stats
    cdef double s, t, dist
    cdef double min_dist = INFINITY
    cdef Py_ssize_t i, j
    for i in range(t_length - s_length + 1):
        dist = 0
        inc_stats_init(&S_stats)
        inc_stats_init(&T_stats)
        inc_stats_init(&ST_stats)
        for j in range(s_length):
            if dist >= min_dist:
                break

            t = T[i + j]
            s = S[j]
            inc_stats_add(&S_stats, 1.0, s)
            inc_stats_add(&T_stats, 1.0, t)
            inc_stats_add(&ST_stats, 1.0, s - t)
            dist = inc_stats_variance(&S_stats) + inc_stats_variance(&T_stats) + 1e-8
            dist = inc_stats_variance(&ST_stats) / dist

        if dist < min_dist:
            min_dist = dist
            if index != NULL:
                index[0] = i

    return sqrt(0.5 * min_dist)


cdef Py_ssize_t euclidean_distance_matches(
    double *S,
    Py_ssize_t s_length,
    double *T,
    Py_ssize_t t_length,
    double threshold,
    double **distances,
    Py_ssize_t **matches,
) nogil except -1:
    cdef double dist = 0
    cdef Py_ssize_t capacity = 1
    cdef Py_ssize_t tmp_capacity
    cdef Py_ssize_t i
    cdef Py_ssize_t j
    cdef double x
    cdef Py_ssize_t n_matches = 0

    matches[0] = <Py_ssize_t*> malloc(sizeof(Py_ssize_t) * capacity)
    distances[0] = <double*> malloc(sizeof(double) * capacity)

    threshold = threshold * threshold
    for i in range(t_length - s_length + 1):
        dist = 0
        for j in range(s_length):
            if dist > threshold:
                break

            x = T[i + j]
            x -= S[j]
            dist += x * x
        if dist <= threshold:
            tmp_capacity = capacity
            realloc_array(<void**> matches, n_matches, sizeof(Py_ssize_t), &tmp_capacity)
            realloc_array(<void**> distances, n_matches, sizeof(double), &capacity)
            matches[0][n_matches] = i
            distances[0][n_matches] = sqrt(dist)
            n_matches += 1

    return n_matches


cdef Py_ssize_t scaled_euclidean_distance_matches(
   double *S,
   Py_ssize_t s_length,
   double s_mean,
   double s_std,
   double *T,
   Py_ssize_t t_length,
   double *X_buffer,
   double threshold,
   double** distances,
   Py_ssize_t** matches,
) nogil:
    cdef double current_value = 0
    cdef double mean = 0
    cdef double std = 0
    cdef double dist = 0

    cdef double ex = 0
    cdef double ex2 = 0
    cdef double tmp

    cdef Py_ssize_t i
    cdef Py_ssize_t j
    cdef Py_ssize_t buffer_pos
    cdef Py_ssize_t capacity = 1
    cdef Py_ssize_t tmp_capacity
    cdef Py_ssize_t n_matches = 0

    matches[0] = <Py_ssize_t*> malloc(sizeof(Py_ssize_t) * capacity)
    distances[0] = <double*> malloc(sizeof(double) * capacity)
    n_matches = 0

    threshold = threshold * threshold

    for i in range(t_length):
        current_value = T[i]
        ex += current_value
        ex2 += current_value * current_value

        buffer_pos = i % s_length
        X_buffer[buffer_pos] = current_value
        X_buffer[buffer_pos + s_length] = current_value
        if i >= s_length - 1:
            j = (i + 1) % s_length
            mean = ex / s_length
            tmp = ex2 / s_length - mean * mean
            if tmp > 0:
                std = sqrt(tmp)
            else:
                std = 1.0
            dist = inner_scaled_euclidean_distance(
                s_length,
                s_mean, 
                s_std, 
                j, 
                mean, 
                std, 
                S, 
                X_buffer,
                threshold,
            )

            if dist <= threshold:
                tmp_capacity = capacity
                realloc_array(
                    <void**> matches, n_matches, sizeof(Py_ssize_t), &tmp_capacity)
                realloc_array(
                    <void**> distances, n_matches, sizeof(double), &capacity)

                matches[0][n_matches] = (i + 1) - s_length
                distances[0][n_matches] = sqrt(dist)

                n_matches += 1

            current_value = X_buffer[j]
            ex -= current_value
            ex2 -= current_value * current_value

    return n_matches
