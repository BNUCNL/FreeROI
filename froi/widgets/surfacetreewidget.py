#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.core.dataobject import Hemisphere
from treemodel import TreeModel
from froi.utils import *
from froi.core.labelconfig import LabelConfig


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

        # initialize surface option push button
        self._white_button = QPushButton('white')
        self._pial_button = QPushButton('pial')
        self._inflated_button = QPushButton('inflated')
        self._flatted_button = QPushButton('flatted')

        # self._surface_button.setIconSize(surface_button_size)
        surface_type_layout = QHBoxLayout()
        surface_type_layout.addWidget(self._white_button)
        surface_type_layout.addWidget(self._pial_button)
        surface_type_layout.addWidget(self._inflated_button)
        surface_type_layout.addWidget(self._flatted_button)
        surface_type_group_box = QGroupBox('Surface type option')
        surface_type_group_box.setLayout(surface_type_layout)

        # initialize visibility controller
        visibility_label = QLabel('Visibility')
        self._visibility = QSlider(Qt.Horizontal)
        self._visibility.setMinimum(0)
        self._visibility.setMaximum(100)
        self._visibility.setSingleStep(5)
        visibility_layout = QHBoxLayout()
        visibility_layout.addWidget(visibility_label)
        visibility_layout.addWidget(self._visibility)

        # -- Surface display settings panel
        # initialize Surface display settings widgets
        # TODO: to be refactorred
        surface_name_label = QLabel('Hemi:')
        self._surface_name = QLineEdit()
        surface_colormap_label = QLabel('Colormap:')
        self._surface_colormap = QComboBox()
        self._surface_colormap.addItems(self.builtin_colormap)
        self._surface_colormap.setEditable(True)

        # layout for Surface settings
        surface_layout = QGridLayout()
        surface_layout.addWidget(surface_name_label, 0, 0)
        surface_layout.addWidget(self._surface_name, 0, 1)
        surface_layout.addWidget(surface_colormap_label, 1, 0)
        surface_layout.addWidget(self._surface_colormap, 1, 1)
        surface_group_box = QGroupBox('Surface display settings')
        surface_group_box.setLayout(surface_layout)

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
        self.layout().addWidget(surface_type_group_box)
        self.layout().addLayout(visibility_layout)
        self.layout().addWidget(surface_group_box)
        self.layout().addWidget(scalar_group_box)
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

        # When dataset changed, refresh display.
        self._model.dataChanged.connect(self._disp_current_para)

        # When add new item, refresh display.
        self._model.rowsInserted.connect(self._disp_current_para)

        # When remove new item, refresh display.
        self._model.rowsRemoved.connect(self._disp_current_para)

        # When layout changed, refresh display.
        self._model.layoutChanged.connect(self._disp_current_para)

        # When vertex id changes, refresh display.
        self._model.idChanged.connect(self._disp_current_para)

        # Config setting actions
        self._view_min.editingFinished.connect(self._set_view_min)
        self._view_max.editingFinished.connect(self._set_view_max)
        self._surface_colormap.currentIndexChanged.connect(self._set_colormap)
        self._scalar_colormap.currentIndexChanged.connect(self._set_colormap)
        self._visibility.sliderReleased.connect(self._set_alpha)
        self._up_button.clicked.connect(self._up_action)
        self._down_button.clicked.connect(self._down_action)
        self._white_button.clicked.connect(self._white_action)
        self._pial_button.clicked.connect(self._pial_action)
        self._inflated_button.clicked.connect(self._inflated_action)
        self._flatted_button.clicked.connect(self._flatted_action)

        self._rightclick_add = self.contextMenu.addAction(u'Add')
        self._rightclick_edit = self.contextMenu.addAction(u'Edit')
        self._rightclick_del = self.contextMenu.addAction(u'Delete')
        self._rightclick_add.triggered.connect(self._rightclick_add_action)
        self._rightclick_edit.triggered.connect(self._rightclick_edit_action)
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

    def _white_action(self):
        """Show white surface."""
        # index = self._tree_view.currentIndex()
        # max_index = self._model.rowCount(index.parent()) - 1
        index = self._get_surface_index('white')
        if not index == -1:
            self._disp_current_para(index)

    def _pial_action(self):
        """Show pial surface."""
        index = self._get_surface_index('pial')
        if not index == -1:
            self._disp_current_para(index)

    def _inflated_action(self):
        """Show inflated surface."""
        index = self._get_surface_index('inflated')
        if not index == -1:
            self._disp_current_para(index)

    def _flatted_action(self):
        """Show flatted surface."""
        index = self._get_surface_index('flatted')
        if not index == -1:
            self._disp_current_para(index)

    def _get_surface_index(self, surf_type):
        """Check different type of surface exist or not."""
        for index in self._tree_view.selectedIndexes():
            if index.data().endswith(surf_type):
                return index
        return -1

    def get_treeview(self):
        return self._tree_view

    def _rightclick_add_action(self):
        """Add, use method: main.py BpMainWindow._add_surface_image()"""
        print 'Add'

    def _rightclick_edit_action(self):
        """Edit"""
        print 'Edit'

    def _rightclick_del_action(self):
        """Del"""
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
    h1.load_surface(sub1, 'inflated')
    h1.load_overlay(s1)
    h1.load_overlay(s2)
    h2 = Hemisphere(surf2)
    h2.load_overlay(s3)
    h2.load_overlay(s4)

    hemisphere_list.append(h1)
    hemisphere_list.append(h2)

    for h in hemisphere_list:
        print h.name
        for ol in h.overlay_list:
            print ol.name

    model = TreeModel(hemisphere_list)

    # View init
    view = SurfaceTreeView(model)
    view.setWindowTitle("Hemisphere Tree Model")
    view.show()

    sys.exit(app.exec_())
