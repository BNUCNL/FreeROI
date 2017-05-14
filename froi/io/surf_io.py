import os
import gzip
import numpy as np
import nibabel as nib
from nibabel.gifti import giftiio as g_io
from nibabel.spatialimages import ImageFileError

from ..algorithm.graph_tool import node_attr2array


def read_scalar_data(filepath):
    """
    Load in scalar data from an image.

    Parameters
    ----------
    filepath : str
        path to scalar data file

    Returns
    -------
    scalar_data : numpy array
        NxM array, N is the number of vertices,
        M is the number of time points.
    """
    try:
        data = nib.load(filepath).get_data()
        scalar_data = []
        if data.ndim == 4:
            for idx in range(data.shape[3]):
                scalar_data.append(np.ravel(data[..., idx], order='F'))
        else:
            scalar_data.append(np.ravel(data, order="F"))
        scalar_data = np.array(scalar_data).T
        return scalar_data

    except ImageFileError:
        ext = os.path.splitext(filepath)[1]
        if ext == ".mgz":
            openfile = gzip.open
        elif ext == ".mgh":
            openfile = open
        else:
            raise ValueError("Scalar file format must be readable "
                             "by Nibabel or .mg{hz} format")

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
        data = np.fromstring(fobj.read(nbytes), typecode)
    finally:
        fobj.close()

    scalar_data = []
    if data.ndim == 4:
        for idx in range(data.shape[3]):
            scalar_data.append(np.ravel(data[..., idx], order='F'))
    else:
        scalar_data.append(np.ravel(data, order="F"))
    scalar_data = np.array(scalar_data).T

    return scalar_data


def read_data(fpath, n_vtx_limit=None):

    (dir, fname) = os.path.split(fpath)
    suffix = fname.split('.')[-1]
    if suffix in ('curv', 'thickness'):
        data = nib.freesurfer.read_morph_data(fpath)
        data = data.astype(np.float64)

    elif suffix == 'label':
        data = nib.freesurfer.read_label(fpath)

    elif suffix in ('nii', 'gz', 'mgh', 'mgz'):  # FIXME remove the support for the 'gz'
        data = read_scalar_data(fpath)
        data = data.astype(np.float64)  # transform type of data into float64

    elif suffix == 'gii':
        gii_data = g_io.read(fpath).darrays
        data = gii_data[0].data

    else:
        raise TypeError('Unsupported data type.')

    if n_vtx_limit is not None:
        if suffix == 'label':
            if np.max(data) <= n_vtx_limit:
                label_array = np.zeros(n_vtx_limit, np.int)
                label_array[data] = 1
                data = label_array
            else:
                raise RuntimeError('vertices number mismatch!')
        else:
            if data.shape[0] != n_vtx_limit:
                raise RuntimeError('vertices number mismatch!')

    if data.dtype.byteorder == '>':
        data.byteswap(True)

    return data


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
