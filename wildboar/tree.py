# This file is part of wildboar
#
# wildboar is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wildboar is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Authors: Isak Samsten

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.base import ClassifierMixin, RegressorMixin
from sklearn.utils import check_random_state
from sklearn.utils.validation import check_is_fitted, check_array

from ._tree_builder import ClassificationShapeletTreeBuilder
from ._tree_builder import ExtraClassificationShapeletTreeBuilder
from ._tree_builder import ExtraRegressionShapeletTreeBuilder
from ._tree_builder import RegressionShapeletTreeBuilder
# from ._tree_builder import ClassificationShapeletTreePredictor
# from ._tree_builder import RegressionShapeletTreePredictor
# from ._tree_builder import ShapeletTreeTraverser
from .distance import DISTANCE_MEASURE

__all__ = ["ShapeletTreeClassifier",
           "ExtraShapeletTreeClassifier",
           "ShapeletTreeRegressor",
           "ExtraShapeletTreeRegressor"]


class BaseShapeletTree(BaseEstimator):

    def __init__(self, *,
                 max_depth=None,
                 min_samples_split=2,
                 n_shapelets=10,
                 min_shapelet_size=0,
                 max_shapelet_size=1,
                 metric='euclidean',
                 metric_params=None,
                 force_dim=None,
                 random_state=None):
        if min_shapelet_size < 0 or min_shapelet_size > max_shapelet_size:
            raise ValueError(
                "`min_shapelet_size` {0} <= 0 or {0} > {1}".format(
                    min_shapelet_size, max_shapelet_size))
        if max_shapelet_size > 1:
            raise ValueError(
                "`max_shapelet_size` {0} > 1".format(max_shapelet_size))
        self.max_depth = max_depth or 2 ** 31
        self.min_samples_split = min_samples_split
        self.random_state = check_random_state(random_state)
        self.n_shapelets = n_shapelets
        self.min_shapelet_size = min_shapelet_size
        self.max_shapelet_size = max_shapelet_size
        self.metric = metric
        self.metric_params = metric_params
        self.force_dim = force_dim
        self.n_timestep_ = None
        self.n_dims_ = None

    def _make_distance_measure(self):
        metric_params = self.metric_params
        if metric_params is None:
            metric_params = {}
        distance_measure = DISTANCE_MEASURE[self.metric](self.n_timestep_, **metric_params)
        return distance_measure

    def _validate_x_predict(self, x, check_input):
        if x.ndim < 2 or x.ndim > 3:
            raise ValueError("illegal input dimensions X.ndim ({})".format(
                x.ndim))
        if isinstance(self.force_dim, int):
            x = np.reshape(x, [x.shape[0], self.force_dim, -1])
        if x.shape[-1] != self.n_timestep_:
            raise ValueError("illegal input shape ({} != {})".format(
                x.shape[-1], self.n_timestep_))
        if x.ndim > 2 and x.shape[1] != self.n_dims_:
            raise ValueError("illegal input shape ({} != {}".format(
                x.shape[1], self.n_dims_))
        if check_input:
            x = check_array(x, dtype=np.float64, allow_nd=True, order="C")

        if x.dtype != np.float64 or not x.flags.contiguous:
            x = np.ascontiguousarray(x, dtype=np.float64)
        return x

    def decision_path(self, x, check_input=True):
        check_is_fitted(self, ["tree_"])
        return self.tree_.decision_path(x)

    def apply(self, x, check_input=True):
        check_is_fitted(self, ["tree_"])
        x = self._validate_x_predict(x, check_input)
        return self.tree_.apply(x)


