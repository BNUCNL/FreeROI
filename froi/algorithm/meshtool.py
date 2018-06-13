# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import subprocess
import numpy as np
from scipy import sparse
from scipy.spatial.distance import cdist, pdist
from scipy.stats import pearsonr


def _fast_cross_3d(x, y):
    """Compute cross product between list of 3D vectors

    Much faster than np.cross() when the number of cross products
    becomes large (>500). This is because np.cross() methods become
    less memory efficient at this stage.

    Parameters
    ----------
    x : array
        Input array 1.
    y : array
        Input array 2.

    Returns
    -------
    z : array
        Cross product of x and y.

    Notes
    -----
    x and y must both be 2D row vectors. One must have length 1, or both
    lengths must match.
    """
    assert x.ndim == 2
    assert y.ndim == 2
    assert x.shape[1] == 3
    assert y.shape[1] == 3
    assert (x.shape[0] == 1 or y.shape[0] == 1) or x.shape[0] == y.shape[0]
    if max([x.shape[0], y.shape[0]]) >= 500:
        return np.c_[x[:, 1] * y[:, 2] - x[:, 2] * y[:, 1],
                     x[:, 2] * y[:, 0] - x[:, 0] * y[:, 2],
                     x[:, 0] * y[:, 1] - x[:, 1] * y[:, 0]]
    else:
        return np.cross(x, y)


def compute_normals(rr, tris):
    """Efficiently compute vertex normals for triangulated surface"""
    # first, compute triangle normals
    r1 = rr[tris[:, 0], :]
    r2 = rr[tris[:, 1], :]
    r3 = rr[tris[:, 2], :]
    tri_nn = _fast_cross_3d((r2 - r1), (r3 - r1))

    # Triangle normals and areas
    size = np.sqrt(np.sum(tri_nn * tri_nn, axis=1))
    zidx = np.where(size == 0)[0]
    # prevent ugly divide-by-zero
    size[zidx] = 1.0
    tri_nn /= size[:, np.newaxis]

    npts = len(rr)

    # the following code replaces this, but is faster (vectorized):
    #
    # for p, verts in enumerate(tris):
    #     nn[verts, :] += tri_nn[p, :]
    #
    nn = np.zeros((npts, 3))
    # note this only loops 3x (number of verts per tri)
    for verts in tris.T:
        for idx in range(3):  # x, y, z
            nn[:, idx] += np.bincount(verts, tri_nn[:, idx], minlength=npts)
    size = np.sqrt(np.sum(nn * nn, axis=1))
    # prevent ugly divide-by-zero
    size[size == 0] = 1.0  
    nn /= size[:, np.newaxis]
    return nn


def find_closest_vertices(surface_coords, point_coords):
    """Return the vertices on a surface mesh closest to some 
    given coordinates.

    The distance metric used is Euclidian distance.

    Parameters
    ----------
    surface_coords : numpy array
        Array of coordinates on a surface mesh
    point_coords : numpy array
        Array of coordinates to map to vertices

    Returns
    -------
    closest_vertices : numpy array
        Array of mesh vertex ids

    """
    point_coords = np.atleast_2d(point_coords)
    return np.argmin(cdist(surface_coords, point_coords), axis=0)


def tal_to_mni(coords):
    """Convert Talairach coords to MNI using the Lancaster transform.

    Parameters
    ----------
    coords : n x 3 numpy array
        Array of Talairach coordinates

    Returns
    -------
    mni_coords : n x 3 numpy array
        Array of coordinates converted to MNI space

    """
    coords = np.atleast_2d(coords)
    xfm = np.array([[1.06860, -0.00396, 0.00826,  1.07816],
                    [0.00640,  1.05741, 0.08566,  1.16824],
                    [-0.01281, -0.08863, 1.10792, -4.17805],
                    [0.00000,  0.00000, 0.00000,  1.00000]])
    mni_coords = np.dot(np.c_[coords, np.ones(coords.shape[0])], xfm.T)[:, :3]
    return mni_coords


