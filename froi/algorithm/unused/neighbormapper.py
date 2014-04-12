# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Mapper for getting spatial neighbors of voxels.
   
    Author: 
    Date: 2012.05.26
    Editors: [plz add own name here after edit]
"""

__docformat__ = 'restructuredtext'

import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.sparse import issparse
from mvpa2.mappers.base import Mapper
from mvpa2.datasets.base import Dataset
from neighbor import *
from bpmri import *
import pdb
class NeighborMapper(Mapper):
    """Mapper to get spatial neighbors.
    """
    def __init__(self,neighbor_shape, outsparse=True, **kwargs):
        """
	    Parameters
        ----------
        neighborhood :  .
        outsparse: bool
            whether to output sparse matrix. 
        """
        Mapper.__init__(self, **kwargs)
        
        self.__outsparse = outsparse
        self.__neighbor_shape = neighbor_shape

    def _forward_dataset(self, ds):
        out_ds = Dataset([])
        out_ds.a = ds.a
        pdb.set_trace()
        iv = np.nonzero(ds.samples)[0]
        coords = ds.sa.values()[0][iv]
        out_ds.fa = coords
        dim = ds.a.voxel_dim
        nbdim = self.__neighbor_shape.nbdim
        nbsize = self.__neighbor_shape.nbsize
        shape_type = self.__neighbor_shape.shape_type
        volnb = volneighbors(coords, dim, nbdim, nbsize, shape_type)
        distmsk = volnb.compute_offsets()
                
        if self.__outsparse == True:
            out_ds.samples = distmask
        elif self.__outsparse == False:
            distmask = distmask.todense()
            out_ds.samples = distmask
        else:
            raise RuntimeError('%outsparse should be True or False.')
            
        
        return out_ds 

if __name__ == "__main__":
    pdb.set_trace()
    targnii = 'prob-face-object.nii.gz')
    nb_shape = neighbor_shape(3,26,'fast_cube')
    map1 = NeighborMapper(nb_shape)
    ds = bpfmri_dataset(targnii)   
    nb_mat = map1._forward_dataset(ds)

