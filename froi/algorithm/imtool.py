# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
from scipy import ndimage as nd
from skimage import feature as skft
from scipy.spatial import distance
from nibabel.affines import apply_affine


def mesh_3d_grid(x, y, z):
    """Create the 3D mesh grid."""
    x = np.asarray(x)
    y = np.asarray(y)
    z = np.asarray(z)
    row, col, hei = len(y), len(x), len(z)
    x = x.reshape(1, 1, col)
    y = y.reshape(1, row, 1)
    z = z.reshape(hei, 1, 1)
    X = x.repeat(row, 1)
    X = X.repeat(hei, 0)
    Y = y.repeat(col, 2)
    Y = y.repeat(hei, 0)
    Z = z.repeat(row, 1)
    Z = Z.repeat(col, 2)
    return X, Y, Z


def ball(radius, dtype=np.uint8):
    """Generate a ball structure element."""
    L_x = np.linspace(-radius[0], radius[0], 2*radius[0]+1)
    L_y = np.linspace(-radius[1], radius[1], 2*radius[1]+1)
    L_z = np.linspace(-radius[2], radius[2], 2*radius[2]+1)
    X, Y, Z = mesh_3d_grid(L_x, L_y, L_z)
    s = X**2 * 1. / (radius[0]**2) + Y**2 * 1. / radius[1]**2 + Z**2 * 1. / radius[2]**2
    return np.array(s <= 1, dtype=dtype)


def opening(src, r=2):
    """Using the opening image algrithm to process the src image."""
    se = ball(r)
    result = nd.grey_opening(src, footprint=se)
    return result


def local_maximum(data, dist=1):
    """Generate the local maxinum value in image."""
    lmax = np.zeros(data.shape)
    p = skft.peak_local_max(data, dist).T
    p = (np.array(p[0]), np.array(p[1]), np.array(p[2]))
    lmax[p] = 1
    return lmax


def roi_filtering(src, ref):
    """Filter the value using the given ref image."""
    mask = ref > 0
    all_roi = np.unique(src[mask])
    result = np.zeros(src.shape)
    for roi in all_roi:
        result[src==roi] = roi
    return result


def sphere_roi(data, x, y, z, radius, value):
    """Generate a sphere roi which center in (x, y, z)."""
    for n_x in range(x - radius[0], x + radius[0] + 1):
        for n_y in range(y - radius[1], y + radius[1] + 1):
            for n_z in range(z - radius[2], z + radius[2] + 1):
                #if n_x < 0:
                #    n_x = data.shape[0] - n_x
                #if n_y < 0:
                #    n_y = data.shape[1] - n_y
                #if n_z < 0:
                #    n_z = data.shape[2] - n_z
                n_coord = np.array((n_x, n_y, n_z))
                coord = np.array((x, y, z))
                minus = coord - n_coord
                if (np.square(minus) / np.square(np.array(radius)).astype(np.float)).sum() <= 1:
                    try:
                        data[n_x, n_y, n_z] = value
                    except IndexError:
                        pass
    return data


def cube_roi(data, x, y, z, radius, value):
    """Generate a cube roi which center in (x, y, z)."""
    for n_x in range(x - radius[0], x + radius[0] + 1):
        for n_y in range(y - radius[1], y + radius[1] + 1):
            for n_z in range(z - radius[2], z + radius[2] + 1):
                try:
                    data[n_x, n_y, n_z] = value
                except IndexError:
                    pass
                # if n_x >= 0 and n_y >= 0 and n_z >= 0:
                #    data[n_x, n_y, n_z] = value
    return data


def nonzero_coord(data):
    """Return all non-zero voxels' coordinate."""
    x, y, z = np.nonzero(data)
    coord_list = zip(x, y, z)
    value_list = [data[coord] for coord in coord_list]
    return coord_list, value_list


def binarize(data, threshold):
    """Image binarization with the given threshold"""
    return (data > threshold).astype(np.int8)


def label_edge_detection(data):
    """Detect the edge in the image with multi-labels."""
    f = nd.generate_binary_structure(len(data.shape), 1)
    # the unwanted thick bounds
    bound = (nd.grey_erosion(data, footprint=f) !=
             nd.grey_dilation(data, footprint=f)) ^ \
            (nd.binary_dilation(data.astype(np.bool)) ^ data.astype(np.bool))
    data = bound.astype(data.dtype)
    return data


