# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Implementation of model part in Qt Model-View architecture.

"""

import numpy as np
from PyQt4.QtCore import *

from ..base.bpdataset import VolumeDataset

class VolumeListModel(QAbstractListModel):
    """
    Definition of class VolumeListModel.
    
    """
    # customized signal
    repaint_slices = pyqtSignal(int, name='repaint_slices')
    scale_changed = pyqtSignal()
    time_changed = pyqtSignal()
    cross_pos_changed = pyqtSignal()
    undo_stack_changed = pyqtSignal()
    redo_stack_changed = pyqtSignal()

    # new image order
    new_no = 1

    def __init__(self, data_list, label_config_center, parent=None):
        """
        Initialize an instance.

        """
        super(VolumeListModel, self).__init__(parent)
        self._data = data_list
        self._current_index = None
        self._selected_indexes = []
        self._grid_scale_factor = 1.0
        self._orth_scale_factor = 1.0
        # FIXME current position should be initialized when the first volume added.
        # The current position is a 4D data.
        self._cross_pos = [0, 0, 0]
        self._display_cross = True
        self._connect_undo_redo()
        self._label_config_center = label_config_center
        self._label_config_center.single_roi_view_update_for_model.connect(
                self.update_all_rgba)

    def get_cross_pos(self):
        """
        Get current cursor position.

        """
        return self._cross_pos

    def set_cross_pos(self, new_coord):
        """
        Set current cursor position.

        """
        self._cross_pos = new_coord
        self.update_orth_rgba()
        self.cross_pos_changed.emit()

    def update_orth_rgba(self):
        """
        Update RGBA data for OrthView.

        """
        for data in self._data:
            data.set_cross_pos(self.get_cross_pos())

    def display_cross(self):
        """
        Return the status of current position indicator.

        """
        return self._display_cross

    def set_cross_status(self, status):
        """
        Set the status of current position indicator.

        """
        if isinstance(status, bool) and not status == self.display_cross():
            self._display_cross = status
            self.cross_pos_changed.emit()

    def rowCount(self, parent=QModelIndex()):
        """
        Return the item numbers in the list.
        
        """
        return len(self._data)

    def data(self, index, role):
        """
        Return the data stored under the given role for the item 
        referred to by the index.
        
        """
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return QVariant()

        row = index.row()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._data[row].get_name()
        elif role == Qt.CheckStateRole:
            if self._data[row].is_visible():
                return Qt.Checked
            else:
                return Qt.Unchecked
        elif role == Qt.UserRole:
            return self._data[row].get_view_min()
        elif role == Qt.UserRole + 1:
            return self._data[row].get_view_max()
        elif role == Qt.UserRole + 2:
            return self._data[row].get_alpha()
        elif role == Qt.UserRole + 3:
            return self._data[row].get_colormap()
        elif role == Qt.UserRole + 4:
            return self._data[row].get_lthr_data()
        elif role == Qt.UserRole + 5:
            return self._data[row].get_lthr_raw_data()
        elif role == Qt.UserRole + 6:
            return self._data[row].get_raw_data()
        elif role == Qt.UserRole + 7:
            # get label config
            return self._label_config_center.get_current_label_config(), self._label_config_center.get_current_list_view_index()
        elif role == Qt.UserRole + 8:
            return self._data[row].is_4d()
        elif role == Qt.UserRole + 9:
            return self._data[row].get_time_point()
        elif role == Qt.UserRole + 10:
            return self._data[row].get_data_shape()[3]

        return QVariant()

    def setData(self, index, value, role):
        """
        Set data according to the data role and item index.
        
        """
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return False

        row = index.row()
        if role == Qt.EditRole:
            value_str = value.toPyObject()
            if not value_str == '':
                if not self._data[row].get_name() == value_str:
                    self._data[row].set_name(str(value_str))
                else:
                    return False
            else:
                return False
        elif role == Qt.CheckStateRole:
            if not self._data[row].is_visible() == value.toBool():
                self._data[row].set_visible(value.toBool())
            else:
                return False
        elif role == Qt.UserRole:
            if not str(self._data[row].get_view_min()) == value:
                self._data[row].set_view_min(value)
            else:
                return False
        elif role == Qt.UserRole + 1:
            if not str(self._data[row].get_view_max()) == value:
                self._data[row].set_view_max(value)
            else:
                return False
        elif role == Qt.UserRole + 2:
            if not self._data[row].get_alpha() == value:
                self._data[row].set_alpha(value)
            else:
                return False
        elif role == Qt.UserRole + 3:
            if not self._data[row].get_colormap() == value:
                self._data[row].set_colormap(value)
            else:
                return False
        # FIXME Following argument should be checked out.
        elif role == Qt.UserRole + 4:
            if value in self._data[row].get_roi_index().items():
                return False
            else:
                self._data[row].set_roi_name([value])
        elif role == Qt.UserRole + 5:
            self._data[row]._data  = np.rot90(value)
        elif role == Qt.UserRole + 9:
            if not self._data[row].get_time_point() == value:
                self._data[row].set_time_point(value)
            else:
                return False

        # Update RGBA list after setting
        #self._data[row].update_rgba()     
        self.dataChanged.emit(index, index)
        self.repaint_slices.emit(-1)
        return True

    def flags(self, index):
        """
        Set item flag.
        
        """
        flag = super(VolumeListModel, self).flags(index)
        return flag | Qt.ItemIsEditable | Qt.ItemIsUserCheckable

    def insertRow(self, row, vol, parent=QModelIndex()):
        """
        Insert a new item to the list.
        
        """
        return self.insertRows(row, 1, [vol], parent)

    def insertRows(self, row, count, vol_list, parent=QModelIndex()):
        """
        Insert new items to the list.
        
        """
        self.beginInsertRows(parent, row, (row + (count - 1)))
        for index in range(count):
            try:
                vol = vol_list[index]
                self._data.insert(row + index, vol)
                vol.connect_undo(self.undo_stack_changed)
                vol.connect_redo(self.redo_stack_changed)
            except:
                raise
                print 'Insert new item failed!'
                return False
        self.endInsertRows()
        return True

    def removeRow(self, row, parent=QModelIndex()):
        """
        Remove one item from the list.
        
        """
        return self.removeRows(row, 1, parent)

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Remove items from the list.
        
        """
        #print type(row),'----------------------',type(count)
        self.beginRemoveRows(parent, row, (row + count - 1))
        for index in range(count):
            self._data.pop(row)
        self.endRemoveRows()
        return True

    def addItem(self, source, label_config=None, name=None, header=None,
                view_min=None, view_max=None, alpha=255, colormap='gray'):
        """
        Add a new item.

        Example:
        --------

        >>> model.addItem(filepath)

        """

        vol = VolumeDataset(source, self._label_config_center, name, header,
                            view_min, view_max, alpha, colormap,
                            [self._cross_pos[0],
                             self._cross_pos[1],
                             self._cross_pos[2]])
        if self.rowCount():
            if self._data[0].get_data_shape()[0:3] == vol.get_data_shape()[0:3]:
                ok = self.insertRow(0, vol)
                if ok:
                    self.repaint_slices.emit(-1)
                    return True
                else:
                    return False
            else:
                print 'Mismatch data size!'
                return False
        else:
            ok = self.insertRow(0, vol)
            if ok:
                self.repaint_slices.emit(-1)
                return True
            else:
                return False

    def delItem(self, row):
        """
        Delete a item.

        Example:
        --------

        >>> model.delItem(3)   # delete the 4th item

        """
        ok = self.removeRow(row)
        if ok:
            self.repaint_slices.emit(-1)
            return True
        else:
            return False
    
    def new_image(self, data=None, name=None, label_config=None, colormap=None):
        """
        Add a new item.

        """
        if data is None:
            new_data = np.zeros(self._data[0].get_data_shape()[0:3], dtype=np.int_)
        else:
            new_data = data
        new_header = self._data[0].get_header().copy()
        new_header.set_data_shape(new_data.shape)
        if colormap is None:
            colormap = self._label_config_center.get_first_label_config()
        if name is None:
            self.addItem(new_data, label_config, 'new_image_%s' % self.new_no,
                         new_header, 0, 100, 255, colormap)
            self.new_no += 1
        else:
            self.addItem(new_data, label_config, name,
                         new_header, 0, 100, 255, colormap)
        
    def moveUp(self, row, parent=QModelIndex()):
        """
        Move the specific row up for one step.

        """
        if row != 0:
            self.beginMoveRows(parent, row, row, parent, row - 1)
            self._data[row], self._data[row - 1] = \
                    self._data[row - 1], self._data[row]
            self.endMoveRows()
            self.repaint_slices.emit(-1)
        else:
            raise ValueError("Input must be non-zero integer.")

    def moveDown(self, row, parent=QModelIndex()):
        """
        Move the specific row down for one step.

        """
        if row != (self.rowCount() - 1):
            self.beginMoveRows(parent, row + 1, row + 1, parent, row)
            self._data[row], self._data[row + 1] = \
                    self._data[row + 1], self._data[row]
            self.endMoveRows()
            self.repaint_slices.emit(-1)
        else:
            raise ValueError("Index out of range!")

    def currentIndex(self):
        """
        Return current index.

        """
        return self._current_index

    def setCurrentIndex(self, index):
        """
        Set current row.

        """
        if index.row() >= 0 and index.row() <= self.rowCount():
            self._current_index = index
        else:
            raise ValueError('Invalid value.')

    def setSelectedIndexes(self):
        """
        Return all selected items and save into _selected_indexes.

        """
        self._selected_indexes = []
        for row in range(self.rowCount()):
            idx = self.index(row) 
            if self.data(idx, Qt.CheckStateRole) == Qt.Checked:
                self._selected_indexes.insert(0, idx)

    def getItemList(self):
        """
        Return whole items' name.

        """
        item_list = []
        for row in range(self.rowCount()):
            idx = self.index(row)
            item_list.append(self.data(idx, Qt.DisplayRole))
        return item_list

    def selectedIndexes(self):
        """
        Get selected items.

        """
        self.setSelectedIndexes()
        return self._selected_indexes

    def set_scale_factor(self, value, type):
        """
        Set scale factor.

        """
        if type == 'grid':
            self._grid_scale_factor = value
        elif type == 'orth':
            self._orth_scale_factor = value
        #self.repaint_slices.emit(-1)
        self.scale_changed.emit()

    def get_scale_factor(self, type):
        """
        Get scale factor.

        """
        if type == 'grid':
            return self._grid_scale_factor
        elif type == 'orth':
            return self._orth_scale_factor

    def modify_voxels(self, coord_list=None, value=None, roi=None, target_row=None, ignore=True):
        """
        Set (x, y, z) voxel's value on specific layer.

        """
        if value is None:
            return

        if coord_list is not None:
            row = self.currentIndex().row()
            x = [item[1] for item in coord_list]
            y = [item[0] for item in coord_list]
            z = [item[2] for item in coord_list]
            self._data[row].set_voxel(x, y, z, value, ignore)
            self.repaint_slices.emit(coord_list[0][2])
        elif roi is not None:
            row = self.currentIndex().row()
            if target_row is None:
                target_row = row
            coords = self._data[row].get_roi_coords(roi)
            x, y, z = list(coords[0]), list(coords[1]), list(coords[2])
            self._data[target_row].set_voxel(x, y, z, value, ignore)
            for s in range(min(z), max(z)+1):
                self.repaint_slices.emit(s)
        else:
            return
    
    def get_current_roi_val(self, x, y, z):
        row = self.currentIndex().row()
        return self._data[row].get_coord_val(x, y, z)

    def get_current_time_point(self):
        row = self.currentIndex().row()
        if self._data[row].is_4d():
            return self._data[row].get_time_point()
        else:
            return False

    def rgba_list(self, index):
        """
        Get RGBA array for `index`th label.

        """
        return [self._data[idx.row()].get_rgba(index) for 
                idx in self.selectedIndexes()]

    def getX(self):
        """
        Get the height of the picture.

        """
        return self._data[0].get_data_shape()[1]

    def getY(self):
        """
        Get width of the picture.

        """
        return self._data[0].get_data_shape()[0]

    def getZ(self):
        """
        Get layer index.

        """
        return self._data[0].get_data_shape()[2]

    def set_time_point(self, tpoint):
        """
        Set time point for every volume.

        """
        if isinstance(tpoint, int) and not tpoint < 0:
            for data in self._data:
                data.set_time_point(tpoint)
        self.time_changed.emit()
        self.repaint_slices.emit(-1)

    def get_current_label_config(self):
        row = self.currentIndex().row()
        return self._data[row].get_label_config()
        
    def _connect_undo_redo(self):
        for data in self._data:
            data.connect_undo(self.undo_stack_changed)
            data.connect_redo(self.redo_stack_changed)

    def undo_current_image(self):
        row = self.currentIndex().row()
        s = self._data[row].undo()
        if s is not None:
            for s_ in range(min(s), max(s)+1):
                self.repaint_slices.emit(s_)

    def redo_current_image(self):
        row = self.currentIndex().row()
        s = self._data[row].redo()
        if s is not None:
            for s_ in range(min(s), max(s)+1):
                self.repaint_slices.emit(s_)

    def current_undo_available(self):
        row = self.currentIndex().row()
        return self._data[row].undo_stack_not_empty()

    def current_redo_available(self):
        row = self.currentIndex().row()
        return self._data[row].redo_stack_not_empty()

    def get_current_value(self, xyz,time_course=False):
        row = self.currentIndex().row()
        return self._data[row].get_value(xyz,time_course)

    def get_row_value(self, xyz,row):
        return self._data[row].get_value(xyz)

    def get_current_value_label(self, value):
        return self._label_config_center.get_value_label(value)

    def update_current_rgba(self):
        row = self.currentIndex().row()
        self._data[row].update_rgba()
        self.repaint_slices.emit(-1)

    def update_all_rgba(self):
        self.repaint_slices.emit(-1)

    def get_sagital_rgba_list(self):
        """
        Get RGBA array for sagital direction in OrthView.

        """
        return [self._data[idx.row()].get_sagital_rgba() for
                idx in self.selectedIndexes()]

    def get_axial_rgba_list(self):
        """
        get RGBA array for axial direction in OrthView.

        """
        return [self._data[idx.row()].get_axial_rgba() for
                idx in self.selectedIndexes()]

    def get_coronal_rgba_list(self):
        """
        get RGBA array for axial direction in OrthView.

        """
        return [self._data[idx.row()].get_coronal_rgba() for
                idx in self.selectedIndexes()]

    #def sagital_rgba_list(self, slice):
    #    index_list = [idx.row() for idx in self.selectedIndexes()]
    #    rgba_list = []
    #    for index in index_list:
    #        f = self._data[index]._rendering_factory()
    #        if self._data[index].is_4d():
    #            temp = f(np.rot90(self._data[index]._data[:, slice, :, 
    #                                        self._data[index]._time_point]))
    #        else:
    #            temp = f(np.rot90(self._data[index]._data[:, slice, :]))
    #        rgba_list.append(temp)
    #    return rgba_list

    #def axial_rgba_list(self, slice):
    #    index_list = [idx.row() for idx in self.selectedIndexes()]
    #    rgba_list = []
    #    for index in index_list:
    #        f = self._data[index]._rendering_factory()
    #        if self._data[index].is_4d():
    #            temp = f(self._data[index]._data[:, :, slice,
    #                        self._data[index]._time_point])
    #        else:
    #            temp = f(self._data[index]._data[:, :, slice])
    #        rgba_list.append(temp)
    #    return rgba_list 

    #def coronal_rgba_list(self, slice):
    #    index_list = [idx.row() for idx in self.selectedIndexes()]
    #    rgba_list = []
    #    for index in index_list:
    #        f = self._data[index]._rendering_factory()
    #        if self._data[index].is_4d():
    #            temp = f(np.rot90(self._data[index]._data[slice, :, :, 
    #                        self._data[index]._time_point]))
    #        else:
    #            temp = f(np.rot90(self._data[index]._data[slice, :, :]))
    #        rgba_list.append(temp)
    #    return rgba_list

    def set_cur_label(self, label_config):
        row = self.currentIndex().row()
        self._data[row].set_label(label_config)

    def set_global_label(self, label_config):
        for bp_data in self._data:
            if bp_data.is_label_global():
                bp_data.set_label(label_config)

    def get_label_config_center(self):
        return self._label_config_center

