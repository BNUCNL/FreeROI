# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Implementation of a Tree model for surface data display.

"""

import numpy as np
from PyQt4.QtCore import *
from traits.trait_handlers import HandleWeakRef

from froi.core.dataobject import Surface


class TreeModel(QAbstractItemModel):
    """Definition of class TreeModel."""
    # customized signals
    repaint_surface = pyqtSignal()
    idChanged = pyqtSignal()

    def __init__(self, surfaces, parent=None):
        """Initialize an instance."""
        super(TreeModel, self).__init__(parent)
        self._data = surfaces
        self._point_id = 0
        self._current_index = QModelIndex()

    def get_data(self):
        return self._data

    def index(self, row, column, parent):
        """Return the index of item in the model."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            surf_item = self._data[row]
            return self.createIndex(row, column, surf_item)
        else:
            surf_item = parent.internalPointer()
            if surf_item in self._data:
                ol_item = surf_item.overlays[surf_item.overlay_count()-1-row]
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
            for surf in self._data:
                if item in surf.overlays:
                    return self.createIndex(self._data.index(surf), 0, surf)

    def rowCount(self, parent):
        """Return the number of rows for display."""

        depth = self.index_depth(parent)
        if depth == 0:
            return len(self._data)
        elif depth == 1:
            return parent.internalPointer().overlay_count()
        elif depth == 2:
            return 0

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return 1
        
    def data(self, index, role):
        """Return specific data."""

        depth = self.index_depth(index)
        if depth == 0:
            return None
        elif depth == 1:
            item = index.internalPointer()
            if role == Qt.UserRole + 2:
                # FIXME to remove the role after refine visible bar's display
                return 1.0
            if role == Qt.UserRole + 3:
                return item.get_colormap()
            elif role == Qt.UserRole + 4:
                if self._point_id == -1:
                    return None
                if item.bin_curv is not None:
                    return item.bin_curv[self._point_id]
            elif role == Qt.UserRole + 6:
                return item.current_geometry()
            elif role == Qt.DisplayRole or role == Qt.EditRole:
                return item.hemi_rl
        elif depth == 2:
            item = index.internalPointer()
            if role == Qt.UserRole:
                return item.get_min()
            elif role == Qt.UserRole + 1:
                return item.get_max()
            elif role == Qt.UserRole + 2:
                return item.get_alpha()
            elif role == Qt.UserRole + 3:
                return item.get_colormap()
            elif role == Qt.UserRole + 4:
                if self._point_id == -1:
                    return None
                return item.get_data()[self._point_id][0]
            elif role == Qt.UserRole + 5:
                return item.get_data()
            elif role == Qt.UserRole + 7:
                return item.is_label()
            elif role == Qt.UserRole + 8:
                return item.is_visible()
            elif role == Qt.DisplayRole or role == Qt.EditRole:
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
        if item not in self._data:
            for surf in self._data:
                if item in surf.overlays and surf.is_visible():
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

        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Unchecked:
                item.set_visible(False)
            else:
                item.set_visible(True)

        if item in self._data:
            if role == Qt.UserRole + 3:
                if item.get_colormap() != value:
                    item.set_colormap(value)
                else:
                    return False
        else:
            if role == Qt.EditRole:
                value_str = value.toPyObject()
                if value_str != '':
                    if item.get_name() != value_str:
                        item.set_name(str(value_str))
                    else:
                        return False
                else:
                    return False
            elif role == Qt.UserRole:
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
        if isinstance(item, Surface):
            self._data.append(item)  # insert(row, item)
        self.endInsertRows()

    def removeRow(self, row, parent):
        self.beginRemoveRows(parent, row, row)
        item = self.index(row, 0, parent).internalPointer()
        parent_item = parent.internalPointer()
        if item in self._data:
            self._data.remove(item)
        else:
            parent_item.overlays.remove(item)
        self.endRemoveRows()

    def moveUp(self, index):
        item = index.internalPointer()
        row = index.row()
        parent = index.parent()
        self.beginMoveRows(parent, row, row, parent, row-1)
        for surf in self._data:
            if item in surf.overlays:
                idx = surf.overlays.index(item)
                surf.overlay_up(idx)
        self.endMoveRows()
        self.repaint_surface.emit()

    def moveDown(self, index):
        item = index.internalPointer()
        row = index.row()
        parent = index.parent()
        self.beginMoveRows(parent, row+1, row+1, parent, row)
        for surf in self._data:
            if item in surf.overlays:
                idx = surf.overlays.index(item)
                surf.overlay_down(idx)
        self.endMoveRows()
        self.repaint_surface.emit()

    def setCurrentIndex(self, index):
        """Set current row."""
        if -1 <= index.row() <= self.rowCount(index.parent()):
            self._current_index = index
            self.emit(SIGNAL("currentIndexChanged"))
        else:
            raise ValueError('Invalid value.')

    def current_index(self):
        return self._current_index

    def get_surface_index(self, index=None):
        if index is None:
            index = self._current_index

        depth = self.index_depth(index)
        if depth == 1:
            surface_idx = index
        elif depth == 2:
            surface_idx = self.parent(index)
        else:
            return None
        return surface_idx

    def get_overlay_list(self, index=None):
        if index is None:
            index = self._current_index

        overlay_list = []
        surface_idx = self.get_surface_index(index)
        if surface_idx is None:
            return overlay_list

        for row in range(self.rowCount(surface_idx)):
            idx = self.index(row, 0, surface_idx)
            overlay_list.append(self.data(idx, Qt.DisplayRole))
        return overlay_list

    def index_depth(self, index=None):
        """judge the depth of the index relative to the root"""
        if index is None:
            index = self._current_index

        depth = 0
        while True:
            if not hasattr(index, "isValid") or not index.isValid():
                return depth
            else:
                index = self.parent(index)
                depth += 1

    def add_item(self, index, source=None, vmin=None, vmax=None, colormap='jet',
                 alpha=1.0, visible=True, islabel=False, name=None):

        if not index.isValid():
            if not isinstance(source, Surface):
                source = Surface(source)
            self.insertRow(index.row(), source, index)
        else:
            parent = index.parent()
            if not parent.isValid():
                surf_item = index.internalPointer()
            else:
                surf_item = parent.internalPointer()
            if source is None:
                source = np.zeros((surf_item.vertices_count(),))
            surf_item.load_overlay(source, vmin=vmin, vmax=vmax, colormap=colormap, alpha=alpha,
                                   visible=visible, islabel=islabel, name=name)
            self.insertRow(index.row(), None, parent)
        self.repaint_surface.emit()
        return True

    def del_item(self, index):
        if not index.isValid():
            return None
        self.removeRow(index.row(), index.parent())
        self.repaint_surface.emit()
        if len(self._data) == 0:
            self.emit(SIGNAL("modelEmpty"))
        return True

    def set_vertices_value(self, value, index=None, vertices=None, roi=None,
                           target_row=None):

        if index is None:
            index = self._current_index

        depth = self.index_depth(index)
        if depth == 2:
            item = index.internalPointer()
            if roi is not None:
                # change values, which are equal to roi, to the new value.
                vertices = item.get_roi_vertices(roi)

            if target_row is None:
                target_item = item
            else:
                target_idx = self.index(target_row, 0, self.parent(index))
                target_item = target_idx.internalPointer()

            target_item.set_vertices_value(vertices, value)
        else:
            return None

        self.repaint_surface.emit()

    def set_point_id(self, point_id):
        self._point_id = point_id
        self.idChanged.emit()

    def get_point_id(self):
        return self._point_id

    def phi_theta_to_show(self, phi, theta):
        self.emit(SIGNAL("phi_theta_to_show"), phi, theta)

    def phi_theta_to_edit(self, phi, theta):
        self.emit(SIGNAL("phi_theta_to_edit"), phi, theta)
