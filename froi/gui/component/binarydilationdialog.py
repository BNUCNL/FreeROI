__author__ = 'zhouguangfu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
from scipy.ndimage import morphology
from froi.algorithm import imtool

class BinarydilationDialog(QDialog):
    """
    A dialog for action of binarydilation.

    """
    def __init__(self, model, parent=None):
        super(BinarydilationDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Binarydilation")

        # initialize widgets
        source_label = QLabel("Source")
        self.source_combo = QComboBox()

        vol_list = self._model.getItemList()
        self.source_combo.addItems(vol_list)
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)

        structure_label = QLabel("Structure")
        self.structure_combo = QComboBox()
        self.structure_combo.addItem("3x3x3")
        self.structure_combo.addItem("5x5x5")
        self.structure_combo.addItem("7x7x7")
        self.structure_combo.addItem("9x9x9")
        # origin_label = QLabel("Origin")
        # self.origin_edit = QLineEdit()
        # self.origin_edit.setText('0')
        border_value_label = QLabel("BorderValue")
        self.border_value_combo = QComboBox()
        self.border_value_combo.addItem("0")
        self.border_value_combo.addItem("1")
        out_label = QLabel("Output volume name")
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
        self._create_output()

    def _create_actions(self):
        self.source_combo.currentIndexChanged.connect(self._create_output)
        self.run_button.clicked.connect(self._binary_dilation)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        source_name = self.source_combo.currentText()
        output_name = '_'.join([str(source_name), 'binarydilation'])
        self.out_edit.setText(output_name)

    def _binary_dilation(self):
        vol_name = str(self.out_edit.text())
        num = self.structure_combo.currentIndex() + 3
        self.structure_array = np.ones((num,num,num), dtype=np.int)
        # self.orgin = self.origin_edit.text()

        if not vol_name:
            self.out_edit.setFocus()
            return

        source_row = self.source_combo.currentIndex()
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 6)

        binary_vol = imtool.binaryzation(source_data,
                                    (source_data.max() + source_data.min()) / 2)
        new_vol = morphology.binary_dilation(binary_vol,
                                             structure=self.structure_array,
                                             border_value=1)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header())
        self.done(0)

