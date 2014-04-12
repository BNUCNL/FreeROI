__author__ = 'zhouguangfu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool

class BinarizationDialog(QDialog):
    """
    A dialog for action of binaryzation.

    """
    def __init__(self, model, parent=None):
        super(BinarizationDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Binarization")

        # initialize widgets
        source_label = QLabel("Source")
        self.source_combo = QComboBox()
        threshold_label = QLabel("Threshold")
        self.threshold_edit = QLineEdit()
        self.threshold_edit.setText(str(int(self._model._data[self._model.currentIndex().row()].get_view_min())))
        vol_list = self._model.getItemList()
        self.source_combo.addItems(vol_list)
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)
        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(threshold_label, 0, 0)
        grid_layout.addWidget(self.threshold_edit, 0, 1)
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
        self.threshold_edit.editingFinished.connect(self._create_output)
        self.run_button.clicked.connect(self._binaryzation)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        source_name = self.source_combo.currentText()
        output_name = '_'.join(['bin', str(source_name)])
        self.out_edit.setText(output_name)

    def _binaryzation(self):
        vol_name = str(self.out_edit.text())
        threshold = self.threshold_edit.text()

        if not vol_name:
            self.out_edit.setFocus()
            return
        if not threshold:
            self.threshold_edit.setFocus()
            return

        try:
            threshold = int(threshold)
        except ValueError:
            self.threshold_edit.selectAll()
            return

        source_row = self.source_combo.currentIndex()
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 6)
        new_vol = imtool.binaryzation(source_data, threshold)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header())
        self.done(0)

