# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import segment

class WatershedDialog(QDialog):
    """
    A dialog for watershed options

    """

    def __init__(self, model, main_win, parent=None):
        super(WatershedDialog, self).__init__(parent)
        self._model = model 
        self._main_win = main_win
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("Watershed")

        vol_label = QLabel("Volume")
        self.vol_combo = QComboBox()
        seed_label = QLabel("Seed")
        self.seed_combo = QComboBox()
        vol_list = self._model.getItemList()
        self.vol_combo.addItems(QStringList(vol_list))
        row = self._model.currentIndex().row()
        self.vol_combo.setCurrentIndex(row)
        vol_list.append('Local Maxima')
        self.seed_combo.addItems(QStringList(vol_list))
        self.seed_combo.setCurrentIndex(self.seed_combo.count() - 1)
        sigma_label = QLabel("Sigma")
        self.sigma_edit = QLineEdit()
        sigma_vox_label = QLabel("voxels")
        thresh_label = QLabel("Thresh")
        self.thresh_edit = QLineEdit()
        
        sfx_label = QLabel("Segment Function")
        self.sfx_edit = QComboBox()
        self.sfx_edit.addItems(["Inverse", "Gradient", "Distance"])

        out_label = QLabel("Output")
        self.out_edit = QLineEdit()
        self._create_output()

        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")
        
        grid_layout = QGridLayout()
        #grid_layout.addWidget(vol_label, 0, 0)
        #grid_layout.addWidget(self.vol_combo, 0, 1)
        grid_layout.addWidget(seed_label, 0, 0)
        grid_layout.addWidget(self.seed_combo, 0, 1)
        grid_layout.addWidget(sigma_label, 1, 0)
        grid_layout.addWidget(self.sigma_edit, 1, 1)
        grid_layout.addWidget(sigma_vox_label, 1, 2)
        grid_layout.addWidget(thresh_label, 2, 0)
        grid_layout.addWidget(self.thresh_edit, 2, 1)
        grid_layout.addWidget(sfx_label, 3, 0)
        grid_layout.addWidget(self.sfx_edit, 3, 1)
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
        self.seed_combo.currentIndexChanged.connect(self._create_output)
        self.run_button.clicked.connect(self._watershed)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        vol_row = self.vol_combo.currentIndex()
        vol_view_min = self._model.data(self._model.index(vol_row),
                                        Qt.UserRole)

        self.sigma_edit.setText('1')
        self.thresh_edit.setText(str(vol_view_min))
        vol_name = self.vol_combo.currentText()
        output_name = '_'.join([str(vol_name), 'ws'])
        self.out_edit.setText(output_name)

    def _watershed(self):
        sigma = self.sigma_edit.text()
        thresh = self.thresh_edit.text()
        sfx = self.sfx_edit.currentText()
        out = self.out_edit.text()

        if not sigma:
            self.sigma_edit.setFocus()
            return
        if not thresh:
            self.thresh_edit.setFocus()
            return
        if not sfx:
            self.sfx_edit.setFocus()
            return
        if not out:
            self.out_edit.setFocus()
            return
        
        try:
            sigma = float(sigma)
        except ValueError:
            self.sigma_edit.selectAll()
            return
        try:
            thresh = float(thresh)
        except ValueError:
            self.thresh_edit.selectAll()
            return
        try:
            sfx = str(sfx)
        except ValueError:
            self.sfx_edit.setFocus()
            return
        try:
            out = str(out)
        except ValueError:
            self.out_edit.setFocus()
            return

        vol_row = self.vol_combo.currentIndex()
        seed_row = self.seed_combo.currentIndex()
        vol_data = self._model.data(self._model.index(vol_row),
                                    Qt.UserRole + 6)
        if seed_row < self._model.rowCount():
            seed_data = self._model.data(self._model.index(seed_row),
                                         Qt.UserRole + 6)
        else:
            seed_data = None
        
        if sfx == 'Inverse':
            sfx = segment.inverse_transformation
        elif sfx == 'Gradient':
            sfx = segment.gradient_transformation
        elif sfx == 'Distance':
            sfx = segment.distance_transformation
        else:
            raise ValueError, "Unkown segmentation fucntion"

        new_vol = segment.watershed(vol_data, sigma, thresh, seed_data, sfx)
        self._model.addItem(new_vol[2],
                            None,
                            out,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        #self._main_win.new_image_action()
        self.done(0)
