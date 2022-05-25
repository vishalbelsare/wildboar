# cython: boundscheck=False
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
#
# Authors: Isak Samsten

from libc.stdlib cimport free, malloc

from wildboar.distance._distance cimport (
    Subsequence,
    SubsequenceDistanceMeasure,
    SubsequenceView,
)
from wildboar.utils.data cimport Dataset
from wildboar.utils.rand cimport RAND_R_MAX, rand_int

from ._feature cimport Feature, FeatureEngineer


cdef class ShapeletFeatureEngineer(FeatureEngineer):

    cdef Py_ssize_t min_shapelet_size
    cdef Py_ssize_t max_shapelet_size

    cdef readonly SubsequenceDistanceMeasure distance_measure

    def __init__(self, distance_measure, min_shapelet_size, max_shapelet_size):
        self.distance_measure = distance_measure
        self.min_shapelet_size = min_shapelet_size
        self.max_shapelet_size = max_shapelet_size

    cdef Py_ssize_t reset(self, Dataset dataset) nogil:
        self.distance_measure.reset(dataset)
        return 1

    cdef Py_ssize_t free_transient_feature(self, Feature *feature) nogil:
        if feature.feature != NULL:
            self.distance_measure.free_transient(<SubsequenceView*> feature.feature)
            free(feature.feature)

    cdef Py_ssize_t free_persistent_feature(self, Feature *feature) nogil:
        cdef Subsequence *s
        if feature.feature != NULL:
            self.distance_measure.free_persistent(<Subsequence*> feature.feature)
            free(feature.feature)

    cdef Py_ssize_t init_persistent_feature(
        self, 
        Dataset dataset,
        Feature *transient, 
        Feature *persistent
    ) nogil:
        cdef SubsequenceView *v = <SubsequenceView*> transient.feature
        cdef Subsequence *s = <Subsequence*> malloc(sizeof(Subsequence))
        self.distance_measure.init_persistent(dataset, v, s)
        persistent.dim = transient.dim
        persistent.feature = s
        return 1

    cdef double transient_feature_value(
        self,
        Feature *feature,
        Dataset dataset,
        Py_ssize_t sample
    ) nogil:
        return self.distance_measure.transient_distance(
            <SubsequenceView*> feature.feature, dataset, sample
        )

    cdef double persistent_feature_value(
        self,
        Feature *feature,
        Dataset dataset,
        Py_ssize_t sample
    ) nogil:
        return self.distance_measure.persistent_distance(
            <Subsequence*> feature.feature, dataset, sample
        )

    cdef Py_ssize_t transient_feature_fill(
        self, 
        Feature *feature, 
        Dataset dataset, 
        Py_ssize_t sample,
        Dataset td_out,
        Py_ssize_t out_sample,
        Py_ssize_t feature_id,
    ) nogil:
        cdef Py_ssize_t offset = td_out.sample_stride * out_sample + feature_id
        td_out.data[offset] = self.distance_measure.transient_distance(
            <SubsequenceView*> feature.feature, dataset, sample
        )
        return 0

    cdef Py_ssize_t persistent_feature_fill(
        self, 
        Feature *feature, 
        Dataset dataset, 
        Py_ssize_t sample,
        Dataset td_out,
        Py_ssize_t out_sample,
        Py_ssize_t feature_id,
    ) nogil:
        cdef Py_ssize_t offset = td_out.sample_stride * out_sample + feature_id
        td_out.data[offset] = self.distance_measure.persistent_distance(
            <Subsequence*> feature.feature, dataset, sample
        )
        return 0

    cdef object persistent_feature_to_object(self, Feature *feature):
        return feature.dim, self.distance_measure.to_array(<Subsequence*>feature.feature)

    cdef Py_ssize_t persistent_feature_from_object(self, object object, Feature *feature):
        cdef Subsequence *s = <Subsequence*> malloc(sizeof(Subsequence))
        dim, obj = object
        self.distance_measure.from_array(s, obj)
        feature.dim = dim
        feature.feature = s
        return 0

cdef class RandomShapeletFeatureEngineer(ShapeletFeatureEngineer):

    cdef Py_ssize_t n_shapelets

    def __init__(
        self, distance_measure, min_shapelet_size, max_shapelet_size, n_shapelets
    ):
        super().__init__(distance_measure, min_shapelet_size, max_shapelet_size)
        self.n_shapelets = n_shapelets

    cdef Py_ssize_t get_n_features(self, Dataset dataset) nogil:
        return self.n_shapelets

    cdef Py_ssize_t next_feature(
        self,
        Py_ssize_t feature_id,
        Dataset dataset, 
        Py_ssize_t *samples, 
        Py_ssize_t n_samples,
        Feature *transient,
        size_t *random_seed
    ) nogil:
        if feature_id >= self.n_shapelets:
            return -1
        
        cdef Py_ssize_t shapelet_length
        cdef Py_ssize_t shapelet_start
        cdef Py_ssize_t shapelet_index
        cdef Py_ssize_t shapelet_dim
        cdef SubsequenceView *v = <SubsequenceView*> malloc(sizeof(SubsequenceView))

        shapelet_length = rand_int(
            self.min_shapelet_size, self.max_shapelet_size, random_seed)
        shapelet_start = rand_int(
            0, dataset.n_timestep - shapelet_length, random_seed)
        shapelet_index = samples[rand_int(0, n_samples, random_seed)]
        if dataset.n_dims > 1:
            shapelet_dim = rand_int(0, dataset.n_dims, random_seed)
        else:
            shapelet_dim = 0

        transient.dim = shapelet_dim
        self.distance_measure.init_transient(
            dataset,
            v,
            shapelet_index,
            shapelet_start,
            shapelet_length,
            shapelet_dim,
        )
        transient.feature = v
        return 1


    