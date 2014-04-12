# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import froi


def get_icon_dir():
    """
    Get directory which contains icons.

    """
    pjoin = os.path.join
    apath = os.path.abspath
    froi_dir = os.path.dirname(froi.__file__)
    base_dir = apath(pjoin(froi_dir, os.pardir))
    base_dir = apath(pjoin(base_dir, os.pardir))
    if not os.path.exists(pjoin(base_dir, 'data')):
        icon_dir = pjoin(froi_dir,'gui', 'icon')
    else:
        icon_dir = pjoin(base_dir, 'icon')
    return icon_dir

def get_data_dir():
    """
    Get data directory path.

    """
    pjoin = os.path.join
    apath = os.path.abspath
    froi_dir = os.path.dirname(froi.__file__)
    base_dir = apath(pjoin(froi_dir, os.pardir))
    base_dir = apath(pjoin(base_dir, os.pardir))
    if not os.path.exists(pjoin(base_dir, 'data')):
        data_dir = pjoin(froi_dir,'data')
    else:
        data_dir = pjoin(base_dir,'data')
    return data_dir

