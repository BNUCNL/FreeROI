# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Mapper for fusing spatial distance matrix to connectivity-based feature matrix.
    
    Author: kongxiangzheng@gmail.com
    Date: 07/23/2012
    Editors: [plz add own name after edit here]

"""

__docformat__ = 'restructuredtext'

import numpy as np
from scipy.sparse import issparse
from mvpa2.mappers.base import Mapper
from mvpa2.datasets.base import Dataset

class FuseConstrainMapper(Mapper):
    """Mapper to add spatial distance matrix to connectivity-based feature matrix.
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

    def forward_dataset(self, cc_ds, dist_ds, con=0.2):
        # cc = cross-correlation
        out_ds = cc_ds.copy(sa=[])
        
        ccmtx = cc_ds.samples
        distmtx = dist_ds.samples
        
        if ccmtx.shape != distmtx.shape:
            return
        
        mergedmtx = self._tomergemtx(ccmtx, distmtx, con)
        
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
        
        out_ds.samples = mergedmtx
        
        return out_ds

    def _tomergemtx(self, ccmtx, distmtx, con):
        """ Ref.
         Rogier B. Mars' Diffusion-Weighted Imaging Tractography-Based Parcellation

        """
        distmtx = distmtx.max() - distmtx
        ccmtx = ccmtx.max() - ccmtx
        
        mindist = distmtx.min()
        maxdist = distmtx.max()
        mincc = ccmtx.min()
        maxcc = ccmtx.max()
        
        distmtx = ((distmtx-mindist)/(maxdist-mindist))*(maxcc-mincc)+mincc
        print 'factor: ', con
        ccmtx = np.sqrt((1-con)*np.dot(ccmtx.T,ccmtx)+con*np.dot(distmtx.T,distmtx))
        return ccmtx

