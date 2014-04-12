
from os.path import join as pjoin
import numpy as np
import nibabel as nib
import scipy.spatial.distance as distance
import pybp.algorithm.python_ncut_lib as pyncut

from scipy import sparse
from os.path import join as pjoin
from pybp.algorithm import neighbor


from mvpa2.base.dochelpers import _str, _repr_attrs
from mvpa2.mappers.base import Mapper
from mvpa2.datasets import Dataset
from mvpa2.datasets.mri import map2nifti
from bpmri import *




from mvpa2.testing.tools import ok_, assert_equal, assert_array_equal
import pdb


   



class GraphMapper(Mapper):
	def _init_(self,neighbors = None, metric = 'euclidean',chunks_attr = 'chunks'):
		self._thresh = thresh
		self._neighbors = neighbors
		self._metric = metric
		self._chunks_attr = chunks_attr
	
	def _str_(self):
                return _str(self)

	def _forward_dataset(self,ds):
		
		if self._neighbors is None and ds.samples.max()== ds.samples.min():
			raise RuntimeError("The dataset is homogeneity, so the neighbors which offer spatial constrain cannot be null.")
		img = map2nifti(ds)
		mds = ds.copy(deep = Flase)
		mds.samples = ds.samples.copy()
		
		for c in mds.sa[chunks_attr].unique:
			slicer = np.where(mds.sa[chunks_attr].value == c)[0]
		mds.samples[slicer] = self._graph(mds.samples[slicer],np.shape(img))
		mds.a['DsType'] = 'graph'
		mds.a['header'] = img.get_header()
		mds.a['dims'] = np.shape(img)
		return mds	
		
	def _graph(self,samples,dims):
		total = np.prod(dims)
		if not self._neighbors is None:
			vnum = samples.nonzero.size
			neighghbors = self._neighbors
			nbs = neighbors.compute_conn()
			vidx = nbs[0]
			nidx = nbs[1]

			I = np.zeros((vnum*27))
       			J = np.zeros((vnum*27))
       			V = np.zeros((vnum*27))
       			count = 0
			for v in range(vnum):
				vidx = nbs[v][0]
				nbidx = nbs[v][1]
				nbs_len = len(nbs[v][1])
				dist = np.exp(-nbs[v][2])
				I[count:count + nbs_len] = np.tile(nbs[v][0],nbidx.shape[0]) 
				J[count:count + nbs_len] = nbs[v][1]
				V[count:count + nbs_len] = dist
				count  = count + nbs_len
			graph = sparse.csc_matrix((V,(I,J)),shape = (total,total))
		else:	
			graph = distance.pdist(samples)
			graph = sparse.csc_matrix(graph)
		return graph
 	
			
			
		


class NcutSegmentationMapper(Mapper):
	def _init_(self,ncluster,chunks_attr = 'chunks'):
		self._ncluster = ncluster
		self._chunks_attr = chunks_attr
	def _str_(self):
		return _str(self)

	def _forward_dataset(self,ds):
		if not ds.a['DsType'] == 'graph':
			raise RuntimeError("%s cannot only do datasets with type of graph."% self)
		dims = ds.a['dims']
		header = ds.a['header']
		mds = ds.copy(deep = False)
		mds.samples = mds.samples.copy()
		for c in mds.sa[chunks_attr].unique:
			slicer  = np.where(mds.sa[chunks_attr].value == c)[0]
		markers = _ncut(graph,self._ncluster,dims)
		result = np.reshape(markers)

		ming = nib.NiftiImage(result,None,header)
		mds = bpfmri_dataset(ming)
		mds.a['markers'] = markers
		return mds

	def _ncut(self,graph,ncluster,dims):
		total = np.prod(dims)
		eigenval, eigenvec = pyncut.ncut(graph,ncluster)
		eigenvec_discrete= pyncut.descretisation(eigenvec)
		markers = eigenvec_discrete[:,0]
		for i in range(total):
			markers = markers + (i + 1) * eigenvec_discrete[:,i]
		markers = markers.todense()

		return markers









if __name__ == "__main__":
#	datadir = '../data'
	targnii = 'prob-face-object.nii.gz'
    	masknii = 'prob-face-object.nii.gz'
	mask = nib.load(masknii)
	mask = mask.get_data()
#	ds = bpfmri_dataset(pjoin(datadir,targnii))
	ds = bpfmri_dataset(targnii)
	nbs = neighbor.volneighbors(mask, 3,26 )
    	nbs = nbs.compute_offsets()
	map = GraphMapper(nbs)
	nds = map(ds)
#	assert_array_equal(data, map2nifti(nds).get_data()[...,0])
	result = map2nifti(nds)










