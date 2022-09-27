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

# Authors: Isak Samsten
import pytest
from numpy.testing import assert_almost_equal, assert_equal

from wildboar.datasets import load_dataset
from wildboar.ensemble import ShapeletForestClassifier, ShapeletForestRegressor
from wildboar.utils.estimator_checks import check_estimator


def test_check_estimator():
    check_estimator(
        ShapeletForestClassifier(n_estimators=10),
        ignore=["check_sample_weights_invariance"],
    )
    check_estimator(
        ShapeletForestRegressor(n_estimators=10),
        ignore=["check_sample_weights_invariance"],
    )


@pytest.mark.parametrize(
    "estimator, expected_estimator_params",
    [
        (
            ShapeletForestClassifier(),
            (
                "max_depth",
                "n_shapelets",
                "min_samples_split",
                "min_samples_leaf",
                "min_impurity_decrease",
                "min_shapelet_size",
                "max_shapelet_size",
                "alpha",
                "metric",
                "metric_params",
                "criterion",
            ),
        ),
        (
            ShapeletForestRegressor(),
            (
                "max_depth",
                "n_shapelets",
                "min_samples_split",
                "min_samples_leaf",
                "min_impurity_decrease",
                "min_shapelet_size",
                "max_shapelet_size",
                "alpha",
                "metric",
                "metric_params",
                "criterion",
            ),
        ),
    ],
)
def test_check_estimator_params(estimator, expected_estimator_params):
    assert set(estimator.estimator_params) == set(expected_estimator_params)