class ShapeletTreeRegressor(RegressorMixin, BaseShapeletTree):
    def __init__(self,
                 *,
                 max_depth=None,
                 min_samples_split=2,
                 n_shapelets=10,
                 min_shapelet_size=0,
                 max_shapelet_size=1,
                 metric='euclidean',
                 metric_params=None,
                 force_dim=None,
                 random_state=None):
        """A shapelet decision tree regressor

        :param max_depth: The maximum depth of the tree. If `None` the
           tree is expanded until all leafs are pure or until all
           leafs contain less than `min_samples_split` samples
           (default: None).

        :param min_samples_split: The minimum number of samples to
           split an internal node (default: 2).

        :param n_shapelets: The number of shapelets to sample at each
           node (default: 10).

        :param min_shapelet_size: The minimum length of a sampled
           shapelet expressed as a fraction, computed as
           `min(ceil(X.shape[-1] * min_shapelet_size), 2)` (default:
           0).

        :param max_shapelet_size: The maximum length of a sampled
           shapelet, expressed as a fraction and computed as
           `ceil(X.shape[-1] * max_shapelet_size)`.

        :param metric: Distance metric used to identify the best
           match. (default: `'euclidean'`)

        :param metric_params: Paramters to the distace measure

        :param force_dim: Force the number of dimensions (default:
           None). If `int`, `force_dim` reshapes the input to the
           shape `[n_samples, force_dim, -1]` to support the
           `BaggingClassifier` interface.

        :param random_state: If `int`, `random_state` is the seed used
           by the random number generator; If `RandomState` instance,
           `random_state` is the random number generator; If `None`,
           the random number generator is the `RandomState` instance
           used by `np.random`.
        """
        super(ShapeletTreeRegressor, self).__init__(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            n_shapelets=n_shapelets,
            min_shapelet_size=min_shapelet_size,
            max_shapelet_size=max_shapelet_size,
            metric=metric,
            metric_params=metric_params,
            force_dim=force_dim,
            random_state=random_state)

    def _make_tree_builder(self, x, y, sample_weight):
        random_state = check_random_state(self.random_state)
        max_shapelet_size = int(self.n_timestep_ * self.max_shapelet_size)
        min_shapelet_size = int(self.n_timestep_ * self.min_shapelet_size)
        if min_shapelet_size < 2:
            min_shapelet_size = 2

        max_depth = self.max_depth or 2 ** 31
        distance_measure = self._make_distance_measure()
        return RegressionShapeletTreeBuilder(
            self.n_shapelets,
            min_shapelet_size,
            max_shapelet_size,
            max_depth,
            self.min_samples_split,
            distance_measure,
            x,
            y,
            sample_weight,
            random_state,
        )

    def fit(self, X, y, sample_weight=None, check_input=True):
        """Fit a shapelet tree regressor from the training set (X, y)

        :param X: array-like, shape `[n_samples, n_timesteps]` or
           `[n_samples, n_dimensions, n_timesteps]`. The training time
           series.

        :param y: array-like, `[n_samples]`. Target values are
        floating point values.

        :param sample_weight: If `None`, then samples are equally
            weighted. Splits that would create child nodes with net
            zero or negative weight are ignored while searching for a
            split in each node. Splits are also ignored if they would
            result in any single class carrying a negative weight in
            either child node.

        :param check_input: Allow to bypass several input checking.
            Don't use this parameter unless you know what you do.

        :returns: `self`

        """
        if check_input:
            X = check_array(X, dtype=np.float64, allow_nd=True, order="C")
            y = check_array(y, dtype=np.float64, ensure_2d=False)

        if X.ndim < 2 or X.ndim > 3:
            raise ValueError("illegal input dimensions")

        n_samples = X.shape[0]
        if isinstance(self.force_dim, int):
            X = np.reshape(X, [n_samples, self.force_dim, -1])

        n_timesteps = X.shape[-1]

        if X.ndim > 2:
            n_dims = X.shape[1]
        else:
            n_dims = 1

        if len(y) != n_samples:
            raise ValueError("Number of labels={} does not match "
                             "number of samples={}".format(len(y), n_samples))

        if X.dtype != np.float64 or not X.flags.contiguous:
            X = np.ascontiguousarray(X, dtype=np.float64)

        if y.dtype != np.float64 or not y.flags.contiguous:
            y = np.ascontiguousarray(y, dtype=np.float64)

        self.n_timestep_ = n_timesteps
        self.n_dims_ = n_dims

        tree_builder = self._make_tree_builder(X, y, sample_weight)
        tree_builder.build_tree()
        self.tree_ = tree_builder.tree_
        return self

    def predict(self, x, check_input=True):
        """Predict the regression of the input samples X.

        :param x: array-like, shape `[n_samples, n_timesteps]` or
           `[n_samples, n_dimensions, n_timesteps]`. The input time
           series.

        :param check_input: Allow to bypass several input checking.
            Don't use this parameter unless you know what you do.

        :returns: array of `shape = [n_samples]`.

        """
        check_is_fitted(self, ["tree_"])
        x = self._validate_x_predict(x, check_input)
        return self.tree_.predict(x)


