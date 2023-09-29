import numbers

from sklearn.utils._param_validation import Interval, StrOptions

from ._base import BaseFeatureEngineerTransform
from ._chydra import HydraFeatureEngineer, NormalKernelSampler

_SAMPLING_METHOD = {
    "normal": NormalKernelSampler,
}


class HydraMixin:
    _parameter_constraints: dict = {
        "n_kernels": [Interval(numbers.Integral, 1, None, closed="left")],
        "kernel_size": [Interval(numbers.Integral, 2, None, closed="left")],
        "n_groups": [Interval(numbers.Integral, 1, None, closed="left")],
        "sampling": [StrOptions({"normal"})],
        "sampling_params": [dict, None],
    }

    def _get_feature_engineer(self, n_samples):
        sampling_params = {} if self.sampling_params is None else self.sampling_params
        return HydraFeatureEngineer(
            self.n_groups,
            self.n_kernels,
            self.kernel_size,
            _SAMPLING_METHOD[self.sampling](**sampling_params),
        )


class HydraTransform(HydraMixin, BaseFeatureEngineerTransform):
    """
    A Dictionary based method using convolutional kernels.

    Parameters
    ----------
    n_groups : int, optional
        The number of groups of kernels.
    n_kernels : int, optional
        The number of kernels per group.
    kernel_size : int, optional
        The size of the kernel.
    sampling : {"normal"}, optional
        The strategy for sampling kernels. By default kernel weights
        are sampled from a normal distribution with zero mean and unit
        standard deviation.
    sampling_params : dict, optional
        Parameters to the sampling approach. The "normal" sampler
        accepts two parameters: `mean` and `scale`.
    n_jobs : int, optional
        The number of jobs to run in parallel. A value of `None` means using
        a single core and a value of `-1` means using all cores. Positive
        integers mean the exact number of cores.
    random_state : int or RandomState, optional
        Controls the random resampling of the original dataset.

        - If `int`, `random_state` is the seed used by the random number
          generator.
        - If :class:`numpy.random.RandomState` instance, `random_state` is
          the random number generator.
        - If `None`, the random number generator is the
          :class:`numpy.random.RandomState` instance used by
          :func:`numpy.random`.

    Attributes
    ----------
    embedding_ : Embedding
        The underlying embedding

    Notes
    -----
    The implementation is almost feature complete in relation to the algorithm
    described by Dempster et. al. (2023) with the execption of applying the
    convulution of half of the groups to the first order differences.

    References
    ----------
    Dempster, A., Schmidt, D. F., & Webb, G. I. (2023).
        Hydra: competing convolutional kernels for fast and accurate
        time series classification. Data Mining and Knowledge Discovery
    """

    _parameter_constraints: dict = {
        **HydraMixin._parameter_constraints,
        **BaseFeatureEngineerTransform._parameter_constraints,
    }

    def __init__(
        self,
        *,
        n_groups=64,
        n_kernels=8,
        kernel_size=9,
        sampling="normal",
        sampling_params=None,
        n_jobs=None,
        random_state=None,
    ):
        super().__init__(n_jobs=n_jobs, random_state=random_state)
        self.n_groups = n_groups
        self.n_kernels = n_kernels
        self.kernel_size = kernel_size
        self.sampling = sampling
        self.sampling_params = sampling_params
