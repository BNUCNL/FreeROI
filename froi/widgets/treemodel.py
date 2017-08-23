# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Implementation of a Tree model for surface data display.

"""

from PyQt4.QtCore import *
from froi.core.dataobject import Hemisphere


class TreeModel(QAbstractItemModel):
    """Definition of class TreeModel."""
    # customized signals
    repaint_surface = pyqtSignal()

    def __init__(self, hemisphere_list, parent=None):
        """Initialize an instance."""
        super(TreeModel, self).__init__(parent)
        self._data = hemisphere_list

    def get_data(self):
        return self._data

    def index(self, row, column, parent):
        """Return the index of item in the model."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            hemi_item = self._data[row]
            return self.createIndex(row, column, hemi_item)
        else:
            hemi_item = parent.internalPointer()
            if hemi_item in self._data:
                ol_item = hemi_item.overlay_list[hemi_item.overlay_count()-1-row]
                if ol_item:
                    return self.createIndex(row, column, ol_item)
                else:
                    return QModelIndex()
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

        item = index.internalPointer()

        if item in self._data:
            if role == Qt.UserRole + 2:
                return item.get_alpha()
            elif role == Qt.UserRole + 3:
                return item.get_colormap()
        else:
            if role == Qt.UserRole:
                return item.get_min()
            elif role == Qt.UserRole + 1:
                return item.get_max()
            elif role == Qt.UserRole + 2:
                return item.get_alpha()
            elif role == Qt.UserRole + 3:
                return item.get_colormap()

        if role == Qt.DisplayRole or role == Qt.EditRole:
           return item.get_name()

        if role == Qt.CheckStateRole:

            if index.column() == 0:
                if item.is_visible():
                    return Qt.Checked
                else:
                    return Qt.Unchecked

    def flags(self, index):
        """Return the Qt flags for each data item."""
        if not index.isValid():
            return Qt.NoItemFlags
        
        result = Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        item = index.internalPointer()
        if not item in self._data:
            for hemi in self._data:
                if item in hemi.overlay_list:
                    break
            if hemi.is_visible():
                result |= Qt.ItemIsEnabled
        else:
            result |= Qt.ItemIsEnabled

        return result

    def headerData(self, section, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return 'Name'
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == Qt.EditRole:
            value_str = value.toPyObject()
            if value_str != '':
                if item.get_name() != value_str:
                    item.set_name(str(value_str))
                else:
                    return False
            else:
                return False
        elif role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Unchecked:
                item.set_visible(False)
            else:
                item.set_visible(True)

        if item in self._data:
            if role == Qt.UserRole + 2:
                if item.get_alpha != value:
                    item.set_alpha(value)
            elif role == Qt.UserRole + 3:
                if item.get_colormap != value:
                    item.set_colormap(value)
        else:
            if role == Qt.UserRole:
                if str(item.get_min()) != value:
                    item.set_min(value)
                else:
                    return False
            elif role == Qt.UserRole + 1:
                if str(item.get_max()) != value:
                    item.set_max(value)
                else:
                    return False
            elif role == Qt.UserRole + 2:
                if item.get_alpha() != value:
                    item.set_alpha(value)
                else:
                    return False
            elif role == Qt.UserRole + 3:
                if item.get_colormap() != value:
                    item.set_colormap(value)
                else:
                    return False

        self.dataChanged.emit(index, index)
        self.repaint_surface.emit()
        return True

    def insertRow(self, row, item, parent):
        self.beginInsertRows(parent, row, row)
        if item is not None:
            self._data.append(item)  # insert(row, item)
        self.endInsertRows()

    def removeRow(self, row, parent):
        self.beginRemoveRows(parent, row, row)
        item = self.index(row, 0, parent).internalPointer()
        parent_item = parent.internalPointer()
        if item in self._data:
            self._data.remove(item)
        else:
            parent_item.overlay_list.remove(item)
        self.endRemoveRows()

    def moveUp(self, index):
        item = index.internalPointer()
        row = index.row()
        parent = index.parent()
        self.beginMoveRows(parent, row, row, parent, row-1)
        for hemi in self._data:
            if item in hemi.overlay_list:
                idx = hemi.overlay_list.index(item)
                hemi.overlay_up(idx)
        self.endMoveRows()
        self.repaint_surface.emit()

    def moveDown(self, index):
        item = index.internalPointer()
        row = index.row()
        parent = index.parent()
        self.beginMoveRows(parent, row+1, row+1, parent, row)
        for hemi in self._data:
            if item in hemi.overlay_list:
                idx = hemi.overlay_list.index(item)
                hemi.overlay_down(idx)
        self.endMoveRows()
        self.repaint_surface.emit()

    def setCurrentIndex(self, index):
        """Set current row."""
        if index.row() >= 0 and index.row() <= self.rowCount(index.parent()):
            self._current_index = index
        else:
            raise ValueError('Invalid value.')

    def is_hemisphere(self, index):
        """Check whether the `index` item is an instance of Hemisphere."""
        if not index.isValid():
            return Qt.NoItemFlags
        
        item = index.internalPointer()
        if item in self._data:
            return True
        else:
            return False

    def add_item(self, index, source, vmin=None, vmax=None, colormap=None):
        if not index.isValid():
            add_item = Hemisphere(source)
            self.insertRow(index.row(), add_item, index)

        else:
            parent = index.parent()
            if not parent.isValid():
                hemi_item = index.internalPointer()
            else:
                hemi_item = parent.internalPointer()
            hemi_item.load_overlay(source, 'white',
                                   vmin=vmin, vmax=vmax,
                                   colormap=colormap)  # FIXME 'white' should be replaced with surf_type
            add_item = None
            self.insertRow(index.row(), add_item, parent)
        self.repaint_surface.emit()
        return True

    def del_item(self, index):
        if not index.isValid():
            return None
        self.removeRow(index.row(), index.parent())
        self.repaint_surface.emit()
        return True