class ExtraShapeletTreeRegressor(ShapeletTreeRegressor):
    def __init__(self,
                 *,
                 max_depth=None,
                 min_samples_split=2,
                 min_shapelet_size=0,
                 max_shapelet_size=1,
                 metric='euclidean',
                 metric_params=None,
                 force_dim=None,
                 random_state=None):
        """A shapelet decision tree regressor

        :param max_depth: The maximum depth of the tree. If `None` the
           tree is expanded until all leaves are pure or until all
           leaves contain less than `min_samples_split` samples
           (default: None).

        :param min_samples_split: The minimum number of samples to
           split an internal node (default: 2).

        :param min_shapelet_size: The minimum length of a sampled
           shapelet expressed as a fraction, computed as
           `min(ceil(X.shape[-1] * min_shapelet_size), 2)` (default:
           0).

        :param max_shapelet_size: The maximum length of a sampled
           shapelet, expressed as a fraction and computed as
           `ceil(X.shape[-1] * max_shapelet_size)`.

        :param metric: Distance metric used to identify the best
           match. (default: `'euclidean'`)

        :param metric_params: Parameters to the distance measure

        :param force_dim: Force the number of dimensions (default:
           None). If `int`, `force_dim` reshapes the input to the
           shape `[n_samples, force_dim, -1]` to support the
           `BaggingClassifier` interface.

        :param random_state: If `int`, `random_state` is the seed used
           by the random number generator; If `RandomState` instance,
           `random_state` is the random number generator; If `None`,
           the random number generator is the `RandomState` instance
           used by `np.random`.
        """
        super(ExtraShapeletTreeRegressor, self).__init__(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            n_shapelets=1,
            min_shapelet_size=min_shapelet_size,
            max_shapelet_size=max_shapelet_size,
            metric=metric,
            metric_params=metric_params,
            force_dim=force_dim,
            random_state=random_state)

    def _make_tree_builder(self, x, y, sample_weight):
        random_state = check_random_state(self.random_state)
        max_shapelet_size = int(self.n_timestep_ * self.max_shapelet_size)
        min_shapelet_size = int(self.n_timestep_ * self.min_shapelet_size)
        if min_shapelet_size < 2:
            min_shapelet_size = 2

        max_depth = self.max_depth or 2 ** 31
        distance_measure = self._make_distance_measure()
        return ExtraRegressionShapeletTreeBuilder(
            self.n_shapelets,
            min_shapelet_size,
            max_shapelet_size,
            max_depth,
            self.min_samples_split,
            distance_measure,
            x,
            y,
            sample_weight,
            random_state)


