import os
import gzip
import numpy as np
import nibabel as nib

from ..algorithm.graph_tool import node_attr2array
from .io import GiftiReader, CiftiReader


def read_mgh_mgz(filepath):

    ext = os.path.splitext(filepath)[1]
    if ext == ".mgz":
        openfile = gzip.open
    elif ext == ".mgh":
        openfile = open
    else:
        raise ValueError("The data must be a mgh or mgz file!")

    fobj = openfile(filepath, "rb")
    # We have to use np.fromstring here as gzip fileobjects don't work
    # with np.fromfile; same goes for try/finally instead of with statement
    try:
        v = np.fromstring(fobj.read(4), ">i4")[0]
        if v != 1:
            # I don't actually know what versions this code will read, so to be
            # on the safe side, let's only let version 1 in for now.
            # Scalar data might also be in curv format (e.g. lh.thickness)
            # in which case the first item in the file is a magic number.
            raise NotImplementedError("Scalar data file version not supported")
        ndim1 = np.fromstring(fobj.read(4), ">i4")[0]
        ndim2 = np.fromstring(fobj.read(4), ">i4")[0]
        ndim3 = np.fromstring(fobj.read(4), ">i4")[0]
        nframes = np.fromstring(fobj.read(4), ">i4")[0]
        datatype = np.fromstring(fobj.read(4), ">i4")[0]
        # Set the number of bytes per voxel and numpy data type according to
        # FS codes
        databytes, typecode = {0: (1, ">i1"), 1: (4, ">i4"), 3: (4, ">f4"),
                               4: (2, ">h")}[datatype]
        # Ignore the rest of the header here, just seek to the data
        fobj.seek(284)
        nbytes = ndim1 * ndim2 * ndim3 * nframes * databytes
        # Read in all the data, keep it in flat representation
        # (is this ever a problem?)
        _data = np.fromstring(fobj.read(nbytes), typecode)
    finally:
        fobj.close()

    data = []
    if _data.ndim == 4:
        for idx in range(_data.shape[3]):
            data.append(np.ravel(_data[..., idx], order='F'))
    else:
        data.append(np.ravel(_data, order="F"))
    data = np.array(data).T

    return data


def read_scalar_data(fpath, n_vtx=None, brain_structure=None):

    fname = os.path.basename(fpath)
    suffix0 = fname.split('.')[-1]
    suffix1 = fname.split('.')[-2]
    islabel = False
    if suffix0 in ('curv', 'thickness'):
        data = nib.freesurfer.read_morph_data(fpath)
        data = data.astype(np.float64)  # necessary for visualization
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
            Warning('The data will be regarded as a nifti file.')
            _data = nib.load(fpath).get_data()
            data = []
            if _data.ndim == 4:
                for idx in range(_data.shape[3]):
                    data.append(np.ravel(_data[..., idx], order='F'))
            else:
                data.append(np.ravel(_data, order="F"))
            data = np.array(data).T

    elif suffix0 == 'gz' and suffix1 == 'nii':
        _data = nib.load(fpath).get_data()
        data = []
        if _data.ndim == 4:
            for idx in range(_data.shape[3]):
                data.append(np.ravel(_data[..., idx], order='F'))
        else:
            data.append(np.ravel(_data, order="F"))
        data = np.array(data).T

    elif suffix0 in ('mgh', 'mgz'):
        data = read_mgh_mgz(fpath)
        data = data.astype(np.float64)

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