def inverse_transformation(data):
    """Return a inverted image."""
    return -data


def cluster_labeling(data, threshold, conn=2):
    """Label different clusters in an image."""
    temp = data.copy()
    temp[temp <= threshold] = 0
    temp[temp > threshold] = 1
    structure = nd.generate_binary_structure(3, conn)
    labeled_array, num_features = nd.label(temp, structure)
    return labeled_array


def gaussian_smoothing(data, sigma):
    """Gaussian smoothing."""
    data = nd.gaussian_filter(data, sigma)
    return data


def intersect(source, mask):
    """An intersection action, return a new numpy array.

    New array will preserve the source data value, and mask data will be binaried as a `mask`.
    """
    # binary mask data
    mask[mask > 0] = 1
    temp = source * mask
    temp = np.rot90(temp, 3)
    return temp


def merge(a, b):
    """Merge the image a and image b. Return the merged image."""
    a_mask = a > 0
    b_mask = b > 0
    if len((a_mask & b_mask).nonzero()[0]) > 0:
        raise ValueError, 'Conflicts!'
    c = a + b
    return c


def nearest_labeling(src, tar):
    """For each temp voxel assigns the value of it's closest seed voxel."""
    srcn = src.nonzero()
    tarn = tar.nonzero()
    srcn_coord = np.column_stack((srcn[0], srcn[1], srcn[2]))
    tarn_coord = np.column_stack((tarn[0], tarn[1], tarn[2]))
    dist = distance.cdist(srcn_coord, tarn_coord)
    min_pos = np.argmin(dist, 0)
    tar[tarn] = src[srcn][min_pos]
    return tar


def region_grow(seed, source, labeling=False):
    """The region growing algrithm."""
    temp = source.copy()
    labels, n_labels = nd.label(seed)
    mask = source > 0
    labels[~mask] = 0
    dilation = nd.binary_dilation(labels, iterations=0, mask=mask)
    temp[~dilation] = 0
    if labeling:
        temp = nearest_labeling(seed, temp)
    return temp


def extract_mean_ts(source, mask):
    """Extract mean time course in a mask from source image."""
    mask[mask > 0] = 1
    mask[mask < 0] = 0
    src_dim = len(source.shape)
    if src_dim > 3:
        source_len = source.shape[3]
        data = np.zeros((source_len, 1))
        for idx in range(source_len):
            temp = source[..., idx]
            temp = temp * mask
            data[idx] = temp.sum() / mask.sum()
    else:
        source = source * mask
        data = source.sum() / mask.sum()
        data = np.array([data])
    return data


def voxel_number(source_data, voxel_value):
    """Compute the voxel number which voxel value equal to #voxel_value#."""
    if voxel_value:
        source_data[source_data!=voxel_value] = 0
        source_data[source_data==voxel_value] = 1
        return source_data.sum()
    else:
        source_data[source_data!=0] = 1
        data_shape = source_data.shape
        whole_voxel_num = data_shape[0] * data_shape[1] * data_shape[2]
        return whole_voxel_num - source_data.sum()


def cluster_stats(source_data, cluster_data, image_affine):
    """Get the cluster size, and the peak value, coordinate based on the#source_data."""
    if not source_data.shape == cluster_data.shape:
        print 'Inconsistent data shape.'
        return
    cluster_info = []
    cluster_idx = np.unique(cluster_data)
    for idx in cluster_idx:
        if idx:
            mask = cluster_data.copy()
            mask[mask!=idx] = 0
            mask[mask==idx] = 1
            extent = mask.sum()
            masked_src = source_data * mask
            max_val = masked_src.max()
            max_coord = np.unravel_index(masked_src.argmax(),
                                         masked_src.shape)
            max_coord = apply_affine(image_affine, np.array(max_coord))
            cluster_info.append([idx, max_val, max_coord[0], max_coord[1],
                                 max_coord[2], extent])
    cluster_info = np.array(cluster_info)
    cluster_extent = cluster_info[..., -1]
    cluster_info = cluster_info[np.argsort(cluster_extent)[::-1]]
    return cluster_info
