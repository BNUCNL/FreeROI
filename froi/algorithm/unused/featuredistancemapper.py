# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Mapper to compute distance matrix
   Date: 2012.05.29
"""

__docformat__ = 'restructuredtext'

import numpy as np
import scipy.sparse as sp

from mvpa2.base import warning
from mvpa2.base.dochelpers import _str, borrowkwargs, _repr_attrs
from mvpa2.mappers.base import accepts_dataset_as_samples, Mapper
from mvpa2.datasets.base import Dataset
from mvpa2.support import copy
from scipy.spatial.distance import pdist, squareform

class FeatureDistanceMapper(Mapper):
    """Mapper to compute distance matrix
    """
    def __init__(self, metric='euclidean', **kwargs):
        """
	parameters
        __________
        metric : string or function
          The distance metric to use. The distance function can be 'braycurtis', 
         'canberra', 'chebyshev', 'cityblock', 'correlation', 'cosine', 'dice', 
         'euclidean', 'hamming', 'jaccard', 'kulsinski', 'mahalanobis', 
         'matching', 'minkowski', 'rogerstanimoto', 'russellrao', 'seuclidean',
         'sokalmichener', 'sokalsneath', 'sqeuclidean', 'yule'.
        """
        Mapper.__init__(self, **kwargs)

        self.__metric = metric


    def __repr__(self, prefixes=[]):
        return super(KMeanMapper, self).__repr__(
            prefixes=prefixes
            + _repr_attrs(self, ['metric']))


    def __str__(self):
        return _str(self)


    def _forward_dataset(self, ds):
        mds = Dataset([])
        mds.a = ds.a
        vectordist = self._fdistance(ds.samples)
        mds.samples = squareform(vectordist, force='no', checks=True)
        return mds


    def _fdistance(self, samples):
        if sp.issparse(samples):
           samples = samples.todense()
        samples = samples.T
        print np.shape(samples)
        return pdist(samples, metric=self.__metric)