class ShapeletTreeClassifier(ClassifierMixin, BaseShapeletTree):
    """A shapelet tree classifier."""

    def __init__(self,
                 max_depth=None,
                 min_samples_split=2,
                 n_shapelets=10,
                 min_shapelet_size=0,
                 max_shapelet_size=1,
                 metric='euclidean',
                 metric_params=None,
                 force_dim=None,
                 random_state=None):
        """A shapelet decision tree

        :param max_depth: The maximum depth of the tree. If `None` the
           tree is expanded until all leafs are pure or until all
           leafs contain less than `min_samples_split` samples
           (default: None).

        :param min_samples_split: The minimum number of samples to
           split an internal node (default: 2).

        :param n_shapelets: The number of shapelets to sample at each
           node (default: 10).

        :param min_shapelet_size: The minimum length of a sampled
           shapelet expressed as a fraction, computed as
           `min(ceil(X.shape[-1] * min_shapelet_size), 2)` (default:
           0).

        :param max_shapelet_size: The maximum length of a sampled
           shapelet, expressed as a fraction and computed as
           `ceil(X.shape[-1] * max_shapelet_size)`.

        :param metric: Distance metric used to identify the best
           match. (default: `'euclidean'`)

        :param metric_params: Paramters to the distace measure

        :param force_dim: Force the number of dimensions (default:
           None). If `int`, `force_dim` reshapes the input to the
           shape `[n_samples, force_dim, -1]` to support the
           `BaggingClassifier` interface.

        :param random_state: If `int`, `random_state` is the seed used
           by the random number generator; If `RandomState` instance,
           `random_state` is the random number generator; If `None`,
           the random number generator is the `RandomState` instance
           used by `np.random`.

        """
        super(ShapeletTreeClassifier, self).__init__(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            n_shapelets=n_shapelets,
            min_shapelet_size=min_shapelet_size,
            max_shapelet_size=max_shapelet_size,
            metric=metric,
            metric_params=metric_params,
            force_dim=force_dim,
            random_state=random_state)
        self.n_classes_ = None

    def _make_tree_builder(self, x, y, sample_weight):
        random_state = check_random_state(self.random_state)
        max_shapelet_size = int(self.n_timestep_ * self.max_shapelet_size)
        min_shapelet_size = int(self.n_timestep_ * self.min_shapelet_size)
        if min_shapelet_size < 2:
            min_shapelet_size = 2
        max_depth = self.max_depth or 2 ** 31
        distance_measure = self._make_distance_measure()
        return ClassificationShapeletTreeBuilder(
            self.n_shapelets,
            min_shapelet_size,
            max_shapelet_size,
            max_depth,
            self.min_samples_split,
            distance_measure,
            x,
            y,
            sample_weight,
            random_state,
            self.n_classes_)

    def fit(self, x, y, sample_weight=None, check_input=True):
        """Fit a shapelet tree classifier from the training set (X, y)

        :param x: array-like, shape `[n_samples, n_timesteps]` or
           `[n_samples, n_dimensions, n_timesteps]`. The training time
           series.

        :param y: array-like, shape `[n_samples, n_classes]` or
           `[n_classes]`. Target values (class labels) as integers or
           strings.

        :param sample_weight: If `None`, then samples are equally
            weighted. Splits that would create child nodes with net
            zero or negative weight are ignored while searching for a
            split in each node. Splits are also ignored if they would
            result in any single class carrying a negative weight in
            either child node.

        :param check_input: Allow to bypass several input checking.
            Don't use this parameter unless you know what you do.

        :returns: `self`

        """
        random_state = check_random_state(self.random_state)

        if check_input:
            x = check_array(x, dtype=np.float64, allow_nd=True, order="C")
            y = check_array(y, ensure_2d=False)

        if x.ndim < 2 or x.ndim > 3:
            raise ValueError("illegal input dimensions")

        n_samples = x.shape[0]
        if isinstance(self.force_dim, int):
            x = np.reshape(x, [n_samples, self.force_dim, -1])

        n_timesteps = x.shape[-1]

        if x.ndim > 2:
            n_dims = x.shape[1]
        else:
            n_dims = 1

        if y.ndim == 1:
            self.classes_, y = np.unique(y, return_inverse=True)
        else:
            _, y = np.nonzero(y)
            if len(y) != n_samples:
                raise ValueError("Single label per sample expected.")
            self.classes_ = np.unique(y)

        if len(y) != n_samples:
            raise ValueError("Number of labels={} does not match "
                             "number of samples={}".format(len(y), n_samples))

        if x.dtype != np.float64 or not x.flags.contiguous:
            x = np.ascontiguousarray(x, dtype=np.float64)

        if not y.flags.contiguous:
            y = np.ascontiguousarray(y, dtype=np.intp)

        self.n_classes_ = len(self.classes_)
        self.n_timestep_ = n_timesteps
        self.n_dims_ = n_dims

        tree_builder = self._make_tree_builder(x, y, sample_weight)
        tree_builder.build_tree()
        self.tree_ = tree_builder.tree_
        return self

    def predict(self, X, check_input=True):
        """Predict the class for X

        :param X: array-like, shape `[n_samples, n_timesteps]` or
            `[n_samples, n_dimensions, n_timesteps]`. The input time
            series.

        :param check_input: Allow to bypass several input checking.
            Don't use this parameter unless you know what you do.

        :returns: array of `shape = [n_samples]`. The predicted
            classes

        """
        return self.classes_[np.argmax(
            self.predict_proba(X, check_input=check_input), axis=1)]

    def predict_proba(self, x, check_input=True):
        """Predict class probabilities of the input samples X.  The predicted
        class probability is the fraction of samples of the same class
        in a leaf.

        :param x: array-like, shape `[n_samples, n_timesteps]` or
           `[n_samples, n_dimensions, n_timesteps]`. The input time
           series.

        :param check_input: Allow to bypass several input checking.
            Don't use this parameter unless you know what you do.

        :returns: array of `shape = [n_samples, n_classes]`. The
            class probabilities of the input samples. The order of the
            classes corresponds to that in the attribute `classes_`.
        """
        check_is_fitted(self, ["tree_"])
        x = self._validate_x_predict(x, check_input)
        return self.tree_.predict(x)


