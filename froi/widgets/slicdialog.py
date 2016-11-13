# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from skimage.segmentation import slic

class SLICDialog(QDialog):
    """A dialog for SLIC options."""

    def __init__(self, model, main_win, parent=None):
        super(SLICDialog, self).__init__(parent)
        self._model = model 
        self._main_win = main_win
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("SLIC")
        self.vol_combo = QComboBox()
        # self.vol_combo.addItems(QStringList(self._model.getItemList()))
        self.vol_combo.addItems(self._model.getItemList())
        row = self._model.currentIndex().row()
        self.vol_combo.setCurrentIndex(row)

        n_segments_label = QLabel("N Segmentats")
        self.n_segments_edit = QLineEdit('5000')
        compactness_label = QLabel("Compactness")
        self.compactness_edit = QLineEdit('10')
        slic_zero_label = QLabel("Slic Zero")
        self.slic_zero_checkbox = QCheckBox()
        self.slic_zero_checkbox.setChecked(False)
        sigma_label = QLabel("Sigma")
        self.sigma_edit = QLineEdit('2')
        out_label = QLabel("Output")
        self.out_edit = QLineEdit()
        self._create_output()

        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")
        
        grid_layout = QGridLayout()
        #grid_layout.addWidget(vol_label, 0, 0)
        #grid_layout.addWidget(self.vol_combo, 0, 1)
        grid_layout.addWidget(n_segments_label, 0, 0)
        grid_layout.addWidget(self.n_segments_edit, 0, 1)
        grid_layout.addWidget(compactness_label, 1, 0)
        grid_layout.addWidget(self.compactness_edit, 1, 1)
        grid_layout.addWidget(slic_zero_label, 2, 0)
        grid_layout.addWidget(self.slic_zero_checkbox, 2, 1)
        grid_layout.addWidget(sigma_label, 3, 0)
        grid_layout.addWidget(self.sigma_edit, 3, 1)
        grid_layout.addWidget(out_label, 4, 0)
        grid_layout.addWidget(self.out_edit, 4, 1)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.vol_combo.currentIndexChanged.connect(self._create_output)
        self.slic_zero_checkbox.clicked.connect(self._disable_compactness)
        self.run_button.clicked.connect(self._slic)
        self.cancel_button.clicked.connect(self.done)

    def _disable_compactness(self):
        if self.slic_zero_checkbox.isChecked():
            self.compactness_edit.setEnabled(False)
        else:
            self.compactness_edit.setEnabled(True)

    def _create_output(self):
        vol_name = self.vol_combo.currentText()
        output_name = '_'.join([str(vol_name), 'sv'])
        self.out_edit.setText(output_name)

    def _slic(self):
        import numpy as np
        n_segments = self.n_segments_edit.text()
        compactness = self.compactness_edit.text()
        slic_zero_checked = self.slic_zero_checkbox.isChecked()
        sigma = self.sigma_edit.text()
        out = self.out_edit.text()

        if not n_segments:
            self.n_segments_edit.setFocus()
            return
        if not compactness:
            self.compactness_edit.setFocus()
            return
        if not sigma:
            self.sigma_edit.setFocus()
            return
        if not out:
            self.out_edit.setFocus()
            return

        try:
            n_segments = int(n_segments)
        except ValueError:
            self.n_segments_edit.selectAll()
            return
        try:
            compactness = int(compactness)
        except ValueError:
            self.compactness_edit.selectAll()
            return
        try:
            sigma = float(sigma)
        except ValueError:
            self.sigma_edit.selectAll()
            return
        try:
            out = str(out)
        except ValueError:
            self.out_edit.setFocus()
            return

        if n_segments <=0 or compactness <=0 or sigma <= 0:
            return

        vol_data = self._model.data(self._model.index(self.vol_combo.currentIndex()), Qt.UserRole + 6)
        if len(vol_data.shape) > 3:
            return
        gray_image = (vol_data - vol_data.min()) * 255.0 / (vol_data.max() - vol_data.min())

        new_vol = slic(gray_image.astype(np.float),
                       n_segments=n_segments,
                       compactness=compactness,
                       sigma=sigma,
                       slic_zero=slic_zero_checked,
                       multichannel =False,
                       enforce_connectivity=True)
        self._model.addItem(new_vol,
                            None,
                            out,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        self.done(0)
