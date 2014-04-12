#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os
import numpy as np
import nibabel as nib
from scipy import sparse
import scipy.spatial.distance as distance
from pybp.algorithm import neighbor
import pybp.algorithm.python_ncut_lib as pyncut
import pdb
_DEBUG = True

#class graph:
#    def __init__(self, X, metric = 'euclidean'):
#        self.X = X
#        self.metric = metric
#    def connmat(self):
#        self.compute_conn()
#    def compute_conn(self):
#        return distance.pdist(self.X, self.metric)        
class graph:
    def _init_(self,X,metric = 'euclidean'):
        self.X = X
        self.metric = metrix
    def connmat(self):
        self.compute_conn()
    def compute_conn(self):
        return distance.cdist(self.X,self.metric)

class volgraph(graph):
#    """
#    Generate graph for 3D/4D volume data 
#    """
    def __init__(self, targnii, masknii = None, metric= 'euclidean'):
        self.targ =  nib.load(targnii)
        self.metric = metric
        self.dims = np.shape(nib.load(targnii))
        if masknii is not None:
            self.mask = nib.load(masknii)
        else:
            self.mask = None
    def get_dims(self):
        dims = np.shape(self.targ.get_data())
        return dims
    def compute_conn(self):
        # Transform image to 2D and mask it
        dims = get_dims()
        targ = np.reshape(self.targ.get_data(),(np.prod(self.dims[0:3]),-1))
        if self.mask is not None:
            mask = np.reshape(self.mask.get_data(),(np.prod(self.dims[0:3]),-1))

        #compute connectivity matrx 
        graph = distance.pdist(targ[mask,:], self.metric)
        return graph

    def savenodeasnii(self, filename, nodecs):
        volout = np.array(self.mask.get_shape())
        if self.mask is not None:
            mask = self.mask.get_data()
            volout[mask] = nodecs
        else:
            volout[:] = nodecs
        self.volout = nib.Nifti1Image(volout, None, self.targ.get_header())
        nib.save(self.volout,filename)
#class volgraph(graph):
#    def _init_(self,targnii,masknii = None,metric='euclidean'):
#        self.targ = nib.load(targnii)
#        self.metric = mentric
#        self.dims = np.shape(nib.load(targnii))
#        if masknii is not None:
#            self.mask = nib.load(masknii)
#        else:
#            self.mask = None
#    def compute_conn(self):
#        #Transform image to 2D and mask it
#        dims = np.shape(targ.get_data())
#        targ = np.reshape(self.targ.get_data(),(np.prod(self.dims[0:3]),-1))
#        if self.mask is not None:
#            mask = np.reshape(self.mask.get_data(),(np.prod(self.dims[0:3]),-1))
        #Compute connectivity matrix
#        graph = distance.pdist(targ[mask,:])

class spatialconstraingraph(volgraph):
    """
#    Generate graph for 3D/4D volume data with spatial neighborhood constrain
#    """
    def __init__(self, targnii, masknii = None, metric = 'euclidean', nb=(3, 26)):
        volgraph.__init__(self, targnii, masknii, metric)
        self.nb = nb

    def compute_conn(self):
        # get neigbors for each voxels
        targ = np.reshape(self.targ.get_data(),(np.prod(self.dims[0:3]),-1))
        if self.mask is not None:
            mask = self.mask.get_data()
        else:
            mask = self.targ.get_data()
        print np.shape(mask)
        pdb.set_trace()
#        tempdata = np.array([[[1,1,1],[2,2,2],[3,3,3]],[[4,4,4],[5,5,5],[6,6,6]],[[7,7,7],[8,8,8],[9,9,9]]])

#        tempdata = np.array(
          # get neigbors for each voxels
        nbs = neighbor.volneighbors(mask, self.nb[0], self.nb[1])
#        nbs = neighbor.volneighbors(tempdata, self.nb[0], self.nb[1])
        vnum = nbs.voxnum
        nbs = nbs.compute_offsets()
        #compute connectivity matrx 
        I = np.zeros((vnum*27))
        J = np.zeros((vnum*27))
        V = np.zeros((vnum*27)) 
        count = 0

        for v in range(vnum):
