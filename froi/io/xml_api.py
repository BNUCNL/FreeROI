# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import xml.dom.minidom

def get_file_name(path, postfix):
    """
    get file name with certain postfix automatically

    Parameters
    ----------
    path:
        The path.
    postfix:
        postfix of file, such as ".xml"
    """
    f_list = os.listdir(path)
    for i in f_list:
        if os.path.splitext(i)[1]!=postfix:
            f_list.remove(i)
    return f_list

def get_info(path, f_list, tagname):
    """
    get specific information from xml file according to the name of tag.
    return the information list.

    Parameters
    ----------
    path:
        The path of xml file.
    f_list:
        The xml file name list
    tagname:
        The name of target tag.
    """
    infolist = list()
    for i in f_list:
        dom=xml.dom.minidom.parse(path+i)
        root = dom.documentElement
        tags = root.getElementsByTagName(tagname)
        subinfo = list()
        for j in range(len(tags)):
            subinfo.append(tags[j].firstChild.data)
        infolist.append(subinfo)
    return infolist