def mesh_edges(faces):
    """
    Returns sparse matrix with edges as an adjacency matrix

    Parameters
    ----------
    faces : array of shape [n_triangles x 3]
        The mesh faces

    Returns
    -------
    edges : sparse matrix
        The adjacency matrix
    """
    npoints = np.max(faces) + 1
    nfaces = len(faces)
    a, b, c = faces.T
    edges = sparse.coo_matrix((np.ones(nfaces), (a, b)),
                              shape=(npoints, npoints))
    edges = edges + sparse.coo_matrix((np.ones(nfaces), (b, c)),
                                      shape=(npoints, npoints))
    edges = edges + sparse.coo_matrix((np.ones(nfaces), (c, a)),
                                      shape=(npoints, npoints))
    edges = edges + edges.T
    edges = edges.tocoo()
    return edges


def create_color_lut(cmap, n_colors=256):
    """Return a colormap suitable for setting as a Mayavi LUT.

    Parameters
    ----------
    cmap : string, list of colors, n x 3 or n x 4 array
        Input colormap definition. This can be the name of a matplotlib
        colormap, a list of valid matplotlib colors, or a suitable
        mayavi LUT (possibly missing the alpha channel).
    n_colors : int, optional
        Number of colors in the resulting LUT. This is ignored if cmap
        is a 2d array.
    Returns
    -------
    lut : n_colors x 4 integer array
        Color LUT suitable for passing to mayavi
    """
    if isinstance(cmap, np.ndarray):
        if np.ndim(cmap) == 2:
            if cmap.shape[1] == 4:
                # This looks likes a LUT that's ready to go
                lut = cmap.astype(np.int)
            elif cmap.shape[1] == 3:
                # This looks like a LUT, but it's missing the alpha channel
                alpha = np.ones(len(cmap), np.int) * 255
                lut = np.c_[cmap, alpha]

            return lut

    # Otherwise, we're going to try and use matplotlib to create it

    if cmap in dir(cm):
        # This is probably a matplotlib colormap, so build from that
        # The matplotlib colormaps are a superset of the mayavi colormaps
        # except for one or two cases (i.e. blue-red, which is a crappy
        # rainbow colormap and shouldn't be used for anything, although in
        # its defense it's better than "Jet")
        cmap = getattr(cm, cmap)

    elif np.iterable(cmap):
        # This looks like a list of colors? Let's try that.
        colors = list(map(mpl.colors.colorConverter.to_rgb, cmap))
        cmap = mpl.colors.LinearSegmentedColormap.from_list("_", colors)

    else:
        # If we get here, it's a bad input
        raise ValueError("Input %s was not valid for making a lut" % cmap)

    # Convert from a matplotlib colormap to a lut array
    lut = (cmap(np.linspace(0, 1, n_colors)) * 255).astype(np.int)

    return lut


def smoothing_matrix(vertices, adj_mat, smoothing_steps=20, verbose=None):
    """Create a smoothing matrix which can be used to interpolate data defined
       for a subset of vertices onto mesh with an adjancency matrix given by
       adj_mat.

       If smoothing_steps is None, as many smoothing steps are applied until
       the whole mesh is filled with with non-zeros. Only use this option if
       the vertices correspond to a subsampled version of the mesh.

    Parameters
    ----------
    vertices : 1d array
        vertex indices
    adj_mat : sparse matrix
        N x N adjacency matrix of the full mesh
    smoothing_steps : int or None
        number of smoothing steps (Default: 20)
    verbose : bool, str, int, or None
        If not None, override default verbose level (see surfer.verbose).

    Returns
    -------
    smooth_mat : sparse matrix
        smoothing matrix with size N x len(vertices)
    """
    from scipy import sparse

    logger.info("Updating smoothing matrix, be patient..")

    e = adj_mat.copy()
    e.data[e.data == 2] = 1
    n_vertices = e.shape[0]
    e = e + sparse.eye(n_vertices, n_vertices)
    idx_use = vertices
    smooth_mat = 1.0
    n_iter = smoothing_steps if smoothing_steps is not None else 1000
    for k in range(n_iter):
        e_use = e[:, idx_use]

        data1 = e_use * np.ones(len(idx_use))
        idx_use = np.where(data1)[0]
        scale_mat = sparse.dia_matrix((1 / data1[idx_use], 0),
                                      shape=(len(idx_use), len(idx_use)))

        smooth_mat = scale_mat * e_use[idx_use, :] * smooth_mat

        logger.info("Smoothing matrix creation, step %d" % (k + 1))
        if smoothing_steps is None and len(idx_use) >= n_vertices:
            break

    # Make sure the smoothing matrix has the right number of rows
    # and is in COO format
    smooth_mat = smooth_mat.tocoo()
    smooth_mat = sparse.coo_matrix((smooth_mat.data,
                                    (idx_use[smooth_mat.row],
                                     smooth_mat.col)),
                                   shape=(n_vertices,
                                          len(vertices)))

    return smooth_mat


