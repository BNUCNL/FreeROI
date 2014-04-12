# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import scipy.ndimage as ndimage
import skimage.morphology as skmorph

from imtool import inverse_transformation

def distance_transformation(data):
    dist = ndimage.distance_transform_edt(data)
    return -dist

def gradient_transformation(data):
    gx = ndimage.sobel(data, 0)
    gy = ndimage.sobel(data, 1)
    gz = ndimage.sobel(data, 2)
    grad = np.sqrt(gx**2 + gy**2 + gz**2)
    return grad

def watershed(data, sigma, thresh, seeds=None, sfx=inverse_transformation):
    thresh = thresh > 0 and thresh
    if thresh == 0:
        mask = data > thresh 
    else:
        mask = data >= thresh
    data = ndimage.gaussian_filter(data, sigma)
    if seeds is None:
        # using unmasked data to get local maximum
        seeds = is_local_maximum(data)
    # mask out those smaller than threshold
    seeds[~mask] = 0

    se = ndimage.generate_binary_structure(3, 3)
    markers = ndimage.label(seeds, se)[0]
    if sfx == distance_transformation:
        seg_input = sfx(mask)
    else:
        seg_input = sfx(data)
    result = skmorph.watershed(seg_input, markers, mask=mask)
    return markers, seg_input, result

def is_local_maximum(image, labels=None, footprint=None):
    """
    Return a boolean array of points that are local maxima
 
    Parameters
    ----------
    image: ndarray (2-D, 3-D, ...)
        intensity image
        
    labels: ndarray, optional 
        find maxima only within labels. Zero is reserved for background.
    
    footprint: ndarray of bools, optional
        binary mask indicating the neighborhood to be examined
        `footprint` must be a matrix with odd dimensions, the center is taken 
        to be the point in question.

    Returns
    -------
    result: ndarray of bools
        mask that is True for pixels that are local maxima of `image`

    Notes
    -----
    This function is copied from watershed module in CellProfiler.

    This module implements a watershed algorithm that apportions pixels into
    marked basins. The algorithm uses a priority queue to hold the pixels
    with the metric for the priority queue being pixel value, then the time
    of entry into the queue - this settles ties in favor of the closest marker.

    Some ideas taken from
    Soille, "Automated Basin Delineation from Digital Elevation Models Using
    Mathematical Morphology", Signal Processing 20 (1990) 171-182.

    The most important insight in the paper is that entry time onto the queue
    solves two problems: a pixel should be assigned to the neighbor with the
    largest gradient or, if there is no gradient, pixels on a plateau should
    be split between markers on opposite sides.

    Originally part of CellProfiler, code licensed under both GPL and BSD licenses.
    Website: http://www.cellprofiler.org

    Copyright (c) 2003-2009 Massachusetts Institute of Technology
    Copyright (c) 2009-2011 Broad Institute
    All rights reserved.

    Original author: Lee Kamentsky

    Examples
    --------
    >>> image = np.zeros((4, 4))
    >>> image[1, 2] = 2
    >>> image[3, 3] = 1
    >>> image
    array([[ 0.,  0.,  0.,  0.],
           [ 0.,  0.,  2.,  0.],
           [ 0.,  0.,  0.,  0.],
           [ 0.,  0.,  0.,  1.]])
    >>> is_local_maximum(image)
    array([[ True, False, False, False],
           [ True, False,  True, False],
           [ True, False, False, False],
           [ True,  True, False,  True]], dtype='bool')
    >>> image = np.arange(16).reshape((4, 4))
    >>> labels = np.array([[1, 2], [3, 4]])
    >>> labels = np.repeat(np.repeat(labels, 2, axis=0), 2, axis=1)
    >>> labels
    array([[1, 1, 2, 2],
           [1, 1, 2, 2],
           [3, 3, 4, 4],
           [3, 3, 4, 4]])
    >>> image
    array([[ 0,  1,  2,  3],
           [ 4,  5,  6,  7],
           [ 8,  9, 10, 11],
           [12, 13, 14, 15]])
    >>> is_local_maximum(image, labels=labels)
    array([[False, False, False, False],
           [False,  True, False,  True],
           [False, False, False, False],
           [False,  True, False,  True]], dtype='bool')
    """
    if labels is None:
        labels = np.ones(image.shape, dtype=np.uint8)
    if footprint is None:
        footprint = np.ones([3] * image.ndim, dtype=np.uint8)
    assert((np.all(footprint.shape) & 1) == 1)
    footprint = (footprint != 0)
    footprint_extent = (np.array(footprint.shape)-1) // 2
    if np.all(footprint_extent == 0):
        return labels > 0
    result = (labels > 0).copy()
    #
    # Create a labels matrix with zeros at the borders that might be
    # hit by the footprint.
    #
    big_labels = np.zeros(np.array(labels.shape) + footprint_extent*2,
                          labels.dtype)
    big_labels[[slice(fe,-fe) for fe in footprint_extent]] = labels
    #
    # Find the relative indexes of each footprint element
    #
    image_strides = np.array(image.strides) // image.dtype.itemsize
    big_strides = np.array(big_labels.strides) // big_labels.dtype.itemsize
    result_strides = np.array(result.strides) // result.dtype.itemsize
    footprint_offsets = np.mgrid[[slice(-fe,fe+1) for fe in footprint_extent]]
    
    fp_image_offsets = np.sum(image_strides[:, np.newaxis] *
                              footprint_offsets[:, footprint], 0)
    fp_big_offsets = np.sum(big_strides[:, np.newaxis] *
                            footprint_offsets[:, footprint], 0)
    #
    # Get the index of each labeled pixel in the image and big_labels arrays
    #
    indexes = np.mgrid[[slice(0,x) for x in labels.shape]][:, labels > 0]
    image_indexes = np.sum(image_strides[:, np.newaxis] * indexes, 0)
    big_indexes = np.sum(big_strides[:, np.newaxis] * 
                         (indexes + footprint_extent[:, np.newaxis]), 0)
    result_indexes = np.sum(result_strides[:, np.newaxis] * indexes, 0)
    #
    # Now operate on the raveled images
    #
    big_labels_raveled = big_labels.ravel()
    image_raveled = image.ravel()
    result_raveled = result.ravel()
    #
    # A hit is a hit if the label at the offset matches the label at the pixel
    # and if the intensity at the pixel is greater or equal to the intensity
    # at the offset.
    #
    for fp_image_offset, fp_big_offset in zip(fp_image_offsets, fp_big_offsets):
        same_label = (big_labels_raveled[big_indexes + fp_big_offset] ==
                      big_labels_raveled[big_indexes])
        less_than = (image_raveled[image_indexes[same_label]] <
                     image_raveled[image_indexes[same_label]+ fp_image_offset])
        result_raveled[result_indexes[same_label][less_than]] = False
        
    return result
