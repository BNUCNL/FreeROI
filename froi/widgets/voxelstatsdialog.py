# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..algorithm import imtool


class VoxelStatsDialog(QDialog):
    """A dialog for voxel stats."""
    def __init__(self, model, parent=None):
        super(VoxelStatsDialog, self).__init__(parent)
        self._model = model

        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Tool | \
                            Qt.CustomizeWindowHint | \
                            Qt.WindowTitleHint)

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("Voxel Number Stats")

        # initialize widgets
        value_label = QLabel("Voxel intensity")
        self.value_edit = QLineEdit()
        self.value_edit.setReadOnly(True)
        xyz = self._model.get_cross_pos()
        value = self._model.get_current_value([xyz[0], xyz[1], xyz[2]])
        self.value_edit.setText(str(value))
        out_label = QLabel("Voxel Number")
        self.stats_edit = QLineEdit()
        self.stats_edit.setReadOnly(True)

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(value_label, 0, 0)
        grid_layout.addWidget(self.value_edit, 0, 1)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.stats_edit, 1, 1)

        # button config
        self.cancel_button = QPushButton("Cancel")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self._model.cross_pos_changed.connect(self._voxel_stats)
        self.cancel_button.clicked.connect(self._close_dialog)

    def _voxel_stats(self):
        xyz = self._model.get_cross_pos()
        vxl_value = self._model.get_current_value([xyz[0], xyz[1], xyz[2]])
        self.value_edit.setText(str(vxl_value))

        current_row = self._model.currentIndex().row()
        source_data = self._model.data(self._model.index(current_row),
                                       Qt.UserRole + 6)
        vxl_num = imtool.voxel_number(source_data, vxl_value)
        self.stats_edit.setText(str(vxl_num))

    def _close_dialog(self):
        self.hide()

