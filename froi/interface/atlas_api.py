# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from collections import OrderedDict

import nibabel as nib
import os


def get_nii_data(path, nii_name):
    """Get nii data."""
    img_name = nii_name + ".nii.gz"
    img = nib.load(os.path.join(path, img_name))
    img_data = img.get_data()
    return img_data

def get_atlasprob(data, x, y, z):
    """Extract atlas probability values according to coordinate.

    return a probability list.

    Parameters
    ----------
    data:
        The nii data.
    x,y,z:
        The coordinate value of target voxel.
    """
    prob = data[x, y, z, :] / 100.0
    return prob

def sorting(labellist, problist):
    """Sort the label according to probability value.

    return a string which including the sorted nonzero probability and the corresponding label.

    Parameters
    ----------
    labellist:
        The label names list.
    problist:
        The probability values list.
    """
    if (len(labellist)!=len(problist)):
        raise 'the length of label and probability can not match'
    result = ''
    dic = dict(zip(labellist, problist))
    dic = dict(filter(lambda  x:x[1] != 0, dic.items()))
    if (not dic):
        result = 'No label found!\n'
        return result
    dic = OrderedDict(sorted(dic.items(), key=lambda t:t[1], reverse=True))
    for i in range(len(dic)):
        result += (str(dic.values()[i])+' '+dic.keys()[i]+'\n')
    return result