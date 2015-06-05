# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import operator
import xml.dom.minidom
import nibabel as nib

def xmlread_label(prefix, xmlname, tagname, index):
    """
    read specific label from xml file according to tag and index.

    """
    dom=xml.dom.minidom.parse(prefix + xmlname)
    root = dom.documentElement
    tags = root.getElementsByTagName(tagname)
    tag = tags[index]
    return tag.firstChild.data

def xmlread_labellist(prefix, xmlname, tagname):
    """
    read specific label list from xml file according to tag.

    """
    labellist = []
    dom=xml.dom.minidom.parse(prefix + xmlname)
    root = dom.documentElement
    tags = root.getElementsByTagName(tagname)
    for i in range(len(tags)):
        labellist.append(tags[i].firstChild.data)
    return labellist

def extract_atlasprob(prefix, image, x, y, z):
    """
    extract atlas probability values according to coordinate.

    """
    atlas = nib.load(prefix + image)
    atlasdata = atlas.get_data()
    problist = atlasdata[x, y, z, :]/100.0
    return problist

def sorting(labellist, problist):
    """
    sorting the label according to probability value.

    """
    if (len(labellist)!=len(problist)):
        raise 'the length of label and value can not match'
    result = ''
    outputlist = []
    for i in range(len(problist)):
        if (problist[i] != 0):
            outputlist.append([problist[i],labellist[i]])
    if (len(outputlist)==0):
        result = 'No Labels\n'
        return result
    outputlist = sorted(outputlist, key= operator.itemgetter(0))
    outputlist.reverse()
    for i in range(len(outputlist)):
        result += (str(outputlist[i][0])+' '+outputlist[i][1]+'\n')
    return result
