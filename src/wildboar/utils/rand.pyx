# cython: cdivision=True
# cython: boundscheck=False
# cython: wraparound=False
# cython: language_level=3

# This file is part of wildboar
#
# wildboar is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wildboar is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from libc.math cimport log, sqrt
from libc.stdlib cimport free, malloc


# https://jugit.fz-juelich.de/mlz/ransampl/-/blob/master/lib/ransampl.c
cdef void vose_rand_init(VoseRand *vr, Py_ssize_t n) nogil:
    vr.prob = <double*> malloc(sizeof(double) * n)
    vr.alias = <Py_ssize_t*> malloc(sizeof(Py_ssize_t) * n)
    vr.n = n

cdef void vose_rand_free(VoseRand *vr) nogil:
    free(vr.prob)
    free(vr.alias)

cdef void vose_rand_precompute(VoseRand *vr, double *p) nogil:
    cdef Py_ssize_t n = vr.n
    cdef Py_ssize_t i, a, g
    cdef double *P = <double*> malloc(sizeof(double) * n)
    cdef Py_ssize_t *S = <Py_ssize_t*> malloc(sizeof(Py_ssize_t) * n)
    cdef Py_ssize_t *L = <Py_ssize_t*> malloc(sizeof(Py_ssize_t) * n)

    cdef double s = 0
    for i in range(n):
        s += p[i]

    for i in range(n):
        P[i] = p[i] * n / s

    cdef Py_ssize_t nS = 0
    cdef Py_ssize_t nL = 0
    for i in range(n - 1, -1, -1):
        if P[i] < 1:
            S[nS] = i
            nS += 1
        else:
            L[nL] = i
            nL += 1

    while nS > 0 and nL > 0: 
        nS -= 1
        a = S[nS]
        nL -= 1
        g = L[nL]
        vr.prob[a] = P[a]
        vr.alias[a] = g
        P[g] = P[g] + P[a] - 1
        if P[g] < 1:
            S[nS] = g
            nS += 1
        else:
            L[nL] = g
            nL += 1

    while nL > 0:
        nL -= 1
        vr.prob[L[nL]] = 1

    while nS > 0:
        nS -= 1
        vr.prob[S[nS]] = 1

    free(P)
    free(S)
    free(L)


cdef Py_ssize_t vose_rand_int(VoseRand *vr, size_t *seed) nogil:
    cdef double r1 = rand_uniform(0, 1, seed)
    cdef double r2 = rand_uniform(0, 1, seed)
    cdef Py_ssize_t i = <Py_ssize_t> (vr.n * r1)
    if r2 < vr.prob[i]:
        return i 
    else:
        return vr.alias[i]


from libc.stdio cimport printf


def test(r):
    cdef Py_ssize_t i
    cdef VoseRand vr
    vose_rand_init(&vr, 10)
    cdef double *p = <double*> malloc(sizeof(double) * 10)
    p[0] = 0.5
    for i in range(9):
        p[i + 1] = 0.5 / 9
    for i in range(10):
        printf("p[%d]=%f\n", i, p[i])

    vose_rand_precompute(&vr, p)

    cdef size_t seed = 102
    cdef Py_ssize_t k
    import numpy as np
    arr = np.zeros(r, dtype=np.intp)
    for i in range(r):
        k = vose_rand_int(&vr, &seed)
        if k < 0:
            printf("wtf!!!\n")
        if k > 9:
            printf("wtf2!!!\n")
        #printf("%d=%d\n", i, k)
        arr[i] = k

    return arr


cdef inline size_t rand_r(size_t *seed) nogil:
    """Returns a pesudo-random number based on the seed."""
    seed[0] = seed[0] * 1103515245 + 12345
    return seed[0] % (<size_t> RAND_R_MAX + 1)


cdef size_t rand_int(size_t min_val, size_t max_val, size_t *seed) nogil:
    """Returns a pseudo-random number in the range [`min_val` `max_val`["""
    if min_val == max_val:
        return min_val
    else:
        return min_val + rand_r(seed) % (max_val - min_val)


cdef double rand_uniform(double low, double high, size_t *random_state) nogil:
    """Generate a random double in the range [`low` `high`[."""
    return ((high - low) * <double> rand_r(random_state) / <double> RAND_R_MAX) + low


cdef double rand_normal(double mu, double sigma, size_t *random_state) nogil:
    cdef double x1, x2, w, _y1
    x1 = 2.0 * rand_uniform(0, 1, random_state) - 1.0
    x2 = 2.0 * rand_uniform(0, 1, random_state) - 1.0
    w = x1 * x1 + x2 * x2
    while w >= 1.0:
        x1 = 2.0 * rand_uniform(0, 1, random_state) - 1.0
        x2 = 2.0 * rand_uniform(0, 1, random_state) - 1.0
        w = x1 * x1 + x2 * x2

    w = sqrt((-2.0 * log(w)) / w)
    _y1 = x1 * w
    y2 = x2 * w
    return mu + _y1 * sigma


cdef void shuffle(Py_ssize_t *values, Py_ssize_t length, size_t *seed) nogil:
    cdef Py_ssize_t i, j
    for i in range(length - 1, 0, -1):
        j = rand_int(0, i, seed)
        values[i], values[j] = values[j], values[i]