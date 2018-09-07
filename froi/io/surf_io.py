import os
import gzip
import numpy as np
import nibabel as nib

from ..algorithm.graph_tool import node_attr2array
from .io import GiftiReader, CiftiReader


def read_mgh(fpath):
    """
    read MGH/MGZ file data
    If the data in the file is a 3D array, it will be raveled as a surface map.
    If the data in the file is a 4D array, the first 3 dimensions will be raveled as a surface map,
    and the forth dimension is the number of surface maps.
    If the number of dimension is neither 3 nor 4, an error will be thrown.
    NOTE!!! MGH file format seemingly has 3D dimensions at least. As a result, it essentially
    regards the first dimensions as a volume and the forth dimension as the number of volumes.
    References:
        https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/MghFormat
    :param fpath: str
    :return: data: numpy array
    """
    data = nib.load(fpath).get_data()

    if data.ndim == 3:
        data = np.atleast_2d(np.ravel(data, order='F')).T
    elif data.ndim == 4:
        _data = []
        for idx in range(data.shape[3]):
            _data.append(np.ravel(data[..., idx], order='F'))
        data = np.array(_data).T
    else:
        raise ValueError("The number of dimension is neither 3 nor 4")

    return data


def read_nifti(fpath):
    """
    read Nifti file data
    If the data in the file is a 1D array, it will be regard as a surface map.
    If the data in the file is a 2D array, each row of it will be regard as a surface map.
    If the data in the file is a 3D array, it will be raveled as a surface map.
    If the data in the file is a 4D array, the first 3 dimensions will be raveled as a surface map,
    and the forth dimension is the number of surface maps.
    If the number of dimension is larger than 4, an error will be thrown.
    :param fpath: str
    :return: data: numpy array
    """
    data = nib.load(fpath).get_data()
    if data.ndim <= 2:
        data = np.atleast_2d(data).T
    elif data.ndim == 3:
        data = np.atleast_2d(np.ravel(data, order='F')).T
    elif data.ndim == 4:
        _data = []
        for idx in range(data.shape[3]):
            _data.append(np.ravel(data[..., idx], order='F'))
        data = np.array(_data).T
    else:
        raise ValueError("The number of dimension of data array is larger than 4.")

    return data


def read_scalar_data(fpath, n_vtx=None, brain_structure=None):

    fname = os.path.basename(fpath)
    suffix0 = fname.split('.')[-1]
    suffix1 = fname.split('.')[-2]
    islabel = False
    if suffix0 in ('curv', 'thickness', 'sulc', 'area'):
        data = nib.freesurfer.read_morph_data(fpath)
        data = np.atleast_2d(data).T

    elif suffix0 == 'label':
        islabel = True
        _data = nib.freesurfer.read_label(fpath)
        if n_vtx is None:
            raise RuntimeError("Reading label as scalar data need specify the number of vertices.")
        else:
            if np.max(_data) < n_vtx:
                label_array = np.zeros(n_vtx, np.int)
                label_array[_data] = 1
                data = np.array([label_array]).T
            else:
                raise RuntimeError('vertices number mismatch!')

    elif suffix0 == 'nii':
        if suffix1 in ('dscalar', 'dtseries', 'dlabel'):
            if suffix1 == 'dlabel':
                islabel = True
            reader = CiftiReader(fpath)
            data = reader.get_data(brain_structure, True).T
        else:
            data = read_nifti(fpath)

    elif suffix0 == 'gz' and suffix1 == 'nii':
        data = read_nifti(fpath)

    elif suffix0 in ('mgh', 'mgz'):
        data = read_mgh(fpath)

    elif suffix0 == 'gii':
        if suffix1 == 'label':
            islabel = True
        data = nib.load(fpath).darrays[0].data
        data = np.atleast_2d(data).T

    else:
        raise RuntimeError('Unsupported data type.')

    if n_vtx is not None:
        if data.shape[0] != n_vtx:
            raise RuntimeError('vertices number mismatch!')

    if not islabel:
        data = data.astype(np.float64)  # necessary for visualization

    if data.dtype.byteorder == '>':
        # may be useful for visualization
        data.byteswap(True)

    return data, islabel


def read_geometry(fpath):
    """
    read surface geometry data
    Parameters:
    ----------
    fpath: str
        a path to the file

    Returns:
    -------
        coords: numpy array
            shape (vertices, 3)
            Each row is a vertex coordinate
        faces: numpy array
            shape (triangles, 3)
    """
    if fpath.endswith('.surf.gii'):
        # GIFTI style geometry filename
        reader = GiftiReader(fpath)
        coords, faces = reader.coords, reader.faces
    elif fpath.endswith('.inflated') or fpath.endswith('.white') or fpath.endswith('pial'):
        # FreeSurfer style geometry filename
        coords, faces = nib.freesurfer.read_geometry(fpath)
    else:
        raise RuntimeError("This function isn't able to deal with the file format at present!")

    return coords, faces


def node_attr2text(fpath, graph, attrs, fmt='%d', comments='#!ascii\n', **kwargs):
    """
    save nodes' attributes to text file
    :param fpath: str
        output file name
    :param graph: nx.Graph
    :param attrs: tuple e.g. ('ncut label', 'color')
        nodes' attributes which are going to be saved
    :param fmt: str or sequence of strs, optional
    :param comments: str, optional
    :param kwargs: key-word arguments for numpy.savetxt()
    :return:
    """
    header = ''
    for attr in attrs:
        header = header + attr + '\t'

    X = node_attr2array(graph, attrs)
    np.savetxt(fpath, X, fmt=fmt, header=header, comments=comments, **kwargs)


def save2label(fpath, vertices, hemi_coords=None):
        """
        save labeled vertices to a text file

        Parameters
        ----------
        fpath : string
            The file path to output
        vertices : 1-D array_like sequence
            labeled vertices
        hemi_coords : numpy array
            If not None, it means that saving vertices as the freesurfer style.
        """
        header = str(len(vertices))
        vertices = np.array(vertices)
        if hemi_coords is None:
            np.savetxt(fpath, vertices, fmt='%d', header=header,
                       comments="#!ascii, label vertexes\n")
        else:
            coords = hemi_coords[vertices]
            unknow = np.zeros_like(vertices, np.float16)
            X = np.c_[vertices, coords, unknow]
            np.savetxt(fpath, X, fmt=['%d', '%f', '%f', '%f', '%f'],
                       header=header, comments="#!ascii, label vertexes\n")
