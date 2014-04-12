# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool

class SmoothingDialog(QDialog):
    """
    A dialog for image smoothing.

    """
    def __init__(self, model, parent=None):
        super(SmoothingDialog, self).__init__(parent)
        self._model = model
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Smoothing")

        # initialize widgets
        sigma_label = QLabel("Sigma")
        self.sigma_edit = QLineEdit()
        row = self._model.currentIndex().row()
        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()
        self._create_output()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(sigma_label, 0, 0)
        grid_layout.addWidget(self.sigma_edit, 0, 1)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.out_edit, 1, 1)

        # button config
        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        notes_label = QLabel("Notes: FWHM = 2.3548 * sigma\nSigma is specified in voxels.")
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)
        vbox_layout.addWidget(notes_label)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.run_button.clicked.connect(self._smooth)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        current_row = self._model.currentIndex().row()
        vol_name = self._model.data(self._model.index(current_row),
                                    Qt.DisplayRole)
        output_name = '_'.join(['sm', str(vol_name)])
        self.out_edit.setText(output_name)

    def _smooth(self):
        vol_name = str(self.out_edit.text())
        sigma = self.sigma_edit.text()

        if not vol_name:
            self.out_edit.setFocus()
            return
        if not sigma:
            self.sigma_edit.setFocus()
            return

        try:
            sigma = float(sigma)
        except ValueError:
            self.sigma_edit.selectAll()
            return

        current_row = self._model.currentIndex().row()
        source_data = self._model.data(self._model.index(current_row),
                                       Qt.UserRole + 6)
        new_vol = imtool.gaussian_smoothing(source_data, sigma)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header())
        self.done(0)

