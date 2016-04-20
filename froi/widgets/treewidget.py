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


class TreeView(QWidget):
    """Implementation a widget for layer selection and parameters alternating.
    """

    current_changed = pyqtSignal()
    builtin_colormap = ['gray',
                        'red2yellow',
                        'blue2cyanblue',
                        'red',
                        'green',
                        'blue',
                        'rainbow',
                        'single ROI']

    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.setMaximumWidth(280)
        self._icon_dir = get_icon_dir()

        # initialize the model
        self._model = None

    def _init_gui(self):
        """Initialize a GUI designation."""
        # initialize QTreeView
        self._tree_view = QTreeView()

        # initialize up/down push button
        button_size = QSize(12, 12)
        self._up_button = QPushButton()
        self._up_button.setIcon(QIcon(os.path.join(self._icon_dir, 'arrow_up.png')))
        self._up_button.setIconSize(button_size)
        self._down_button = QPushButton()
        self._down_button.setIcon(QIcon(os.path.join(self._icon_dir, 'arrow_down.png')))
        self._down_button.setIconSize(button_size)

        # layout config for tree_view panel
        button_layout = QHBoxLayout()

        # initialize parameter  selection widgets
        visibility_label = QLabel('Visibility')
        self._visibility = QSlider(Qt.Horizontal)
        self._visibility.setMinimum(0)
        self._visibility.setMaximum(100)
        self._visibility.setSingleStep(5)

        button_layout.addWidget(visibility_label)
        button_layout.addWidget(self._visibility)
        button_layout.addWidget(self._up_button)
        button_layout.addWidget(self._down_button)

        max_label = QLabel('Max:')
        self._view_max = QLineEdit()
        min_label = QLabel('Min:')
        self._view_min = QLineEdit()
        colormap_label = QLabel('Colormap:')
        self._colormap = QComboBox()
        colormaps = self.builtin_colormap
        self._colormap.addItems(colormaps)

        # initialize parameter selection panel
        grid_layout = QGridLayout()
        grid_layout.addWidget(colormap_label, 1, 0)
        grid_layout.addWidget(self._colormap, 1, 1, 1, 3)

        # initialize parameter selection panel
        para_layout = QHBoxLayout()
        para_layout.addWidget(min_label)
        para_layout.addWidget(self._view_min)
        para_layout.addWidget(max_label)
        para_layout.addWidget(self._view_max)

        tree_view_layout = QVBoxLayout()
        tree_view_layout.addWidget(self._tree_view)
        tree_view_layout.addLayout(button_layout)
        tree_view_layout.addLayout(para_layout)
        tree_view_layout.addLayout(grid_layout)

        # layout config of whole widget
        self.setLayout(QVBoxLayout())
        self.layout().addLayout(tree_view_layout)

    def setModel(self, model):
        """Set model of the viewer."""
        if isinstance(model, QAbstractItemModel):
            self._model = model
            self._init_gui()
            self._tree_view.setModel(model)
            self._create_action()
        else:
            raise ValueError('Input must be a TreeModel!')

    def _create_action(self):
        """Create several necessary actions."""
        # When select one item, display specific parameters
        self._tree_view.selectionModel().currentChanged.connect(self._disp_current_para)

        # When select one item, display its undo/redo settings
        self._tree_view.selectionModel().currentChanged.connect(self.current_changed)

        # When dataset changed, refresh display.
        self._model.dataChanged.connect(self._disp_current_para)

        # When add new item, refresh display.
        self._model.rowsInserted.connect(self._disp_current_para)

        # When remove new item, refresh display.
        self._model.rowsRemoved.connect(self._disp_current_para)

        # When layout changed, refresh display.
        self._model.layoutChanged.connect(self._disp_current_para)

        # Config setting actions
        self._view_min.editingFinished.connect(self._set_view_min)
        self._view_max.editingFinished.connect(self._set_view_max)
        self._colormap.currentIndexChanged.connect(self._set_colormap)
        self._visibility.sliderReleased.connect(self._set_alpha)
        self._up_button.clicked.connect(self._up_action)
        self._down_button.clicked.connect(self._down_action)

    def _disp_current_para(self):
        """Display current model's paraters."""
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
            # print str(self._model.data(index, Qt.UserRole))
            self._view_min.setText(str(self._model.data(index, Qt.UserRole)))
            self._view_max.setText(str(self._model.data(index, Qt.UserRole + 1)))

            # colormap combo box setting
            cur_colormap = self._model.data(index, Qt.UserRole + 3)
            if isinstance(cur_colormap, LabelConfig):
                cur_colormap = cur_colormap.get_name()
            idx = self._colormap.findText(cur_colormap)
            self._colormap.setCurrentIndex(idx)

            # alpha slider setting
            current_alpha = self._model.data(index, Qt.UserRole + 2) * 100 / 255
            self._visibility.setValue(current_alpha)

            self._tree_view.setFocus()

            # Set current index
            self._model.setCurrentIndex(self._tree_view.currentIndex())
            # self._model.setSelectedIndexes(self._tree_view.currentIndex())
            # print "exe"

    def _set_view_min(self):
        """Set current selected item's view_min value."""
        index = self._tree_view.currentIndex()
        value = self._view_min.text()
        if value == '':
            self._view_min.setText(str(self._model.data(index, Qt.UserRole)))
        else:
            self._model.setData(index, value, role=Qt.UserRole)

    def _set_view_max(self):
        """Set current selected item's view_max value."""
        index = self._tree_view.currentIndex()
        value = self._view_max.text()
        if value == '':
            self._view_max.setText(str(self._model.data(index, Qt.UserRole + 1)))
        else:
            self._model.setData(index, value, role=Qt.UserRole + 1)

    def _set_colormap(self):
        """Set colormap of current selected item."""
        index = self._tree_view.currentIndex()
        value = self._colormap.currentText()
        self._model.setData(index, value, role=Qt.UserRole + 3)

    def _set_alpha(self):
        """Set alpha value of current selected item."""
        index = self._tree_view.currentIndex()
        value = self._visibility.value() * 255 / 100
        self._model.setData(index, value, role=Qt.UserRole + 2)

    def _up_action(self):
        """Move selected item up for one step."""
        index = self._tree_view.currentIndex()
        self._model.moveUp(index)
        index = self._tree_view.currentIndex()
        if index.row() == 0:
            self._up_button.setEnabled(False)
        else:
            self._up_button.setEnabled(True)
        if index.row() == (self._model.rowCount(index.parent()) - 1):
            self._down_button.setEnabled(False)
        else:
            self._down_button.setEnabled(True)
        self._tree_view.setFocus()

    def _down_action(self):
        """Move selected item down for one step."""
        index = self._tree_view.currentIndex()
        self._model.moveDown(index)
        index = self._tree_view.currentIndex()
        if index.row() == 0:
            self._up_button.setEnabled(False)
        else:
            self._up_button.setEnabled(True)
        if index.row() == (self._model.rowCount(index.parent()) - 1):
            self._down_button.setEnabled(False)
        else:
            self._down_button.setEnabled(True)
        self._tree_view.setFocus()


if __name__ == '__main__':
    db_dir = r'/nfs/t1/nsppara/corticalsurface'

    app = QApplication(sys.argv)

    # model init
    hemisphere_list = []
    surf1 = os.path.join(db_dir, 'S0001', 'surf', 'lh.white')
    surf2 = os.path.join(db_dir, 'S0001', 'surf', 'rh.white')
    s1 = os.path.join(db_dir, 'S0001', 'surf', 'lh.thickness')
    s2 = os.path.join(db_dir, 'S0001', 'surf', 'lh.curv')
    s3 = os.path.join(db_dir, 'S0001', 'surf', 'rh.thickness')
    s4 = os.path.join(db_dir, 'S0001', 'surf', 'rh.curv')

    h1 = Hemisphere(surf1)
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
    view = TreeView()
    view.setModel(model)
    view.setWindowTitle("Hemisphere Tree Model")
    view.show()
    sys.exit(app.exec_())
