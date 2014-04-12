# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool
from froi.io import csv

class MeanTSDialog(QDialog):
    """
    A dialog for action of intersection.

    """
    def __init__(self, model, parent=None):
        super(MeanTSDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Export Mean Time Course")

        # initialize widgets
        self.source_combo = QComboBox()
        mask_label = QLabel("Mask")
        self.mask_combo = QComboBox()
        vol_list = self._model.getItemList()
        self.source_combo.addItems(QStringList(vol_list))
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)
        self.mask_combo.addItems(QStringList(vol_list))

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(mask_label, 0, 0)
        grid_layout.addWidget(self.mask_combo, 0, 1)

        # button config
        self.run_button = QPushButton("Export...")
        self.cancel_button = QPushButton("Cancel")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.run_button.clicked.connect(self._export)
        self.cancel_button.clicked.connect(self.done)

    def _export(self):
        """
        Export mean time course.

        """
        source_name = self.source_combo.currentText()
        mask_name = self.mask_combo.currentText()
        output_name = '_'.join([str(source_name), str(mask_name)]) + '.csv'
        file_path = os.path.join(str(QDir.currentPath()), output_name)
        path = QFileDialog.getSaveFileName(self, 'Save file as ...',
                                           file_path, 'csv files (*.csv *.txt)')
        if not path.isEmpty():
            source_row = self.source_combo.currentIndex()
            mask_row = self.mask_combo.currentIndex()
            source_data = self._model.data(self._model.index(source_row),
                                           Qt.UserRole + 6)
            mask_data = self._model.data(self._model.index(mask_row),
                                         Qt.UserRole + 5)
            meants = imtool.extract_mean_ts(source_data, mask_data) 
            meants = meants.tolist()
            csv.save2csv(meants, path)
            self.done(0)

