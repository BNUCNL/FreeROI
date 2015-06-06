# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from collections import OrderedDict
import xml.dom.minidom
import nibabel as nib


def get_info(filepath, tagname):
    """
    get specific information from xml file according to the name of tag.
    return the information list.

    Parameters
    ----------
    filepath:
        The path of xml file which including the xml file name.
    tagname:
        The name of target tag.

    """
    infolist = []
    dom=xml.dom.minidom.parse(filepath)
    root = dom.documentElement
    tags = root.getElementsByTagName(tagname)
    for i in range(len(tags)):
        infolist.append(tags[i].firstChild.data)
    return infolist

def extract_atlasprob(filepath, x, y, z):
    """
    extract atlas probability values according to coordinate.
    return a probability list.

    Parameters
    ----------
    filepath:
        The path of atlas file which including the niftil file name.
    x,y,z:
        The coordinate value of target voxel.

    """
    atlas = nib.load(filepath)
    atlasdata = atlas.get_data()
    problist = atlasdata[x, y, z, :]/100.0
    return problist

def sorting(labellist, problist):
    """
    sort the label according to probability value.
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
        result = 'No Labels\n'
        return result
    dic = OrderedDict(sorted(dic.items(), key=lambda t:t[1], reverse=True))
    for i in range(len(dic)):
        result += (str(dic.values()[i])+' '+dic.keys()[i]+'\n')
    return result
