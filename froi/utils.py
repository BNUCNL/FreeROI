# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os


def get_file_names(path, postfix):
    """Get file names with certain postfix automatically

    Parameters
    ----------
    path:
        The file path.
    postfix:
        postfix of file, such as ".xml"
    """
    flist = list()
    for i in os.listdir(path):
        if os.path.splitext(i)[1]==postfix:
            flist.append(i)
    return flist

def get_icon_dir():
    """Get directory which contains icons."""
    pjoin = os.path.join
    apath = os.path.abspath
    froi_dir = os.path.dirname(__file__)
    base_dir = apath(pjoin(froi_dir, os.pardir))
    #base_dir = apath(pjoin(base_dir, os.pardir))
    if not os.path.exists(pjoin(base_dir, 'data')):
        icon_dir = pjoin(froi_dir, 'icon')
    else:
        icon_dir = pjoin(base_dir, 'icon')
    return icon_dir

def get_data_dir():
    """Get data directory path."""
    pjoin = os.path.join
    apath = os.path.abspath
    froi_dir = os.path.dirname(__file__)
    base_dir = apath(pjoin(froi_dir, os.pardir))
    #base_dir = apath(pjoin(base_dir, os.pardir))
    if not os.path.exists(pjoin(base_dir, 'data')):
        data_dir = pjoin(froi_dir,'data')
    else:
        data_dir = pjoin(base_dir,'data')
    return data_dir