def coord_to_label(subject_id, coord, label, hemi='lh', n_steps=30,
                   map_surface='white', coord_as_vert=False, verbose=None):
    """Create label from MNI coordinate

    Parameters
    ----------
    subject_id : string
        Use if file is in register with subject's orig.mgz
    coord : numpy array of size 3 | int
        One coordinate in MNI space or the vertex index.
    label : str
        Label name
    hemi : [lh, rh]
        Hemisphere target
    n_steps : int
        Number of dilation iterations
    map_surface : str
        The surface name used to find the closest point
    coord_as_vert : bool
        whether the coords parameter should be interpreted as vertex ids
    verbose : bool, str, int, or None
        If not None, override default verbose level (see surfer.verbose).
    """
    geo = Surface(subject_id, hemi, map_surface)
    geo.load_geometry()

    if coord_as_vert:
        coord = geo.coords[coord]

    n_vertices = len(geo.coords)
    adj_mat = mesh_edges(geo.faces)
    foci_vtxs = find_closest_vertices(geo.coords, [coord])
    data = np.zeros(n_vertices)
    data[foci_vtxs] = 1.
    smooth_mat = smoothing_matrix(np.arange(n_vertices), adj_mat, 1)
    for _ in range(n_steps):
        data = smooth_mat * data
    idx = np.where(data.ravel() > 0)[0]
    # Write label
    label_fname = label + '-' + hemi + '.label'
    logger.info("Saving label : %s" % label_fname)
    f = open(label_fname, 'w')
    f.write('#label at %s from subject %s\n' % (coord, subject_id))
    f.write('%d\n' % len(idx))
    for i in idx:
        x, y, z = geo.coords[i]
        f.write('%d  %f  %f  %f 0.000000\n' % (i, x, y, z))


def _get_subjects_dir(subjects_dir=None, raise_error=True):
    """Get the subjects directory from parameter or environment variable

    Parameters
    ----------
    subjects_dir : str | None
        The subjects directory.
    raise_error : bool
        If True, raise a ValueError if no value for SUBJECTS_DIR can be found
        or the corresponding directory does not exist.

    Returns
    -------
    subjects_dir : str
        The subjects directory. If the subjects_dir input parameter is not
        None, its value will be returned, otherwise it will be obtained from
        the SUBJECTS_DIR environment variable.
    """
    if subjects_dir is None:
        subjects_dir = os.environ.get("SUBJECTS_DIR", "")
        if not subjects_dir and raise_error:
            raise ValueError('The subjects directory has to be specified '
                             'using the subjects_dir parameter or the '
                             'SUBJECTS_DIR environment variable.')

    if raise_error and not os.path.exists(subjects_dir):
        raise ValueError('The subjects directory %s does not exist.'
                         % subjects_dir)

    return subjects_dir


def has_fsaverage(subjects_dir=None):
    """Determine whether the user has a usable fsaverage"""
    fs_dir = os.path.join(_get_subjects_dir(subjects_dir, False), 'fsaverage')
    if not os.path.isdir(fs_dir):
        return False
    if not os.path.isdir(os.path.join(fs_dir, 'surf')):
        return False
    return True

requires_fsaverage = np.testing.dec.skipif(not has_fsaverage(),
                                           'Requires fsaverage subject data')


