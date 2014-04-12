# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Mapper for spectral clustering.
   Date: 2012.05.29
"""

__docformat__ = 'restructuredtext'

import numpy as np
import scipy.sparse as sp

from mvpa2.base import warning
from mvpa2.base.dochelpers import _str, borrowkwargs, _repr_attrs
from mvpa2.mappers.base import accepts_dataset_as_samples, Mapper
from mvpa2.datasets.base import Dataset
from mvpa2.datasets.miscfx import get_nsamples_per_attr, get_samples_by_attr
from mvpa2.support import copy
from sklearn.cluster import SpectralClustering

class SpectralMapper(Mapper):
    """Mapper to do spectral clustering
    """
    def __init__(self, chunks_attr=None, k=8, mode='arpack', random_state=None, n_init=10, **kwargs):
        """
	parameters
        __________
        chunks_attr : str or None
          If provided, it specifies the name of a samples attribute in the
          training data, unique values of which will be used to identify chunks of
          samples, and to perform individual clustering within them.
        k : int or ndarray
          The number of clusters to form as well as the number of centroids to
          generate. If init initialization string is matrix, or if a ndarray
          is given instead, it is interpreted as initial cluster to use instead
        mode : {None, 'arpack' or 'amg'}
          The eigenvalue decomposition strategy to use. AMG requires pyamg
          to be installed. It can be faster on very large, sparse problems,
          but may also lead to instabilities.
	random_state: int seed, RandomState instance, or None (default)
          A pseudo random number generator used for the initialization
          of the lobpcg eigen vectors decomposition when mode == 'amg'
          and by the K-Means initialization.
        n_init : int
	  Number of iterations of the k-means algrithm to run. Note that this 
	  differs in meaning from the iters parameter to the kmeans function.
        """
        Mapper.__init__(self, **kwargs)

        self.__chunks_attr = chunks_attr
        self.__k = k
        self.__mode = mode
        self.__random_state = random_state
	self.__n_init = n_init



    def __repr__(self, prefixes=[]):
        return super(KMeanMapper, self).__repr__(
            prefixes=prefixes
            + _repr_attrs(self, ['chunks_attr', 'k', 'mode', 'random_state', 'n_init']))


    def __str__(self):
        return _str(self)


    def _forward_dataset(self, ds):
        chunks_attr = self.__chunks_attr
        mds = Dataset([])
        mds.a = ds.a
       # mds.sa =ds.sa
       # mds.fa =ds.fa
        if chunks_attr is None:
	       # global kmeans
            mds.samples = self._spectralcluster(ds.samples).labels_
            print max(mds.samples)
        else:
	       # per chunk kmeans
            for c in ds.sa[chunks_attr].unique:
                slicer = np.where(ds.sa[chunks_attr].value == c)[0]
                mds.samples = ds.samples[0,:]
                mds.samples[slicer] = self._spectralcluster(ds.samples[slicer]).labels_

        return mds


    def _spectralcluster(self, samples):
        if sp.issparse(samples):
           samples = samples.todense()
        print np.shape(samples)
        samples = np.exp(-samples/samples.std())
        return SpectralClustering(k=self.__k, n_init=self.__n_init, mode=self.__mode).fit(samples)
