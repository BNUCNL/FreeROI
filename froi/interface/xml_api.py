# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import xml.dom.minidom


def get_info(xmlname, tagname):
    """Get specific information from xml file according to the name of tag.

    Parameters
    ----------
    xmlname
        The xml file name
    tagname:
        The name of target tag.
    """
    infolist = list()
    dom=xml.dom.minidom.parse(xmlname)
    root = dom.documentElement
    tags = root.getElementsByTagName(tagname)
    for j in range(len(tags)):
        infolist.append(tags[j].firstChild.data)
    return infolist
