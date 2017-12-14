#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from treemodel import TreeModel
from froi.utils import *
from froi.core.dataobject import Hemisphere
from froi.core.labelconfig import LabelConfig
from froi.algorithm.tools import get_curr_hemi


class SurfaceTreeView(QWidget):
    """
    Implementation a widget for layer selection and parameters alternating.
    """
    # current_changed = pyqtSignal()
    repaint_surface = pyqtSignal()
    builtin_colormap = ['gray',
                        'red2yellow',
                        'blue2cyanblue',
                        'red',
                        'green',
                        'blue',
                        'rainbow',
                        'single ROI',
                        'rocket',
                        'mako',
                        'icefire',
                        'vlag',
                        'jet']

    def __init__(self, model, parent=None):
        """TreeView initialization."""
        super(SurfaceTreeView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.setMaximumWidth(280)
        self._temp_dir = None
        self._icon_dir = get_icon_dir()

        self._init_gui()

        if isinstance(model, QAbstractItemModel):
            self._model = model
            self._tree_view.setModel(model)
        else:
            raise ValueError('Input must be a TreeModel!')

        self._create_action()

    def _init_gui(self):
        """Initialize a GUI designation."""
        # initialize QTreeView
        self._tree_view = QTreeView()

        # initialize visibility controller
        visibility_label = QLabel('Visibility')
        self._visibility = QSlider(Qt.Horizontal)
        self._visibility.setMinimum(0)
        self._visibility.setMaximum(100)
        self._visibility.setSingleStep(5)
        visibility_layout = QHBoxLayout()
        visibility_layout.addWidget(visibility_label)
        visibility_layout.addWidget(self._visibility)

        # -- Geometry display settings panel
        # initialize geometry display settings widgets
        # TODO: to be refactorred to support more geometry shapes
        geo_name_label = QLabel('Geo:')
        self._geo_name_edit = QLineEdit()

        # layout for geometry settings
        geo_layout = QGridLayout()
        geo_layout.addWidget(geo_name_label, 0, 0)
        geo_layout.addWidget(self._geo_name_edit, 0, 1)
        geo_group_box = QGroupBox('Geometry display settings')
        geo_group_box.setLayout(geo_layout)

        # -- Overlay display settings panel
        # initialize up/down push button
        button_size = QSize(12, 12)
        self._up_button = QPushButton()
        self._up_button.setIcon(QIcon(os.path.join(self._icon_dir,
                                                   'arrow_up.png')))
        self._up_button.setIconSize(button_size)
        self._down_button = QPushButton()
        self._down_button.setIcon(QIcon(os.path.join(self._icon_dir,
                                                     'arrow_down.png')))
        self._down_button.setIconSize(button_size)

        # initialize ScalarData display settings widgets
        max_label = QLabel('Max:')
        self._view_max = QLineEdit()
        min_label = QLabel('Min:')
        self._view_min = QLineEdit()
        scalar_colormap_label = QLabel('Colormap:')
        self._scalar_colormap = QComboBox()
        self._scalar_colormap.addItems(self.builtin_colormap)
        self._scalar_colormap.setEditable(True)

        # layout for ScalarData settings
        scalar_layout = QGridLayout()
        scalar_layout.addWidget(max_label, 0, 0)
        scalar_layout.addWidget(self._view_max, 0, 1)
        scalar_layout.addWidget(self._up_button, 0, 2)
        scalar_layout.addWidget(min_label, 1, 0)
        scalar_layout.addWidget(self._view_min, 1, 1)
        scalar_layout.addWidget(self._down_button, 1, 2)
        scalar_layout.addWidget(scalar_colormap_label, 2, 0)
        scalar_layout.addWidget(self._scalar_colormap, 2, 1, 1, 2)
        scalar_group_box = QGroupBox('Overlay display settings')
        scalar_group_box.setLayout(scalar_layout)

        # initialize widgets for cursor information
        id_label = QLabel('id:')
        self._id_edit = QLineEdit()
        self._id_edit.setReadOnly(True)
        value_label = QLabel('value:')
        self._value_edit = QLineEdit()
        self._value_edit.setReadOnly(True)

        # layout for cursor position information
        cursor_layout = QHBoxLayout()
        cursor_layout.addWidget(id_label)
        cursor_layout.addWidget(self._id_edit)
        cursor_layout.addWidget(value_label)
        cursor_layout.addWidget(self._value_edit)
        cursor_group_box = QGroupBox('Cursor')
        cursor_group_box.setLayout(cursor_layout)

        # -- layout config for whole TreeWidget
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._tree_view)
        self.layout().addWidget(geo_group_box)
        self.layout().addWidget(scalar_group_box)
        self.layout().addLayout(visibility_layout)
        self.layout().addWidget(cursor_group_box)

        # -- right click context show
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.contextMenu = QMenu(self)

    def showContextMenu(self):
        '''Show right click context menu'''
        self.contextMenu.move(QCursor.pos())
        self.contextMenu.show()

    def _create_action(self):
        """Create several necessary actions."""
        # When select one item, display specific parameters
        self._tree_view.selectionModel().currentChanged.connect(
                self._disp_current_para)

        # TODO: fulfill this function
        # # When select one item, display its undo/redo settings
        # self._tree_view.selectionModel().currentChanged.connect(
        #        self.current_changed)

        # When layout changed, refresh display.
        self._model.layoutChanged.connect(self._disp_current_para)

        # When vertex id changes, refresh display.
        self._model.idChanged.connect(self._disp_current_para)

        # Config setting actions
        self._view_min.editingFinished.connect(self._set_view_min)
        self._view_max.editingFinished.connect(self._set_view_max)
        self._scalar_colormap.currentIndexChanged.connect(self._set_colormap)
        self._visibility.sliderReleased.connect(self._set_alpha)
        self._up_button.clicked.connect(self._up_action)
        self._down_button.clicked.connect(self._down_action)

        self._rightclick_add = self.contextMenu.addAction(u'Add')
        self._rightclick_del = self.contextMenu.addAction(u'Delete')
        self._rightclick_rename = self.contextMenu.addAction(u'Rename')
        self._rightclick_rename.setVisible(False)
        self._rightclick_add.triggered.connect(self._rightclick_add_action)
        self._rightclick_rename.triggered.connect(self._rightclick_rename_action)
        self._rightclick_del.triggered.connect(self._rightclick_del_action)

    def _disp_current_para(self, index=-1):
        """Display selected item's parameters."""
        if index == -1:
            index = self._tree_view.currentIndex()

        if index.row() != -1:
            # set up status of up/down button
            if index.row() == 0:
                self._up_button.setEnabled(False)
            else:
                self._up_button.setEnabled(True)
            if index.row() == (self._model.rowCount(index.parent()) - 1):
                self._down_button.setEnabled(False)
            else:
                self._down_button.setEnabled(True)

            # geometry information
            hemi = get_curr_hemi(index)
            self._geo_name_edit.setText(hemi.get_name())

            # min/max value
            self._view_min.setText(str(self._model.data(index, Qt.UserRole)))
            self._view_min.setCursorPosition(0)
            self._view_max.setText(str(self._model.data(index, Qt.UserRole + 1)))
            self._view_max.setCursorPosition(0)

            # colormap combo box setting
            cur_colormap = self._model.data(index, Qt.UserRole + 3)
            if isinstance(cur_colormap, LabelConfig):
                cur_colormap = cur_colormap.get_name()
            idx = self._scalar_colormap.findText(cur_colormap)
            self._scalar_colormap.setCurrentIndex(idx)

            # alpha slider setting
            current_alpha = self._model.data(index, Qt.UserRole + 2) * 100
            self._visibility.setValue(current_alpha)

            # cursor clicked information
            self._id_edit.setText(str(self._model.get_point_id()))
            self._value_edit.setText(str(self._model.data(index, Qt.UserRole + 4)))
            self._value_edit.setCursorPosition(0)

            self._tree_view.setFocus()

            # Set current index
            self._model.setCurrentIndex(self._tree_view.currentIndex())

    def _set_view_min(self):
        """Set current selected item's view_min value."""
        index = self._tree_view.currentIndex()
        value = self._view_min.text()
        if value == '':
            self._view_min.setText(str(self._model.data(index, Qt.UserRole)))
            self._view_min.setCursorPosition(0)
        else:
            self._model.setData(index, value, role=Qt.UserRole)

    def _set_view_max(self):
        """Set current selected item's view_max value."""
        index = self._tree_view.currentIndex()
        value = self._view_max.text()
        if value == '':
            self._view_max.setText(str(self._model.data(index, Qt.UserRole + 1)))
            self._view_max.setCursorPosition(0)
        else:
            self._model.setData(index, value, role=Qt.UserRole + 1)

    def _set_colormap(self):
        """Set colormap of current selected item."""
        index = self._tree_view.currentIndex()
        value = self._scalar_colormap.currentText()
        self._model.setData(index, str(value), role=Qt.UserRole + 3)

    def _set_alpha(self):
        """Set alpha value of current selected item."""
        index = self._tree_view.currentIndex()
        value = self._visibility.value() / 100.
        self._model.setData(index, value, role=Qt.UserRole + 2)

    def _up_action(self):
        """Move selected item up for one step."""
        index = self._tree_view.currentIndex()
        self._model.moveUp(index)
        self._tree_view.setFocus()

    def _down_action(self):
        """Move selected item down for one step."""
        index = self._tree_view.currentIndex()
        self._model.moveDown(index)
        self._tree_view.setFocus()

    def _get_surface_index(self, geo_type):
        # TODO may be removed in future
        """Check different type of surface exist or not."""
        for index in self._tree_view.selectedIndexes():
            if index.data().endswith(geo_type):
                return index
        return -1

    def get_treeview(self):
        return self._tree_view

    def _rightclick_add_action(self):
        """Add an overlay"""
        if self._temp_dir is None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_name = QFileDialog.getOpenFileName(self,
                                                'Add new surface file',
                                                temp_dir)
        if file_name != '':
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
            index = self._tree_view.currentIndex()
            self._model.add_item(index, file_path)
            self._disp_current_para()

            self._temp_dir = os.path.dirname(file_path)

    def _rightclick_rename_action(self):
        """rename overlays"""
        pass

    def _rightclick_del_action(self):
        """Delete an overlay"""
        index = self._tree_view.currentIndex()
        self._model.del_item(index)
        self._disp_current_para()

    # def _add_item(self, source):
    #     index = self._tree_view.currentIndex()
    #     if not index.isValid():
    #         add_item = Hemisphere(source)
    #         ok = self._model.insertRow(index.row(), add_item, index)
    #
    #     else:
    #         parent = index.parent()
    #         if not parent.isValid():
    #             add_item = Hemisphere(source)
    #         else:
    #             parent_item = parent.internalPointer()
    #             parent_item.load_overlay(source)
    #             add_item = None
    #         ok = self._model.insertRow(index.row(), add_item, parent)
    #
    #     if ok:
    #         self._model.repaint_surface.emit()
    #         return True
    #     else:
    #         return False
    #
    # def _del_item(self, row, parent):
    #     index = self._tree_view.currentIndex()
    #     if not index.isValid():
    #         return False
    #     ok = self._model.removeRow(index.row(), index.parent())
    #     if ok:
    #         self._model.repaint_surface.emit()
    #         return True
    #     else:
    #         return False


