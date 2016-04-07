# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Implementation of a Tree model for surface data display.

"""

import numpy as np
from PyQt4.QtCore import *

from ..core.dataobject import Hemisphere

class TreeModel(QAbstractItemModel):
    """Definition of class TreeModel."""
    def __init__(self, hemisphere_list, parent):
        """Initialize an instance."""
        super(TreeModel, self).__init__(parent)
        
        self._data = hemisphere_list

    def index(self):
        pass

    def parnet(self):
        pass

    def rowCount(self, parent):
        """Return the number of overlays for a hemisphere."""
        if parnet.isValid():


    def columnCount(self, parent):
        """Return the number of hemispheres."""
        return len(self._data)
        
    def data(self):
        pass

