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
#
# Authors: Isak Samsten
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils import check_array
from sklearn.pipeline import make_pipeline
from sklearn.utils.validation import check_is_fitted, check_random_state
from sklearn.linear_model import RidgeClassifierCV

from ._base import EmbeddingRidgeClassifierCV, EmbeddingRidgeCV
from ..embed import RocketEmbedding


class RocketClassifier(EmbeddingRidgeClassifierCV):
    def __init__(
        self,
        n_kernels=10000,
        *,
        alphas=(0.1, 1.0, 10.0),
        fit_intercept=True,
        normalize=False,
        scoring=None,
        cv=None,
        class_weight=None,
        random_state=None
    ):
        super().__init__(
            alphas=alphas,
            fit_intercept=fit_intercept,
            normalize=normalize,
            scoring=scoring,
            cv=cv,
            class_weight=class_weight,
            random_state=random_state,
        )
        self.n_kernels = n_kernels

    def _get_embedding(self, random_state):
        return RocketEmbedding(self.n_kernels, random_state=random_state)


class RocketRegressor(EmbeddingRidgeCV):
    def __init__(
        self,
        n_kernels=None,
        *,
        alphas=(0.1, 1.0, 10.0),
        fit_intercept=True,
        normalize=False,
        scoring=None,
        cv=None,
        gcv_mode=None,
        random_state=None
    ):
        super().__init__(
            alphas=alphas,
            fit_intercept=fit_intercept,
            normalize=normalize,
            scoring=scoring,
            cv=cv,
            gcv_mode=gcv_mode,
            random_state=random_state,
        )
        self.n_kernels = n_kernels

    def _get_embedding(self, random_state):
        return RocketEmbedding(self.n_kernels, random_state=random_state)