if __name__ == '__main__':
    from froi import utils as froi_utils

    app = QApplication(sys.argv)
    db_dir = froi_utils.get_data_dir()
    # model init
    hemisphere_list = []
    sub1 = os.path.join(db_dir, 'surf', 'lh.white')
    surf2 = os.path.join(db_dir, 'surf', 'rh.white')
    s1 = os.path.join(db_dir, 'surf', 'white')
    s2 = os.path.join(db_dir, 'surf', 'pial')
    s3 = os.path.join(db_dir, 'surf', 'rh.thickness')
    s4 = os.path.join(db_dir, 'surf', 'rh.curv')

    h1 = Hemisphere(sub1)
    h1.load_geometry(sub1, 'inflated')
    h1.load_overlay(s1)
    h1.load_overlay(s2)
    h2 = Hemisphere(surf2)
    h2.load_overlay(s3)
    h2.load_overlay(s4)

    hemisphere_list.append(h1)
    hemisphere_list.append(h2)

    for h in hemisphere_list:
        print h.name
        for ol in h.overlays:
            print ol.name

    model = TreeModel(hemisphere_list)

    # View init
    view = SurfaceTreeView(model)
    view.setWindowTitle("Hemisphere Tree Model")
    view.show()

    sys.exit(app.exec_())
