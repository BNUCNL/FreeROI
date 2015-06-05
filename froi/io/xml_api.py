# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
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
    plist, llist = [], []
    for i in range(len(problist)):
        if (problist[i] != 0):
            plist.append(problist[i])
            llist.append(labellist[i])
    if (len(plist)==0):
        result = 'No Labels\n'
        return result
    for i in range(len(plist)):
        for j in range(i+1,len(plist)):
            if (plist[i]<plist[j]):
                plist[i], plist[j] = plist[j], plist[i]
                llist[i], llist[j] = llist[j], llist[i]
    for i in range(len(plist)):
        result += (str(plist[i])+' '+llist[i]+'\n')
    return result