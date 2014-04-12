# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Some basic functions for image construction

"""

import sys as _sys
import numpy as _np
from PyQt4 import QtGui as _qt

from qimageview import qimageview as _qimageview

if _sys.byteorder == 'little':
    _bgra = (0, 1, 2, 3)
else:
    _bgra = (3, 2, 1, 0)

bgra_dtype = _np.dtype({'b': (_np.uint8, _bgra[0], 'blue'),
                        'g': (_np.uint8, _bgra[1], 'green'),
                        'r': (_np.uint8, _bgra[2], 'red'),
                        'a': (_np.uint8, _bgra[3], 'alpha')})

def gray(array, alpha):
    """
    Return a rgba array which color ranges from black to white.
    
    """
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    array[array<=0] = 0
    array[array>255] = 255
    new_array[..., 0] = array
    new_array[..., 1] = array
    new_array[..., 2] = array
    new_array[..., 3] = alpha * array.clip(0, 1)
    
    return new_array

def red2yellow(array, alpha):
    """
    Return a rgba array which color ranges from red to yellow.
    
    """
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    array[array<=0] = 0
    array[array>255] = 255
    new_array[..., 0] = 255 * array.clip(0, 1)
    new_array[..., 1] = array
    new_array[..., 2] = 0
    new_array[..., 3] = alpha * array.clip(0, 1)
    
    return new_array

def blue2cyanblue(array, alpha):
    """
    Return a rgba array which color ranges from blue to cyanblue.
    
    """
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    array[array<=0] = 0
    array[array>255] = 255
    new_array[..., 0] = 0
    new_array[..., 1] = array
    new_array[..., 2] = 255 * array.clip(0, 1)
    new_array[..., 3] = alpha * array.clip(0, 1)

    return new_array

def red(array, alpha):
    """
    Return a whole red rgba array.
    
    """
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    new_array[..., 0] = 255 * array.clip(0, 1)
    new_array[..., 1] = 0
    new_array[..., 2] = 0
    new_array[..., 3] = alpha * array.clip(0, 1)
    
    return new_array

def green(array, alpha):
    """
    Return a whole green rgba array.
    
    """
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    new_array[..., 0] = 0
    new_array[..., 1] = 255 * array.clip(0, 1)
    new_array[..., 2] = 0
    new_array[..., 3] = alpha * array.clip(0, 1)

    return new_array

def blue(array, alpha):
    """
    Return a whole blue rgba array.
    
    """
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    new_array[..., 0] = 0
    new_array[..., 1] = 0
    new_array[..., 2] = 255 * array.clip(0, 1)
    new_array[..., 3] = alpha * array.clip(0, 1)
    
    return new_array

def single_roi(array, alpha, roi):
    """
    Return a single roi view array.

    """
    color = (70, 70, 70)
    h, w = array.shape
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    if roi is None or roi == 0:
        return new_array
    mask = array == roi
    new_array[mask, 0] = color[0]
    new_array[mask, 1] = color[1]
    new_array[mask, 2] = color[2]
    new_array[mask, 3] = alpha 
    return new_array

def _normalize255(array, normalize, scale_length=255.0):
    if not normalize:
        return array

    if normalize is True:
        normalize = array.min(), array.max()
    elif _np.isscalar(normalize):
        normalize = (0, normalize)
    elif isinstance(normalize, tuple) and (normalize[0] == normalize[1]):
        normalize = array.min(), array.max()
    nmin, nmax = normalize

    if nmin:
        array = array - nmin

    if nmax == nmin:
        return _np.round(array)
    else:
        scale =  scale_length / (nmax - nmin)
        if scale != 1.0:
            array = array * scale
        array[_np.logical_and(array > 0, array < 1)] = 1
        return _np.round(array)

def gray2qimage(array, normalize=False):
    """Convert a 2D numpy array 'array' into a 8-bit, indexed QImage with
    a specific colormap. The first dimension represents the vertical image
    axis.

    The parameter 'normalize' can be used to normalize an image's value range
    to 0 ~ 255:

        normalize = (nmin, nmax):
         scale & clip image values from nmin..nmax to 0..255

        normalize = nmax:
         lets nmin default to zero, i.e. scale & clip the range 0..nmax to
         0..255

        normalize = True:
         scale image values to 0..255 (same as passing (array.min(), 
         array.max()))

    If the source array 'array' contains masked values, the result will have 
    only 255 shades of gray, and one color map entry will be used to make the
    corresponding pixels transparent.


    """
    if _np.ndim(array) != 2:
        raise ValueError("gray2qimage can only convert 2D arrays")

    h, w = array.shape
    result = _qt.QImage(w, h, _qt.QImage.Format_Indexed8)

    array = _normalize255(array, normalize)

    for i in range(256):
        result.setColor(i, _qt.qRgb(i, i, i))

    _qimageview(result)[:] = array.clip(0, 255)

    return result

def byte_view(qimage, byteorder = 'little'):
    raw = _qimageview(qimage)
    result = raw.view(_np.uint8).reshape(raw.shape + (-1, ))
    if byteorder and byteorder != _sys.byteorder:
        result = result[...,::-1]
    return result

def rgb_view(qimage, byteorder='big'):
    if byteorder is None:
        byteorder = _sys.byteorder
    bytes = byte_view(qimage, byteorder)
    if bytes.shape[2] != 4:
        raise ValueError, "For rgb_view, the image must have 32 bit pixel" + \
                " size (use RGB32, ARGB32, or ARGB32_Premultiplied)"

    if byteorder == 'little':
        return bytes[..., :3]
    else:
        return bytes[..., 1:]

def alpha_view(qimage):
    bytes = byte_view(qimage, byteorder = None)
    if bytes.shape[2] != 4:
        raise ValueError, "For alpha_view, the image must have 32 bit pixel" + \
                        " size (use RGB32, ARGB32, or ARGB32_Premultiplied)"
    return bytes[..., _bgra[3]]

def array2qrgba(array, alpha, colormap, normalize=False, roi=None):
    """Convert a 2D-array into a 3D-array containing rgba value."""
    if _np.ndim(array) != 2:
        raise ValueError("array2qrgb can only convert 2D array")

    if isinstance(colormap, str):
        if colormap != 'rainbow':
            if colormap != 'single ROI':
                array = _normalize255(array, normalize)
                if colormap == 'gray':
                    new_array = gray(array, alpha)
                elif colormap == 'red2yellow':
                    new_array = red2yellow(array, alpha)
                elif colormap == 'blue2cyanblue':
                    new_array = blue2cyanblue(array, alpha)
                elif colormap == 'red':
                    new_array = red(array, alpha)
                elif colormap == 'green':
                    new_array = green(array, alpha)
                elif colormap == 'blue':
                    new_array = blue(array, alpha)
            else:
                new_array = single_roi(array, alpha, roi)
        else:
            if _np.isscalar(normalize):
                new_array = array.clip(0, array.max())
                new_array[array < 0] = 0
                new_array[array > normalize] = 0
            elif isinstance(normalize, tuple):
                new_array = array.clip(0, array.max())
                new_array[array < normalize[0]] = 0
                new_array[array > normalize[1]] = 0
            else:
                new_array = array.clip(0, array.max())
                new_array[array < 0] = 0
            h, w = new_array.shape
            R, G, B = 41, 61, 83
            fst_norm = 100000.0
            new_array_raw = _normalize255(new_array,
                                          normalize,
                                          scale_length=fst_norm)
            new_array_R = _normalize255(new_array_raw % R,
                                        (0, R),
                                        scale_length=254.0)
            new_array_G = _normalize255(new_array_raw % G,
                                        (0, G),
                                        scale_length=254.0)
            new_array_B = _normalize255(new_array_raw % B,
                                        (0, B),
                                        scale_length=254.0)
            new_array2 = _np.zeros((h, w, 4), dtype=_np.uint8)
            add_ = new_array.clip(0, 1)
            new_array2[..., 0] = new_array_R + add_ 
            new_array2[..., 1] = new_array_G + add_
            new_array2[..., 2] = new_array_B + add_
            new_array2[..., 3] = alpha * _np.sum(new_array2, 2).clip(0, 1)
            #_np.set_printoptions(threshold=1000000)
            new_array = new_array2
    else:
        if _np.isscalar(normalize):
            new_array = array.clip(0, array.max())
            new_array[array < 0] = 0
            new_array[array > normalize] = 0
        elif isinstance(normalize, tuple):
            new_array = array.clip(0, array.max())
            new_array[array < normalize[0]] = 0
            new_array[array > normalize[1]] = 0
        else:
            new_array = array.clip(0, array.max())
            new_array[array < 0] = 0
        values = colormap.keys()
        values = [int(item) for item in values]
        h, w = new_array.shape
        new_array2 = _np.zeros((h, w, 4), dtype=_np.uint8)
        for item in values:
            new_array2[new_array==item] = [colormap[item][0],
                                           colormap[item][1],
                                           colormap[item][2],
                                           0]
        new_array2[..., 3] = alpha * _np.sum(new_array2, 2).clip(0, 1)
        new_array = new_array2

    return new_array

def qcomposition(array_list):
    """Composite several qrgba arrays into one."""
    if not len(array_list):
        raise ValueError('Input array list cannot be empty.')
    if _np.ndim(array_list[0]) != 3:
        raise ValueError('RGBA array must be 3D.')

    h, w, channel = array_list[0].shape
    result = _np.array(array_list[0][..., :3], dtype=_np.int64)
    for index in range(1, len(array_list)):
        item = _np.array(array_list[index], dtype=_np.int64)
        alpha_array = _np.tile(item[..., -1].reshape((-1, 1)), (1, 1, 3))
        alpha_array = alpha_array.reshape((h, w, 3))
        result = item[..., :3] * alpha_array + result * \
                (255 - alpha_array)
        result = result / 255
    result = _np.array(result, dtype=_np.uint8)
    return result

def composition(dest, source):
    """Save result in place
    
    Note
    ----
    The dest is a rgb image, while the source is a rgba image
    """
    alpha = source[...,3].reshape(source.shape[0], source.shape[1], 1).astype(_np.float)
    alpha /= 255
    source_rgb = source[...,:3].astype(_np.float)
    dest[:] = _np.uint8(source_rgb * alpha + dest.astype(_np.float) * (1 - alpha))
    return dest

def qrgba2qimage(array):
    """Convert the input array into a image."""
    if _np.ndim(array) != 3:
        raise ValueError("RGBA array must be 3D.")

    h, w, channel = array.shape
    fmt = _qt.QImage.Format_ARGB32
    result = _qt.QImage(w, h, fmt)
    rgb_view(result)[:] = array[..., :3]
    alpha = alpha_view(result)
    alpha[:] = 255
    return result

def null_image(h, w):
    """return a whole black rgba array"""
    new_array = _np.zeros((h, w, 4), dtype=_np.uint8)
    new_array[..., 3] = 255
    return new_array

