#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import sys
import numpy as np
from PyQt4 import QtCore, QtGui

from froi.core.dataobject import Hemisphere
from treemodel import TreeModel

if __name__ == '__main__':
    db_dir = r'/nfs/t1/nsppara/corticalsurface'

    app = QtGui.QApplication(sys.argv)

    # model init
    hemisphere_list = []
    surf1 = os.path.join(db_dir, 'S0001', 'surf', 'lh.white')
    surf2 = os.path.join(db_dir, 'S0001', 'surf', 'rh.white')
    s1 = os.path.join(db_dir, 'S0001', 'surf', 'lh.thickness')
    s2 = os.path.join(db_dir, 'S0001', 'surf', 'lh.curv')
    s3 = os.path.join(db_dir, 'S0001', 'surf', 'rh.curv')

    h1 = Hemisphere(surf1)
    h1.load_overlay(s1)
    h1.load_overlay(s2)
    h2 = Hemisphere(surf2)
    h2.load_overlay(s3)

    hemisphere_list.append(h1)
    hemisphere_list.append(h2)

    for h in hemisphere_list:
        print h.name
        for ol in h.overlay_list:
            print ol.name

    model = TreeModel(hemisphere_list)

    # View init
    view = QtGui.QTreeView()
    view.setModel(model)
    view.setWindowTitle("Hemisphere Tree Model")
    #view.setRootIsDecorated(True)
    view.show()
    sys.exit(app.exec_())