class ExtraShapeletTreeClassifier(ShapeletTreeClassifier):
    def __init__(self,
                 max_depth=None,
                 min_samples_split=2,
                 min_shapelet_size=0,
                 max_shapelet_size=1,
                 metric='euclidean',
                 metric_params=None,
                 force_dim=None,
                 random_state=None):
        """A shapelet decision tree

        :param max_depth: The maximum depth of the tree. If `None` the
           tree is expanded until all leafs are pure or until all
           leafs contain less than `min_samples_split` samples
           (default: None).

        :param min_samples_split: The minimum number of samples to
           split an internal node (default: 2).

        :param min_shapelet_size: The minimum length of a sampled
           shapelet expressed as a fraction, computed as
           `min(ceil(X.shape[-1] * min_shapelet_size), 2)` (default:
           0).

        :param max_shapelet_size: The maximum length of a sampled
           shapelet, expressed as a fraction and computed as
           `ceil(X.shape[-1] * max_shapelet_size)`.

        :param metric: Distance metric used to identify the best
           match. (default: `'euclidean'`)

        :param metric_params: Paramters to the distace measure

        :param force_dim: Force the number of dimensions (default:
           None). If `int`, `force_dim` reshapes the input to the
           shape `[n_samples, force_dim, -1]` to support the
           `BaggingClassifier` interface.

        :param random_state: If `int`, `random_state` is the seed used
           by the random number generator; If `RandomState` instance,
           `random_state` is the random number generator; If `None`,
           the random number generator is the `RandomState` instance
           used by `np.random`.

        """
        super(ShapeletTreeClassifier, self).__init__(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            n_shapelets=1,
            min_shapelet_size=min_shapelet_size,
            max_shapelet_size=max_shapelet_size,
            metric=metric,
            metric_params=metric_params,
            force_dim=force_dim,
            random_state=random_state)
        self.n_classes_ = None

    def _make_tree_builder(self, x, y, sample_weight):
        random_state = check_random_state(self.random_state)
        max_shapelet_size = int(self.n_timestep_ * self.max_shapelet_size)
        min_shapelet_size = int(self.n_timestep_ * self.min_shapelet_size)
        if min_shapelet_size < 2:
            min_shapelet_size = 2

        distance_measure = self._make_distance_measure()
        max_depth = self.max_depth or 2 ** 31
        return ExtraClassificationShapeletTreeBuilder(
            1,
            min_shapelet_size,
            max_shapelet_size,
            max_depth,
            self.min_samples_split,
            distance_measure,
            x,
            y,
            sample_weight,
            random_state,
            self.n_classes_)
