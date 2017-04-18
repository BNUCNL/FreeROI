import os
import numpy as np
import nibabel as nib
from nibabel.gifti import giftiio as g_io


def read_scalar_data(filepath):
    """
	Load in scalar data from an image.

    Parameters
    ----------
    filepath : str
        path to scalar data file

    Returns
    -------
    scalar_data : [numpy array]
        flat numpy array of scalar data
    """
    try:
        scalar_data = nib.load(filepath).get_data()
        shape = scalar_data.shape
        if len(shape) == 4:
            scalar_data_list = []
            for index in range(shape[3]):
                scalar_data_list.append(np.ravel(scalar_data[:, :, :, index], order='F'))
        else:
            scalar_data_list = [np.ravel(scalar_data, order="F")]
        return scalar_data_list

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
        scalar_data = np.fromstring(fobj.read(nbytes), typecode)
    finally:
        fobj.close()

    return [scalar_data]


def read_data(fpath, n_vtx_limit=None):

    (dir, fname) = os.path.split(fpath)
    suffix = fname.split('.')[-1]
    if suffix in ('curv', 'thickness'):
        data = nib.freesurfer.read_morph_data(fpath)
        data = data.astype(np.float64)
        if data.dtype.byteorder == '>':
            data.byteswap(True)

    elif suffix == 'label':
        data = nib.freesurfer.read_label(fpath)
        if data.dtype.byteorder == '>':
            data.byteswap(True)

    elif suffix in ('nii', 'gz', 'mgh', 'mgz'):  # FIXME remove the support for the 'gz'
        data_list = read_scalar_data(fpath)
        for _ in data_list:
            if _.shape[0] != n_vtx_limit:
                raise RuntimeError('vertices number mismatch!')

            # transform type of data into float64
            _ = _.astype(np.float64)
            if _.dtype.byteorder == '>':
                _.byteswap(True)
        return data_list

    elif suffix == 'mat':
        'just test, should not be formally supported'
        from scipy import io as sp_io
        # read scalar data
        mat_data1 = sp_io.loadmat(fpath)
        scalar = mat_data1.values()[2][0]

        # read vertex number corresponded to scalar data
        mat_data2 = sp_io.loadmat('/nfs/j3/userhome/chenxiayu/workingdir/test/lqq/FFA_vanE_ver_num.mat')
        vertices = mat_data2.values()[2][0]

        # create scalar data array with suitable size
        data = np.zeros(n_vtx_limit, np.float)
        data[vertices] = scalar

    elif suffix == 'gii':
        gii_data = g_io.read(fpath).darrays
        data = gii_data[0].data

    else:
        raise TypeError('Unsupported data type.')

    if n_vtx_limit is not None:
        if suffix == 'label':
            if np.max(data) <= n_vtx_limit:
                if data.dtype.byteorder == '>':
                    data.byteswap(True)

                label_array = np.zeros(n_vtx_limit, np.int)
                label_array[data] = 1
                data = label_array
            else:
                raise RuntimeError('vertices number mismatch!')
        else:
            if data.shape[0] != n_vtx_limit:
                raise RuntimeError('vertices number mismatch!')
    return [data]