def test_shapelet_forest_classifier():
    x_train, x_test, y_train, y_test = load_dataset(
        "GunPoint", repository="wildboar/ucr-tiny", merge_train_test=False
    )
    clf = ShapeletForestClassifier(n_estimators=10, n_shapelets=10, random_state=1)
    clf.fit(x_train, y_train)
    branches = [
        (
            [1, -1, 3, 4, 5, -1, -1, 8, -1, 10, -1, -1, -1],
            [2, -1, 12, 7, 6, -1, -1, 9, -1, 11, -1, -1, -1],
        ),
        (
            [1, -1, 3, 4, -1, 6, -1, 8, -1, 10, -1, -1, -1],
            [2, -1, 12, 5, -1, 7, -1, 9, -1, 11, -1, -1, -1],
        ),
        (
            [1, 2, 3, 4, -1, -1, 7, -1, -1, 10, -1, 12, -1, -1, -1],
            [14, 9, 6, 5, -1, -1, 8, -1, -1, 11, -1, 13, -1, -1, -1],
        ),
        (
            [1, 2, 3, 4, -1, -1, -1, 8, -1, 10, -1, 12, -1, -1, -1],
            [14, 7, 6, 5, -1, -1, -1, 9, -1, 11, -1, 13, -1, -1, -1],
        ),
        (
            [1, 2, 3, -1, 5, -1, 7, -1, 9, -1, 11, -1, -1, -1, 15, -1, 17, -1, -1],
            [14, 13, 4, -1, 6, -1, 8, -1, 10, -1, 12, -1, -1, -1, 16, -1, 18, -1, -1],
        ),
        (
            [1, 2, -1, 4, 5, -1, 7, -1, -1, 10, -1, -1, 13, 14, -1, -1, -1],
            [12, 3, -1, 9, 6, -1, 8, -1, -1, 11, -1, -1, 16, 15, -1, -1, -1],
        ),
        (
            [1, 2, 3, 4, -1, -1, -1, 8, 9, -1, -1, 12, 13, -1, -1, -1, -1],
            [16, 7, 6, 5, -1, -1, -1, 11, 10, -1, -1, 15, 14, -1, -1, -1, -1],
        ),
        (
            [1, 2, -1, 4, 5, 6, 7, -1, -1, -1, -1, 12, -1, -1, -1],
            [14, 3, -1, 11, 10, 9, 8, -1, -1, -1, -1, 13, -1, -1, -1],
        ),
        (
            [1, 2, 3, -1, 5, -1, -1, 8, 9, 10, -1, 12, -1, -1, -1, -1, -1],
            [16, 7, 4, -1, 6, -1, -1, 15, 14, 11, -1, 13, -1, -1, -1, -1, -1],
        ),
        (
            [1, 2, -1, 4, -1, 6, -1, 8, -1, 10, -1, 12, -1, -1, -1],
            [14, 3, -1, 5, -1, 7, -1, 9, -1, 11, -1, 13, -1, -1, -1],
        ),
    ]

    thresholds = [
        (
            [
                3.728410228070656,
                11.127575591141072,
                7.383224794807461,
                7.109350684315213,
                0.9248183559076002,
                6.08675185469423,
            ],
            [
                3.728410228070656,
                11.127575591141072,
                7.383224794807461,
                7.109350684315213,
                0.9248183559076002,
                6.08675185469423,
            ],
        ),
        (
            [
                2.468504005311855,
                7.912505524900922,
                1.0551252327034113,
                0.8574299925766751,
                0.5760307808209804,
                0.009237440363224308,
            ],
            [
                2.468504005311855,
                7.912505524900922,
                1.0551252327034113,
                0.8574299925766751,
                0.5760307808209804,
                0.009237440363224308,
            ],
        ),
        (
            [
                3.909569808800988,
                2.821010442496668,
                1.8694668182965288,
                0.034583372931197384,
                0.8137102058624538,
                0.7560554810866997,
                2.713102595233928,
            ],
            [
                3.909569808800988,
                2.821010442496668,
                1.8694668182965288,
                0.034583372931197384,
                0.8137102058624538,
                0.7560554810866997,
                2.713102595233928,
            ],
        ),
        (
            [
                5.391042553752862,
                4.420547070721347,
                2.2716225008196576,
                0.6679258993537478,
                1.5471177855226528,
                1.2706259403508802,
                6.379381672446367,
            ],
            [
                5.391042553752862,
                4.420547070721347,
                2.2716225008196576,
                0.6679258993537478,
                1.5471177855226528,
                1.2706259403508802,
                6.379381672446367,
            ],
        ),
        (
            [
                2.784221806516613,
                3.9613021926565697,
                0.43050821107331483,
                1.3603965501478146,
                1.9817847740610532,
                0.557171910946499,
                0.023161212907754903,
                3.2040403820972045,
                0.25123702588573155,
            ],
            [
                2.784221806516613,
                3.9613021926565697,
                0.43050821107331483,
                1.3603965501478146,
                1.9817847740610532,
                0.557171910946499,
                0.023161212907754903,
                3.2040403820972045,
                0.25123702588573155,
            ],
        ),
        (
            [
                9.06314095909644,
                0.9301861459984877,
                1.2749535932250209,
                0.6602701901531287,
                0.3105779260645574,
                3.199344210068309,
                1.7444498163002922,
                0.9679068532147111,
            ],
            [
                9.06314095909644,
                0.9301861459984877,
                1.2749535932250209,
                0.6602701901531287,
                0.3105779260645574,
                3.199344210068309,
                1.7444498163002922,
                0.9679068532147111,
            ],
        ),
        (
            [
                10.684770463276237,
                1.0443634502866903,
                2.657944200018761,
                0.31997645008775166,
                8.506009151805937,
                2.5790890876760417,
                2.444351040739898,
                0.8797498982567451,
            ],
            [
                10.684770463276237,
                1.0443634502866903,
                2.657944200018761,
                0.31997645008775166,
                8.506009151805937,
                2.5790890876760417,
                2.444351040739898,
                0.8797498982567451,
            ],
        ),
        (
            [
                8.903669489275785,
                2.558013265746756,
                1.9352062567009694,
                0.6160338380839283,
                1.1133147922166846,
                2.6673841033247827,
                0.6693157414483296,
            ],
            [
                8.903669489275785,
                2.558013265746756,
                1.9352062567009694,
                0.6160338380839283,
                1.1133147922166846,
                2.6673841033247827,
                0.6693157414483296,
            ],
        ),
        (
            [
                2.9771351955856753,
                3.4048368843307957,
                2.847751510400112,
                1.2655496884627422,
                4.410184513977114,
                2.3116642536119203,
                0.5858765536466852,
                0.7586458184224343,
            ],
            [
                2.9771351955856753,
                3.4048368843307957,
                2.847751510400112,
                1.2655496884627422,
                4.410184513977114,
                2.3116642536119203,
                0.5858765536466852,
                0.7586458184224343,
            ],
        ),
        (
            [
                6.260659343273105,
                0.05120063347084325,
                0.678745571123132,
                5.913261089713139,
                0.25431501853894734,
                0.27996560751446015,
                0.7309024510514174,
            ],
            [
                6.260659343273105,
                0.05120063347084325,
                0.678745571123132,
                5.913261089713139,
                0.25431501853894734,
                0.27996560751446015,
                0.7309024510514174,
            ],
        ),
    ]

    for estimator, (left, right), (left_threshold, right_threshold) in zip(
        clf.estimators_, branches, thresholds
    ):
        assert_equal(left, estimator.tree_.left)
        assert_equal(right, estimator.tree_.right)
        assert_almost_equal(
            left_threshold, estimator.tree_.threshold[estimator.tree_.left > 0]
        )
        assert_almost_equal(
            right_threshold, estimator.tree_.threshold[estimator.tree_.right > 0]
        )
