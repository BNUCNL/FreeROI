# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Implementation of a Tree model for surface data display.

"""

import numpy as np
from PyQt4.QtCore import *

class TreeModel(QAbstractItemModel):
    """Definition of class TreeModel."""
    def __init__(self, hemisphere_list, parent=None):
        """Initialize an instance."""
        super(TreeModel, self).__init__(parent)
        
        self._data = hemisphere_list

    def index(self, row, column, parent):
        """Return the index of item in the model."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self._data[row]
            return self.createIndex(row, column, parentItem)
        else:
            parentItem = parent.internalPointer()
            childItem_idx = parentItem.overlay_idx[
                                parentItem.overlay_count()-1-row]
            childItem = parentItem.overlay_list[childItem_idx]
            if childItem:
                return self.createIndex(row, column, childItem)
            else:
                return QModelIndex()

    def parent(self, index):
        """Return the parent of the model item with the given index."""
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()
        if item in self._data:
            return QModelIndex()
        else:
            for hemi in self._data:
                if item in hemi.overlay_list:
                    return self.createIndex(self._data.index(hemi), 0, hemi)

    def rowCount(self, parent):
        """Return the number of rows for display."""
        if parent.isValid():
            if parent.internalPointer() in self._data:
                return self._data[parent.row()].overlay_count()
            else:
                return 0
        else:
            return len(self._data)

    def columnCount(self, parent):
        """Return the number of overlays in a hemispheres."""
        return 1
        
    def data(self, index, role):
        """Return specific data."""
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()
        return item.name

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return 'Name'
        return None