# ---  check ffmpeg
def has_ffmpeg():
    """Test whether the FFmpeg is available in a subprocess

    Returns
    -------
    ffmpeg_exists : bool
        True if FFmpeg can be successfully called, False otherwise.
    """
    try:
        subprocess.call(["ffmpeg"], stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        return True
    except OSError:
        return False


def assert_ffmpeg_is_available():
    "Raise a RuntimeError if FFmpeg is not in the PATH"
    if not has_ffmpeg():
        err = ("FFmpeg is not in the path and is needed for saving "
               "movies. Install FFmpeg and try again. It can be "
               "downlaoded from http://ffmpeg.org/download.html.")
        raise RuntimeError(err)

requires_ffmpeg = np.testing.dec.skipif(not has_ffmpeg(), 'Requires FFmpeg')


def ffmpeg(dst, frame_path, framerate=24, codec='mpeg4', bitrate='1M'):
    """Run FFmpeg in a subprocess to convert an image sequence into a movie

    Parameters
    ----------
    dst : str
        Destination path. If the extension is not ".mov" or ".avi", ".mov" is
        added. If the file already exists it is overwritten.
    frame_path : str
        Path to the source frames (with a frame number field like '%04d').
    framerate : float
        Framerate of the movie (frames per second, default 24).
    codec : str | None
        Codec to use (default 'mpeg4'). If None, the codec argument is not
        forwarded to ffmpeg, which preserves compatibility with very old
        versions of ffmpeg
    bitrate : str | float
        Bitrate to use to encode movie. Can be specified as number (e.g.
        64000) or string (e.g. '64k'). Default value is 1M

    Notes
    -----
    Requires FFmpeg to be in the path. FFmpeg can be downlaoded from `here
    <http://ffmpeg.org/download.html>`_. Stdout and stderr are written to the
    logger. If the movie file is not created, a RuntimeError is raised.
    """
    assert_ffmpeg_is_available()

    # find target path
    dst = os.path.expanduser(dst)
    dst = os.path.abspath(dst)
    root, ext = os.path.splitext(dst)
    dirname = os.path.dirname(dst)
    if ext not in ['.mov', '.avi']:
        dst += '.mov'

    if os.path.exists(dst):
        os.remove(dst)
    elif not os.path.exists(dirname):
        os.mkdir(dirname)

    frame_dir, frame_fmt = os.path.split(frame_path)

    # make the movie
    cmd = ['ffmpeg', '-i', frame_fmt, '-r', str(framerate),
           '-b:v', str(bitrate)]
    if codec is not None:
        cmd += ['-c', codec]
    cmd += [dst]
    logger.info("Running FFmpeg with command: %s", ' '.join(cmd))
    sp = subprocess.Popen(cmd, cwd=frame_dir, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

    # log stdout and stderr
    stdout, stderr = sp.communicate()
    std_info = os.linesep.join(("FFmpeg stdout", '=' * 25, stdout))
    logger.info(std_info)
    if stderr.strip():
        err_info = os.linesep.join(("FFmpeg stderr", '=' * 27, stderr))
        # FFmpeg prints to stderr in the absence of an error
        logger.info(err_info)

    # check that movie file is created
    if not os.path.exists(dst):
        err = ("FFmpeg failed, no file created; see log for more more "
               "information.")
        raise RuntimeError(err)


def get_n_ring_neighbor(faces, n=1, ordinal=False, mask=None):
    """
    get n ring neighbor from faces array

    Parameters
    ----------
    faces : numpy array
        the array of shape [n_triangles, 3]
    n : integer
        specify which ring should be got
    ordinal : bool
        True: get the n_th ring neighbor
        False: get the n ring neighbor
    mask : 1-D numpy array
        specify a area where the ROI is in.
    Returns
    -------
    lists
        each index of the list represents a vertex number
        each element is a set which includes neighbors of corresponding vertex
    """
    n_vtx = np.max(faces) + 1  # get the number of vertices

    # find 1_ring neighbors' id for each vertex
    coo_w = mesh_edges(faces)
    csr_w = coo_w.tocsr()
    if mask is None:
        vtx_iter = range(n_vtx)
        n_ring_neighbors = [csr_w.indices[csr_w.indptr[i]:csr_w.indptr[i+1]] for i in vtx_iter]
        n_ring_neighbors = [set(i) for i in n_ring_neighbors]
    else:
        mask_id = np.nonzero(mask)[0]
        vtx_iter = mask_id
        n_ring_neighbors = [set(csr_w.indices[csr_w.indptr[i]:csr_w.indptr[i+1]])
                            if mask[i] != 0 else set() for i in range(n_vtx)]
        for vtx in vtx_iter:
            neighbor_set = n_ring_neighbors[vtx]
            neighbor_iter = list(neighbor_set)
            for i in neighbor_iter:
                if mask[i] == 0:
                    neighbor_set.discard(i)

    if n > 1:
        # find n_ring neighbors
        one_ring_neighbors = [i.copy() for i in n_ring_neighbors]
        n_th_ring_neighbors = [i.copy() for i in n_ring_neighbors]
        # if n>1, go to get more neighbors
        for i in range(n-1):
            for neighbor_set in n_th_ring_neighbors:
                neighbor_set_tmp = neighbor_set.copy()
                for v_id in neighbor_set_tmp:
                    neighbor_set.update(one_ring_neighbors[v_id])

            if i == 0:
                for v_id in vtx_iter:
                    n_th_ring_neighbors[v_id].remove(v_id)

            for v_id in vtx_iter:
                n_th_ring_neighbors[v_id] -= n_ring_neighbors[v_id]  # get the (i+2)_th ring neighbors
                n_ring_neighbors[v_id] |= n_th_ring_neighbors[v_id]  # get the (i+2) ring neighbors
    elif n == 1:
        n_th_ring_neighbors = n_ring_neighbors
    else:
        raise RuntimeError("The number of rings should be equal or greater than 1!")

    if ordinal:
        return n_th_ring_neighbors
    else:
        return n_ring_neighbors


def get_vtx_neighbor(vtx, faces, n=1, ordinal=False, mask=None):
    """
    Get one vertex's n-ring neighbor vertices

    Parameters
    ----------
    vtx : integer
        a vertex's id
    faces : numpy array
        the array of shape [n_triangles, 3]
    n : integer
        specify which ring should be got
    ordinal : bool
        True: get the n_th ring neighbor
        False: get the n ring neighbor
    mask : 1-D numpy array
        specify a area where the ROI is in.

    Return
    ------
    neighbors : set
        contain neighbors of the vtx
    """
    n_ring_neighbors = _get_vtx_neighbor(vtx, faces, mask)
    n_th_ring_neighbors = n_ring_neighbors.copy()

    for i in range(n-1):

        neighbors_tmp = set()
        for neighbor in n_th_ring_neighbors:
            neighbors_tmp.update(_get_vtx_neighbor(neighbor, faces, mask))

        if i == 0:
            neighbors_tmp.discard(vtx)

        n_th_ring_neighbors = neighbors_tmp.difference(n_ring_neighbors)
        n_ring_neighbors.update(n_th_ring_neighbors)

    if ordinal:
        return n_th_ring_neighbors
    else:
        return n_ring_neighbors


def _get_vtx_neighbor(vtx, faces, mask=None):
    """
    Get one vertex's 1-ring neighbor vertices

    Parameters
    ----------
    vtx : integer
        a vertex's id
    faces : numpy array
        the array of shape [n_triangles, 3]
    mask : 1-D numpy array
        specify a area where the ROI is in.

    Return
    ------
    neighbors : set
        contain neighbors of the vtx
    """
    row_indices, _ = np.where(faces == vtx)
    neighbors = set(np.unique(faces[row_indices]))
    neighbors.discard(vtx)
    if mask is not None:
        neighbor_iter = list(neighbors)
        for i in neighbor_iter:
            if mask[i] == 0:
                neighbors.discard(i)

    return neighbors


def mesh2edge_list(faces, n=1, ordinal=False, vtx_signal=None,
                   weight_type=('dissimilar', 'euclidean'), weight_normalization=False):
    """
    get edge_list according to mesh's geometry and vtx_signal
    The edge_list can be used to create graph or adjacent matrix

    Parameters
    ----------
    faces : a array with shape (n_triangles, 3)
    n : integer
        specify which ring should be got
    ordinal : bool
        True: get the n_th ring neighbor
        False: get the n ring neighbor
    vtx_signal : numpy array
        NxM array, N is the number of vertices,
        M is the number of measurements and time points.
    weight_type : (str1, str2)
        The rule used for calculating weights
        such as ('dissimilar', 'euclidean') and ('similar', 'pearson correlation')
    weight_normalization : bool
        If it is False, do nothing.
        If it is True, normalize weights to [0, 1].
            After doing this, greater the weight is, two vertices of the edge are more related.

    Returns
    -------
    row_ind : list
        row indices of edges
    col_ind : list
        column indices of edges
    edge_data : list
        edge data of the edges-zip(row_ind, col_ind)
    """

    n_ring_neighbors = get_n_ring_neighbor(faces, n, ordinal)

    row_ind = [i for i, neighbors in enumerate(n_ring_neighbors) for v_id in neighbors]
    col_ind = [v_id for neighbors in n_ring_neighbors for v_id in neighbors]
    if vtx_signal is None:
        # create unweighted edges
        n_edge = len(row_ind)  # the number of edges
        edge_data = np.ones(n_edge)
    else:
        # calculate weights according to mesh's geometry and vertices' signal
        if weight_type[0] == 'dissimilar':
            edge_data = [pdist(np.c_[vtx_signal[i], vtx_signal[j]].T,
                               metric=weight_type[1])[0] for i, j in zip(row_ind, col_ind)]

            if weight_normalization:
                max_dissimilar = np.max(edge_data)
                min_dissimilar = np.min(edge_data)
                edge_data = [(max_dissimilar-dist)/(max_dissimilar-min_dissimilar) for dist in edge_data]
        elif weight_type[0] == 'similar':
            if weight_type[1] == 'pearson correlation':
                edge_data = [pearsonr(vtx_signal[i], vtx_signal[j])[0] for i, j in zip(row_ind, col_ind)]
            else:
                raise TypeError("The weight_type-{} is not supported now!".format(weight_type))

            if weight_normalization:
                max_similar = np.max(edge_data)
                min_similar = np.min(edge_data)
                edge_data = [(simi-min_similar)/(max_similar-min_similar) for simi in edge_data]
        else:
            raise TypeError("The weight_type-{} is not supported now!".format(weight_type))

    return row_ind, col_ind, edge_data


def mesh2adjacent_matrix(faces, n=1, ordinal=False, vtx_signal=None,
                         weight_type=('dissimilar', 'euclidean'), weight_normalization=False):
    """
    get adjacent matrix according to mesh's geometry and vtx_signal

    Parameters
    ----------
    faces : a array with shape (n_triangles, 3)
    n : integer
        specify which ring should be got
    ordinal : bool
        True: get the n_th ring neighbor
        False: get the n ring neighbor
    vtx_signal : numpy array
        NxM array, N is the number of vertices,
        M is the number of measurements and time points.
    weight_type : (str1, str2)
        The rule used for calculating weights
        such as ('dissimilar', 'euclidean') and ('similar', 'pearson correlation')
    weight_normalization : bool
        If it is False, do nothing.
        If it is True, normalize weights to [0, 1].
            After doing this, greater the weight is, two vertices of the edge are more related.

    Returns
    -------
    adjacent_matrix : coo matrix
    """

    n_vtx = np.max(faces) + 1
    row_ind, col_ind, edge_data = mesh2edge_list(faces, n, ordinal, vtx_signal,
                                                 weight_type, weight_normalization)
    adjacent_matrix = sparse.coo_matrix((edge_data, (row_ind, col_ind)), (n_vtx, n_vtx))

    return adjacent_matrix


def mesh2graph(faces, n=1, ordinal=False, vtx_signal=None,
               weight_type=('dissimilar', 'euclidean'), weight_normalization=False):
    """
    create graph according to mesh's geometry and vtx_signal

    Parameters
    ----------
    faces : a array with shape (n_triangles, 3)
    n : integer
        specify which ring should be got
    ordinal : bool
        True: get the n_th ring neighbor
        False: get the n ring neighbor
    vtx_signal : numpy array
        NxM array, N is the number of vertices,
        M is the number of measurements and time points.
    weight_type : (str1, str2)
        The rule used for calculating weights
        such as ('dissimilar', 'euclidean') and ('similar', 'pearson correlation')
    weight_normalization : bool
        If it is False, do nothing.
        If it is True, normalize weights to [0, 1].
            After doing this, greater the weight is, two vertices of the edge are more related.

    Returns
    -------
    graph : nx.Graph
    """

    row_ind, col_ind, edge_data = mesh2edge_list(faces, n, ordinal, vtx_signal,
                                                 weight_type, weight_normalization)
    graph = Graph()
    # add_weighted_edges_from is faster than from_scipy_sparse_matrix and from_numpy_matrix
    # add_weighted_edges_from is also faster than default constructor
    # To get more related information, please refer to
    # http://stackoverflow.com/questions/24681677/transform-csr-matrix-into-networkx-graph
    graph.add_weighted_edges_from(zip(row_ind, col_ind, edge_data))

    return graph


def binary_shrink(bin_data, faces, n=1, n_ring_neighbors=None):
    """
    shrink bin_data

    Parameters
    ----------
    bin_data : 1-D numpy array
        Each array index is corresponding to vertex id in the faces.
        Each element is a bool.
    faces : numpy array
        the array of shape [n_triangles, 3]
    n : integer
        specify which ring should be got
    n_ring_neighbors : list
        If this parameter is not None, two parameters ('faces', 'n') will be ignored.
        It is used to save time when someone repeatedly uses the function with
            a same n_ring_neighbors which can be got by get_n_ring_neighbor.
        The indices are vertices' id of a mesh.
        One index's corresponding element is a collection of vertices which connect with the index.

    Return
    ------
    new_data : 1-D numpy array with bool elements
        The output of the bin_data after binary shrink
    """
    if bin_data.dtype != np.bool:
        raise TypeError("The input dtype must be bool")
    vertices = np.where(bin_data)[0]
    new_data = np.zeros_like(bin_data)

    if n_ring_neighbors is None:
        n_ring_neighbors = get_n_ring_neighbor(faces, n)

    for v_id in vertices:
        neighbors_values = [bin_data[_] for _ in n_ring_neighbors[v_id]]
        if np.all(neighbors_values):
            new_data[v_id] = True

    return new_data


def binary_expand(bin_data, faces, n=1, n_ring_neighbors=None):
    """
    expand bin_data

    Parameters
    ----------
    bin_data : 1-D numpy array
        Each array index is corresponding to vertex id in the faces.
        Each element is a bool.
    faces : numpy array
        the array of shape [n_triangles, 3]
    n : integer
        specify which ring should be got
    n_ring_neighbors : list
        If this parameter is not None, two parameters ('faces' and 'n') will be ignored.
        It is used to save time when someone repeatedly uses the function with
            a same n_ring_neighbors which can be got by get_n_ring_neighbor.
        The indices are vertices' id of a mesh.
        One index's corresponding element is a collection of vertices which connect with the index.

    Return
    ------
    new_data : 1-D numpy array with bool elements
        The output of the bin_data after binary expand
    """
    if bin_data.dtype != np.bool:
        raise TypeError("The input dtype must be bool")
    vertices = np.where(bin_data)[0]
    new_data = bin_data.copy()

    if n_ring_neighbors is None:
        n_ring_neighbors = get_n_ring_neighbor(faces, n)

    for v_id in vertices:
        neighbors_values = [bin_data[_] for _ in n_ring_neighbors[v_id]]
        if not np.all(neighbors_values):
            new_data[list(n_ring_neighbors[v_id])] = True

    return new_data


def label_edge_detection(data, faces, edge_type="inner", neighbors=None):
    """
    edge detection for labels

    Parameters
    ----------
    data : 1-D numpy array
        Each array index is corresponding to vertex id in the faces.
        Each element is a label id.
    faces : numpy array
        the array of shape [n_triangles, 3]
    edge_type : str
        "inner" means inner edges of labels.
        "outer" means outer edges of labels.
        "both" means both of them in one array
        "split" means returning inner and outer edges in two arrays respectively
    neighbors : list
        If this parameter is not None, a parameters ('faces') will be ignored.
        It is used to save time when someone repeatedly uses the function with
            a same neighbors which can be got by get_n_ring_neighbor.
        The indices are vertices' id of a mesh.
        One index's corresponding element is a collection of vertices which connect with the index.

    Return
    ------
    inner_data : 1-D numpy array
        the inner edges of the labels
    outer_data : 1-D numpy array
        the outer edges of the labels
        It's worth noting that outer_data's element values may
            be not strictly corresponding to labels' id when
            there are some labels which are too close.
    """
    # data preparation
    vertices = np.nonzero(data)[0]
    inner_data = np.zeros_like(data)
    outer_data = np.zeros_like(data)
    if neighbors is None:
        neighbors = get_n_ring_neighbor(faces)

    # look for edges
    for v_id in vertices:
        neighbors_values = [data[_] for _ in neighbors[v_id]]
        if min(neighbors_values) != max(neighbors_values):
            if edge_type in ("inner", "both", "split"):
                inner_data[v_id] = data[v_id]
            if edge_type in ("outer", "both", "split"):
                outer_vtx = [vtx for vtx in neighbors[v_id] if data[v_id] != data[vtx]]
                outer_data[outer_vtx] = data[v_id]

    # return results
    if edge_type == "inner":
        return inner_data
    elif edge_type == "outer":
        return outer_data
    elif edge_type == "both":
        return inner_data + outer_data
    elif edge_type == "split":
        return inner_data, outer_data
    else:
        raise ValueError("The argument 'edge_type' must be one of the (inner, outer, both, split)")


class LabelAssessment(object):

    @staticmethod
    def transition_level(label, data, faces, neighbors=None):
        """
        Calculate the transition level on the region's boundary.
        The result is regarded as the region's assessed value.
        Adapted from (Chantal et al. 2002).

        Parameters
        ----------
        label : list
            a collection of vertices with the label
        data : numpy array
            scalar data with the shape (#vertices, #features)
        faces : numpy array
            the array of shape [n_triangles, 3]
        neighbors : list
        If this parameter is not None, a parameters ('faces') will be ignored.
        It is used to save time when someone repeatedly uses the function with
            a same neighbors which can be got by get_n_ring_neighbor.
        The indices are vertices' id of a mesh.
        One index's corresponding element is a collection of vertices which connect with the index.

        Return
        ------
        assessed_value : float
            Larger is often better.
        """
        label_data = np.zeros_like(data, dtype=np.int8)
        label_data[label] = 1

        inner_data = label_edge_detection(label_data, faces, "inner", neighbors)
        inner_edge = np.nonzero(inner_data)[0]

        count = 0
        sum_tmp = 0
        for vtx_i in inner_edge:
            for vtx_o in neighbors[vtx_i]:
                if label_data[vtx_o] == 0:
                    couple_signal = np.r_[np.atleast_2d(data[vtx_i]), np.atleast_2d(data[vtx_o])]
                    sum_tmp += pdist(couple_signal)[0]
                    count += 1
        return sum_tmp / float(count)


if __name__ == '__main__':
    from nibabel.freesurfer import read_geometry
    from froi.io.surf_io import read_scalar_data
    from networkx import Graph
    from graph_tool import graph2parcel, node_attr2array
    import nibabel as nib

    coords, faces = read_geometry('/nfs/t1/nsppara/corticalsurface/fsaverage5/surf/rh.inflated')
    scalar = read_scalar_data('/nfs/t3/workingshop/chenxiayu/data/region-growing-froi/S1/surf/'
                              'rh_zstat1_1w_fracavg.mgz')
    # faces = np.array([[1, 2, 3], [0, 1, 3]])
    # scalar = np.array([[1], [2], [3], [4]])

    graph = mesh2graph(faces, vtx_signal=scalar, weight_normalization=True)

    graph, parcel_neighbors = graph2parcel(graph, n=5000)
    labels = [attrs['label'] for attrs in graph.node.values()]
    print 'finish ncut!'
    labels = np.unique(labels)
    print len(labels)
    print np.max(labels)

    arr = node_attr2array(graph, ('label',))
    # zero_idx = np.where(map(lambda x: x not in parcel_neighbors[800], arr))
    # arr[zero_idx[0]] = 0
    nib.save(nib.Nifti1Image(arr, np.eye(4)), '/nfs/t3/workingshop/chenxiayu/test/cxy/ncut_label_1w_5000.nii')
