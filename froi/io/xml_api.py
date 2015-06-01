# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import xml.dom.minidom

def xmlread(xmldir, xmlname, tagname, index):
    """
    read specific data from xml file according to tag and index.

    """
    dom=xml.dom.minidom.parse(xmldir + xmlname)
    root = dom.documentElement
    tags = root.getElementsByTagName(tagname)
    tag = tags[index]
    return tag.firstChild.data

if __name__ == "__main__":
    ans = xmlread('../data/atlas/','HarvardOxford-Subcortical.xml','label',3)
    print ans;
