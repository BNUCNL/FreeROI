# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Mapper for getting spatial distance matrix.
    
    Author: kongxiangzheng@gmail.com
    Date: 2012.05.26
    Editors: [plz add own name after edit here]
"""

__docformat__ = 'restructuredtext'

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import issparse
from mvpa2.mappers.base import Mapper
from mvpa2.datasets.base import Dataset

class SpatialDistanceMapper(Mapper):
    """Mapper to get spatial distance matrix.
    """
    def __init__(self, distmask=None, **kwargs):
        """
	    parameters
        ----------
        distmask :  ndarray-like matrix or sparse matrix, or a dataset.
            The distmask of voxels to present their neighbors. 
            Usually we do not set it.
        """
        Mapper.__init__(self, **kwargs)

        self.__distmask = distmask

    def _forward_dataset(self, ds):
        out_ds = ds.copy(sa=[])
        coords = ds.fa.values()[0]
        
        distmtx = self._getsdistmtx(coords)
        
        if self.__distmask != None:
            if isinstance(self.__distmask, Dataset):
                distmask = self.__distmask.samples
                if sp.issparse(distmask):
                    distmask = distmask.todense()
            elif issparse(self.__distmask):
                distmask = distmask.todense()
            elif isinstance(self.__distmask, np.ndarray):
                distmask = self.__distmask
            else:
                raise RuntimeError('%distmask should be a matrix or a dataset with a matrix.')
            
            distmtx = distmtx*distmask
        
        out_ds.samples = distmtx
        
        return out_ds

    def _getsdistmtx(self, coords):
        sdistmtx_tmp = pdist(coords, 'euclidean')
        sdistmtx = squareform(sdistmtx_tmp)
        return sdistmtx