#            print v
#            print count
#            pdb.set_trace()

            vidx = nbs[v][0] # voxel index in image space
            nbidx= nbs[v][1] # neighbor index in image space
#            dist = distance.cdist(targ[vidx,:],targ[nbidx,:],self.metric)
            #dist = np.exp(neurodist)
#            dist =np.exp(- (nbs[v][2]**2+ nbs[v][3]**2))
            dist = np.exp(-nbs[v][2])
#            print np.shape(dist)
#            print dist
#            I = np.append(I,np.tile(nbs[v][0], nbidx.shape[0])) # in mask index
#            J = np.append(J,nbs[v][1]) # in mask index
#            V = np.append(V,dist)
            nbs_len = len(nbidx)
#            print nbs_len
            I[count:count + nbs_len] = np.tile(nbs[v][0], nbidx.shape[0])
#            print I[count:count + nbs_len]
            J[count:count + nbs_len] = nbs[v][1]
#            print J[count:count + nbs_len]
            V[count:count + nbs_len] = dist
#            print V[count:count + nbs_len]
#            I.append(np.tile(nbs[v][0], nbidx.shape[0]))
#            J.append(nbs[v][1])
#            V.append(dist)
            count = count + nbs_len
        pdb.set_trace()        
        print "ok"
        print np.shape(V)
        print np.shape(I)
        print np.shape(J)
        dims = volgraph.get_dims(self)
#        total = np.prod(dims)
        total  = np.prod(dims)
        graph = sparse.csc_matrix((V, (I,J)), shape = (total, total))
        return graph
        
#class spatialconstraingraph(volgraph):
#    def _init_(self, targnii,masknii = None, metric = 'euclidean', nb=(3,26)):
#        volgraph._init_(self,targnii, masknii, metric)
#        self.nb = nb
#    def compute_conn(self):
#        data1d = np.reshape(self.targ.get_data(),(np.prod(self.dims[0:3]),-1))
#        if self.mask is not None:
#            mask = self.mask.get_data()
#        else:
#            mask = self.targ.get_data()
#        nbs = neighbor.volneighbors(mask,self.nb[0],self.nb[1])
#        vnum = nbs.voxnum()
#        nbs = nbs.compute_offsets() 

class graphcut:
    """
    Do graph cut with ncut algorithm
    """
    def __init__(self, graph, ncluster):
        self.graph = graph
        self.ncluster = ncluster
    
    def ncut(self):
#        dims = (3,3,3)
        dims = (91,109,91)
        graphconn = self.graph.compute_conn()
        total = np.shape(graphconn)[0]
        print "1"
        print np.shape(graphconn)
        print np.max(self.ncluster)
        pdb.set_trace()
        eigenval, eigenvec = pyncut.ncut(graphconn, np.max(self.ncluster))

        # Discretize to label
#        self.labelcut = np.array(eigenvec.shape[0], len(self.ncluster))
#        for c in range(self.ncluster):
#            eigk = eigenvec[:,:c]
#            print eigk
        eigenvec_discrete = pyncut.discretisation(eigenvec)
        img_outfile_1d = eigenvec_discrete[:,0]
        for i in range(self.ncluster):
            img_outfile_1d = img_outfile_1d + (i + 1)*eigenvec_discrete[:,i]
        img_outfile_1d = list(img_outfile_1d.todense())
        img_outfile_3d = np.reshape(img_outfile_1d,dims)
        print "ok"
    #    name = "mytest.nii.gz"
    
     #   nib.save(img_outfile_3d,name)
        return img_outfile_3d

if __name__ == "__main__":
    targnii = 'prob-face-object.nii.gz'
    masknii = 'prob-face-object.nii.gz'
    volume_graph = spatialconstraingraph(targnii,masknii)
    pacel = graphcut(volume_graph,20).ncut()
  #  for p in range(parcel.shape[1]):
    spvolgraph.savenodeasnii('mytest.nii.gz', parcel)
