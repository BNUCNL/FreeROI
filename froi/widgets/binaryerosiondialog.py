
__author__ = 'zhouguangfu, chenxiayu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
from scipy.ndimage import morphology

from froi.algorithm.meshtool import binary_shrink


class BinErosionDialog(QDialog):
    """A dialog for action of binary erosion."""
    def __init__(self, model, parent=None):
        super(BinErosionDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("BinaryErosion")

        # initialize widgets
        structure_label = QLabel("Structure")
        self.structure_combo = QComboBox()
        out_label = QLabel("Output name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(structure_label, 0, 0)
        grid_layout.addWidget(self.structure_combo, 0, 1)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.out_edit, 1, 1)

        # button config
        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.run_button.clicked.connect(self._binary_erosion)
        self.cancel_button.clicked.connect(self.done)

    def _binary_erosion(self):
        raise NotImplementedError


class VolBinErosionDialog(BinErosionDialog):

    def __init__(self, model, parent=None):
        super(VolBinErosionDialog, self).__init__(model, parent)

        self.index = self._model.currentIndex()

        # fill output editor
        source_name = self._model.data(self.index, Qt.DisplayRole)
        output_name = '_'.join(['binErosion', source_name])
        self.out_edit.setText(output_name)

        # fill structure combo box
        self.structure_combo.addItem("3x3x3")
        self.structure_combo.addItem("4x4x4")
        self.structure_combo.addItem("5x5x5")
        self.structure_combo.addItem("6x6x6")

    def _binary_erosion(self):
        vol_name = str(self.out_edit.text())
        num = self.structure_combo.currentIndex() + 3
        structure = np.ones((num, num, num), dtype=np.int8)

        if not vol_name:
            self.out_edit.setFocus()
            return

        source_data = self._model.data(self.index, Qt.UserRole + 6)
        binary_vol = source_data > self._model.data(self.index, Qt.UserRole)

        new_vol = morphology.binary_erosion(binary_vol,
                                            structure=structure)
        self._model.addItem(new_vol.astype(np.int8),
                            name=vol_name,
                            header=self._model.data(self.index, Qt.UserRole + 11))
        self.done(0)


class SurfBinErosionDialog(BinErosionDialog):

    def __init__(self, model, parent=None):
        super(SurfBinErosionDialog, self).__init__(model, parent)

        self.index = self._model.current_index()
        depth = self._model.index_depth(self.index)
        if depth != 2:
            QMessageBox.warning(self,
                                'Warning!',
                                'Get overlay failed!\nYou may have not selected any overlay!',
                                QMessageBox.Yes)
            # raise error to prevent dialog from being created
            raise RuntimeError("You may have not selected any overlay!")

        # fill output editor
        source_name = self._model.data(self.index, Qt.DisplayRole)
        output_name = '_'.join(['binErosion', source_name])
        self.out_edit.setText(output_name)

        # fill structure combo box
        self.structure_combo.addItem("1-ring")
        self.structure_combo.addItem("2-ring")
        self.structure_combo.addItem("3-ring")
        self.structure_combo.addItem("4-ring")

    def _binary_erosion(self):
        out_name = str(self.out_edit.text())
        n_ring = self.structure_combo.currentIndex() + 1

        if not out_name:
            self.out_edit.setFocus()
            return

        source_data = self._model.data(self.index, Qt.UserRole + 5)
        if self._model.data(self.index, Qt.UserRole + 7):
            bin_data = source_data != 0
        else:
            bin_data = source_data > self._model.data(self.index, Qt.UserRole)

        new_data = binary_shrink(bin_data,
                                 faces=self._model.data(self.index.parent(), Qt.UserRole + 6).faces,
                                 n=n_ring)
        self._model.add_item(self.index,
                             source=new_data.astype(np.int8),
                             colormap="blue",
                             islabel=True,
                             name=out_name)
        self.done(0)
