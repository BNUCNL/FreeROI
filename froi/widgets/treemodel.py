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
        """Reture the index of item in the model."""
        if not self.hasIndex(row, column, parent):
            print 'index - not has index'
            return QModelIndex()

        if not column:
            parentItem = self._data[row]
            print 'index - create index'
            return self.createIndex(row, 0, parentItem)
        else:
            parentItem = parent.internalPointer()
            childItem_idx = parentItem.overlay_idx[column-1]
            childItem = parentItem.overlay_list[childItem_idx]
            if childItem:
                print 'index - create index'
                return self.createIndex(row, column, childItem)
            else:
                print 'index - invalid childitem'
                return QModelIndex()

    def parent(self, index):
        """Return the parent of the model item with the given index."""
        if not index.isValid():
            print 'parent - invalid index'
            return QModelIndex()

        if index.column() > 0:
            print 'parent - find parent'
            return self.createIndex(index.row(), 0, self._data[index.row()])
        else:
            print 'parent - no parent'
            return QModelIndex()

    def rowCount(self, parent):
        """Return the number of rows for display."""
        if parent.isValid():
            return len(self._data[parent.row()].overlay_list)
        else:
            return len(self._data)

    def columnCount(self, parent):
        """Return the number of overlays in a hemispheres."""
        #if parent.isValid():
        #    if not parent.column():
        #        return len(self._data[parent.row()].overlay_list)
        #    else:
        #        return 1
        #else:
        #    return 1
        return 1
        
    def data(self, index, role):
        """Return specific data."""
        if not index.isValid():
            print 'data - invalid index'
            return None

        if role != Qt.DisplayRole:
            print 'data - invalid role'
            return None

        item = index.internalPointer()
        print item.name
        return item.name

    def flags(self, index):
        if not index.isValid():
            print 'no flags'
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            print 'header data - ok'
            return 'Name'
        print 'header data - None'
        return None

