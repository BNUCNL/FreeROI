# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Mapper for kmeans clustering.
   Date: 2012.04.27
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
from sklearn.cluster import KMeans

class KMeanMapper(Mapper):
    """Mapper to do Kmean clustering
    """
    def __init__(self, chunks_attr=None, k=8, init='k-means++', n_init=10, **kwargs):
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
        init : {k-means++, random, points, matrix}
          Method for initialization, defaults to k-means++:k-means++ :
          selects initial cluster centers for k-mean clustering in a smart way
	  to speed up convergence. See section Notes in k_init for more details.
          random: generate k centroids from a Gaussian with mean and variance 
	  estimated from the data.points: choose k observations (rows) at 
	  random from data for the initial centroids.matrix: interpret the k 
	  parameter as a k by M (or length k array for one-dimensional data) 
	  array of initial centroids.
        n_init : int
	  Number of iterations of the k-means algrithm to run. Note that this 
	  differs in meaning from the iters parameter to the kmeans function.
        """
        Mapper.__init__(self, **kwargs)

        self.__chunks_attr = chunks_attr
        self.__k = k
        self.__init = init
        self.__n_init = n_init


    def __repr__(self, prefixes=[]):
        return super(KMeanMapper, self).__repr__(
            prefixes=prefixes
            + _repr_attrs(self, ['chunks_attr', 'k', 'init', 'n_init']))


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
           mds.samples = self._kmeans(ds.samples).labels_
           print max(mds.samples)
        else:
	       # per chunk kmeans
            for c in ds.sa[chunks_attr].unique:
                slicer = np.where(ds.sa[chunks_attr].value == c)[0]
                mds.samples = ds.samples[0,:]
                mds.samples[slicer] = self._kmeans(ds.samples[slicer]).labels_

        return mds


    def _kmeans(self, samples):
        if sp.issparse(samples):
           samples = samples.todense()
        samples = samples.T
        print np.shape(samples)
        return KMeans(k=self.__k, n_init=self.__n_init, init=self.__init).fit(samples)
