# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""ROI generation algorithms.
    
"""

import scipy
import numpy as np
from math import pi
import nibabel as nib
import scipy.ndimage as ndimagei
from scipy import sparse
conn_dict = {6:1, 18:2, 26:3}
import pdb


class neighbor:
    """Define neighor for pixel or voxel.
    
    Return
    ------
        offsets: 2xN or 3xN np array
    
    Contributions
    -------------
        Author: 
        Editor: 
    
    """
    def __init__(self, nbdim, nbsize):
        self.nbdim =  nbdim
        self.nbsize = nbsize

    def offsets(self):
        return self.compute_offsets()

class pixelconn(neighbor):
    """Define pixel connectivity for 2D or 3D image.
    
    Returns
    -------
        offsets: 2 x N or 3 x N np array, 
                N = nbdim + 1(current pixel is included)
    
    Contributions
    -------------
        Author: 
        Editor: 
    
    """

    def compute_offsets(self):
        if self.nbdim == 2: # 2D image 4, 6, 8-connected 
            if self.nbsize == 4:    
                offsets = np.array([[0, 0],
                                    [1, 0],[-1, 0],
                                    [0, 1],[0, -1]])
            elif self.nbsize == 6:                 
                offsets = np.array([[0, 0],
                                    [1, 0],[-1, 0],
                                    [0, 1],[0, -1],
                                    [1, 1], [-1, -1]])
            elif self.nbsize == 8: 
                offsets = np.array([[0, 0],
                                    [1, 0],[-1, 0],
                                    [0, 1],[0, -1],
                                    [1, 1], [-1, -1]
                                    [1, -1], [-1, 1]])
        elif self.nbdim == 3: # 3D volume 6, 18, 26-connected
            if self.nbsize == 6: 
                offsets = np.array([[0, 0, 0],
                                    [1, 0, 0],[-1, 0, 0],
                                    [0, 1, 0],[0, -1, 0],
                                    [0, 0, -1], [0, 0, -1]])      
            elif self.nbsize == 18: 
                offsets = np.array([[0, 0, 0],
                                    [0,-1,-1],[-1, 0,-1],[0, 0,-1],
                                    [1, 0,-1],[0, 1,-1],[-1,-1, 0],
                                    [0,-1, 0],[1,-1, 0],[-1, 0, 0],
                                    [1, 0, 0],[-1, 1, 0],[0, 1, 0],
                                    [1, 1, 0],[0,-1, 1],[-1, 0, 1],
                                    [0, 0, 1],[1, 0, 1],[0, 1, 1]])
        
            elif self.nbsize == 26: 
                offsets = np.array([[0, 0, 0],
                                    [-1,-1,-1],[0,-1,-1],[1,-1,-1],
                                    [-1, 0,-1],[0, 0,-1],[1, 0,-1],
                                    [-1, 1,-1],[0, 1,-1],[1, 1,-1],
                                    [-1,-1, 0],[0,-1, 0],[1,-1, 0], 
                                    [-1, 0, 0],[1, 0, 0],[-1, 1, 0],
                                    [0, 1, 0],[1, 1, 0],[-1,-1, 1],
                                    [0,-1, 1],[1,-1, 1],[-1, 0, 1],
                                    [0, 0, 1],[1, 0, 1],[-1, 1, 1],
                                    [0, 1, 1],[1, 1, 1]])
        return offsets.T


class sphere(neighbor):
    """Sphere neighbor for pixel or voxel.
    
    Contributions
    -------------
        Author: 
        Editor: 
    
    """
    
    def compute_offsets(self):
        offsets = []
        if self.nbdim == 2:
            for x in np.arange(-self.nbsize, self.nbsize + 1):
                for y in np.arange(-self.nbsize, self.nbsize + 1):
                    if np.linalg.norm([x,y]) <= self.nbsize:
                            offsets.append([x,y])
        elif self.nbdim == 3:
            for x in np.arange(-self.nbsize, self.nbsize + 1):
                for y in np.arange(-self.nbsize, self.nbsize + 1):
                    for z in np.arange(-self.nbsize, self.nbsize + 1):
                        if np.linalg.norm([x,y,z]) <= self.nbsize:
                            offsets.append([x,y,z])
        else: print 'wrong nbdim'

        return np.array(offsets).T
     
class cube(neighbor):
    """
    
    Contributions
    -------------
        Author: 
        Editor: 
    
    """
    
    def compute_offsets(self):
        offsets = []
        if self.nbdim == 2:
            for x in np.arange(-self.nhsize, self.nbsize + 1):
                for y in np.arange(-self.nbsize, self.nbsize + 1):
                    offsets.append([x,y])
        elif self.nbdim == 3:
            for x in np.arange(-self.nhsize, self.nbsize + 1):
                for y in np.arange(-self.nbsize, self.nbsize + 1):
                    for z in np.arange(-self.nbsize, self.nbsize + 1):
                        offsets.append([x,y,z])
        
        else: print 'wrong nbdim'
        return np.array(offsets).T

                    
                
def get_bound(low, high, v, dist):
    """
    
    Contributions
    -------------
        Author: 
        Editor: 

    """
    
    x = v - dist
    if x < low:
        x = low
    y = v + dist
    if y > high:
        y = high
    return x, y

def is_in_image(v, shape):
    """
    
    Contributions
    -------------
        Author: 
        Editor: 
    
    """
    
    if np.rank(v) == 1:
        return ((v[0] >= 0) & (v[0] < shape[0]) &
                (v[1] >= 0) & (v[1] < shape[1]) &
                (v[2] >= 0) & (v[2] < shape[2]))
    else:
        return np.all([v[:,0] >= 0,v[:,0] < shape[0],
                    v[:,1] >= 0,v[:,1] < shape[1],
                    v[:,2] >= 0,v[:,2] < shape[2]],axis = 0)
   
def out_of_image(v, shape):
    """
    
    Contributions
    -------------
        Author: 
        Editor:
    
    """
    if np.rank(v) == 1:
        return ((v[0] < 0) | (v[0] > shape[0] - 1)|
                (v[1] < 0) | (v[1] > shape[1] - 1)|
                (v[2] < 0) | (v[2] > shape[2] - 1))
    else:
        return np.any([v[:,0] < 0,v[:,0] > shape[0] - 1,
                        v[:,1] < 0,v[:,1] > shape[1] - 1,
                        v[:,2] < 0,v[:,2] > shape[2] - 1])
            
def dist(v1, v2, res):
    """
    
    Contributions
    -------------
        Author: 
        Editor: 
    
    """
    
    return ((res[0] * (v1[0] - v2[0])) ** 2 +
            (res[1] * (v1[1] - v2[1])) ** 2 +
            (res[2] * (v1[2] - v2[2])) ** 2) ** 0.5

def yzt_sphere(data, voxels, res, radius):
    """Deal with 3D data only.
    
    Parameters
    ----------
        data : array-like
        voxels : list of 3-item tuples
        radius : int or float
    
    Contributions
    -------------
        Author: 
        Editor: 
    """
    
    shape = data.shape
    if len(shape) != 3:
        raise ValueError('Data should be 3D')
    result = np.zeros(shape)
    resmin = min(res)
    dmax = int(radius / resmin)
    for idx, v in enumerate(voxels):
        result[v[0], v[1], v[2]] = 1
        xl, xh = get_bound(0, shape[0]-1, v[0], dmax)
        yl, yh = get_bound(0, shape[1]-1, v[1], dmax)
        zl, zh = get_bound(0, shape[2]-2, v[2], dmax)
        for x in range(xl, xh+1):
            for y in range(yl, yh+1):
                for z in range(zl, zh+1):
                    if (dist((x, y, z), v, res) <= radius and 
                        data[x, y, z] != 0):
                        result[x, y, z] = idx+1
    return result

def region_grow(data, voxels, res, radius, conn):
    """Generate a region the same size as a sphere.
    
    Contributions
    -------------
        Author: 
        Editor: 
    """
    shape = data.shape
    if len(shape) != 3:
        raise ValueError('Data should be 3D')
    result = np.zeros(shape)
    size = int((4.0 / 3 * pi * (radius ** 3)) / (res[0] * res[1] * res[2]))
    try:
        neighbor = ndimage.generate_binary_structure(3, conn_dict[conn])
    except KeyError:
        print 'Region grow connectivity must be 6, 18, or 26'
        raise
    pos = neighbor.nonzero()
    neighbor = zip(pos[0], pos[1], pos[2])
    neighbor.remove((1, 1, 1))
    neighbor = np.array(neighbor) - (1, 1, 1)
    for v in voxels:
        newv = [v]
        result[tuple(v)] = 1
        region_size = 1
        while region_size < size and newv != []:
            new_size = 0
            center = newv.pop(0)
            neighbor_pos = neighbor + center
            for pos in neighbor_pos:
                if (result[tuple(pos)] == 1 or out_of_image(pos, shape) or data[tuple(pos)] == 0):
                    continue
                newv.append(pos)
                result[tuple(pos)] = 1
                new_size += 1
            region_size += new_size
    return result
class neighbor_shape():
        def __init__(self,nbdim, nbsize, shape_type):
            self.nbdim = nbdim
            self.nbsize = nbsize
            self.shape_type = shape_type
                                

class  volneighbors(pixelconn):
    """ A class to compute the neighbor index for non zeros elements in volume
    
    Parameters
    -------
        imgdat: array-like.
        nbdim: int, 2 or 3, default 3.
        nbsize: int, default 26,
                radius of a sphere or half side of a cube,
                BUT pay special attention when using 'fast_cube' for shape.
        shape: str, 'sphere', 'cube' or 'fast_cube', default 'fast_cube',
                shape of the spatial constraints,
                when using 'fast_cube', nbsize must be 4 or 6 or 8 for nbdim 2,
                and 6 or 18 or 26 for nbdim 3.
        
    Return
    -------
        volneighbors
            volnb[v][0]: the 1d index for v
            volnb[v][1] 1d neighbor index for v
            volnb[v][2]: neighbor distance to v
    
    Contributions
    -------------
        Author: 
        Editor: conxz

    """
    
    def __init__(self, mask_coords,img_dims, nbdim=3, nbsize=26, shape='fast_cube'):
        pdb.set_trace()
        self.mask_coords = mask_coords
        self.dims = img_dims
        self.vol_num = np.shape(mask_coords)[0]
#        self.imgidx1d = np.array(np.nonzero(self.data1d > 0)).T
#        self.voxnum = np.shape(self.imgidx1d)[0]
        
        if shape == 'fast_cube':
            self.nb_shape = pixelconn(nbdim, nbsize)
        elif shape == 'sphere':
            self.nb_shape = sphere(nbdim, nbsize)
        elif shape == 'cube':
            self.nb_shape = cube(nbdim, nbsize)
        else:
           raise RuntimeError('shape should be \'fast_cube\' or \'sphere\' or \'cube\'.') 


        #number of neighbor voxels  
        self.nb_num = np.shape(self.nb_shape.compute_offsets())[1]

    def get_offsets_dist(self,offsets):
    
    #    Compute neighbor distance.
    

        
        offsets_dist = np.zeros(len(offsets))
        for n in range(len(offsets)):
            offsets_dist[n] = np.linalg.norm(offsets[n])

        return offsets_dist
    
    def compute_offsets(self):
    
    #    Compute neighbor offsets index.
        mask_coords = self.mask_coords
        vol_num = self.vol_num
        nb_num = self.nb_num
        dims = self.dims
        mask_idx = np.ravel_multi_index(self.mask_coords.T, dims)
         
        offsets = self.nb_shape.compute_off()
        ds_idx = np.arange(vol_num)
        volid = np.zeros(nb_num*vol_num)
        nbid = np.zeros(nb_num*vol_num)
        is_nb = np.zeros(nb_num*vol_num)
        
        
        count = 0
        for v in range(self.vol_num):
            v3d = mask_coords[v,:]
            nb3d = v3d + offsets.T
            imgnb = is_in_image(nb3d, dims)
            nb1d = np.ravel_multi_index(nb3d[imgnb, :].T, dims)
            is_in_mask = np.in1d(nb1d,mask_idx)
            nb1d = nb1d[is_in_mask]
            nb_idx_in_mask = np.in1d(mask_idx,nb1d)
            nb1d = mask_idx[nb_idx_in_mask]
            nb_idx_in_ds = np.nonzero(nb_idx_in_mask)[0]
            volnb_num = len(nb1d)
            volid[ count: count + volnb_num]= np.tile(v, volnb_num)
            nbid[ count: count + volnb_num] = nb_idx_in_ds
            is_nb[ count: count + volnb_num] = 1
            count  = count + volnb_num
        neighbor_sparse_matrix = sparse.csc_matrix((is_nb,(volid,nbid)),shape = (vol_num,vol_num))
        return neighbor_sparse_matrix








if __name__ == "__main__":
    pdb.set_trace()
    mask = nib.load('prob-face-object.nii.gz')
    mask = mask.get_data()
    mask = np.nonzero(mask)
    nei = volneighbors(mask)
    matrix = nei.offsets_sparsematrix()



class  ncut_volneighbors(pixelconn):
    
    def __init__(self, imgdat, nbdim=3, nbsize=26, shape='fast_cube'):
 #       pdb.set_trace()
        self.data = imgdat
        self.data1d = imgdat.flatten()
        self.imgidx1d = np.array(np.nonzero(self.data1d > 0)).T
        self.voxnum = np.shape(self.imgidx1d)[0]

        if shape == 'fast_cube':
            self.nb_shape = pixelconn(nbdim, nbsize)
        elif shape == 'sphere':
            self.nb_shape = sphere(nbdim, nbsize)
        elif shape == 'cube':
            self.nb_shape = cube(nbdim, nbsize)
        else:
           raise RuntimeError('shape should be \'fast_cube\' or \'sphere\' or \'cube\'.')


    def get_offsets_dist(self,offsets):

    #    Compute neighbor distance.



        offsets_dist = np.zeros(len(offsets))
        for n in range(len(offsets)):
            offsets_dist[n] = np.linalg.norm(offsets[n])
#            print offsets_dist[n]
#            print offsets[n]
        return offsets_dist

    def compute_offsets(self):


    #    Compute neighbor offsets index.


        offsets = self.nb_shape.compute_offsets()

        # flatten data and get nonzero voxel index
        maskidx = np.arange(self.voxnum)
        # iteratly compute neighbor index for each voxel
        volnb = []
        dims = self.data.shape
        imgidx3d = np.array(np.unravel_index(self.imgidx1d, dims))
        imgidx3d = imgidx3d.T[0]
        for v in range(self.voxnum):
            v3d = imgidx3d[v,:]
            nb3d = v3d + offsets.T

            imgnb = is_in_image(nb3d, dims)

            nb1d = np.ravel_multi_index(nb3d[imgnb, :].T, dims)
            masnb = (self.data1d[nb1d] > 0)
        #    for j in range(nb1f[masnb])
        #        t = self.imgidx1d[j]*v
            v_offsets = offsets.T[imgnb]
            v_offsets = v_offsets[masnb]
            offsets_dist = self.get_offsets_dist( v_offsets)
            volnb.append([self.imgidx1d[v], nb1d[masnb], offsets_dist])

        return volnb
