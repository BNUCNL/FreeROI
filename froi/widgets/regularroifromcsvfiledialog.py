# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool
from ..interface.csv import get_cord_from_file

import numpy as np
import os

class RegularROIFromCSVFileDialog(QDialog):
    """A dialog for generate a regular ROI."""

    def __init__(self, model, parent=None):
        super(RegularROIFromCSVFileDialog, self).__init__(parent)
        self._model = model
        self._temp_dir = None

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("Generate Regular ROI based on CSV file")

        cordinate_file_label= QLabel('Cordinate File :')
        self._cordinate_file_dir = QLineEdit('')
        self._cordinate_file_dir.setReadOnly(True)
        self._cordinate_file_button = QPushButton('Browse')

        out_label = QLabel("Output")
        self.out_edit = QLineEdit()
        self._create_output()

        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")

        grid_layout = QGridLayout()

        grid_layout.addWidget(cordinate_file_label, 0, 0)
        grid_layout.addWidget(self._cordinate_file_dir, 0, 1)
        grid_layout.addWidget(self._cordinate_file_button, 0, 2)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.out_edit, 1, 1, 1, 2)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.run_button.clicked.connect(self._regular_roi)
        self._cordinate_file_button.clicked.connect(self._cordinate_file_browse)
        self.cancel_button.clicked.connect(self.done)

    def _cordinate_file_browse(self):
        cordinate_file_filepath = self._open_file_dialog("Add cordinate txt file.")
        if cordinate_file_filepath is not None:
            self._temp_dir = os.path.dirname(cordinate_file_filepath)
            self._cordinate_file_dir.setText(cordinate_file_filepath)

    def _open_file_dialog(self, title):
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_name = QFileDialog.getOpenFileName(self,
                                                title,
                                                temp_dir,
                                                "Cordinate files (*.txt *.csv)")
        import sys
        file_path = None
        if not file_name.isEmpty():
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
        return file_path

    def _update_output_name(self):
        row = self._model.currentIndex()
        vol_name = self._model.data(row, Qt.DisplayRole)
        output_name = '_'.join([str(vol_name), str('sphere'), 'ROI'])
        self.out_edit.setText(output_name)

    def _create_output(self):
        self._update_output_name()

    def _regular_roi(self):
        out = self.out_edit.text()
        cord_filepath = str(self._cordinate_file_dir.text())

        if not out:
            self.out_edit.setFocus()
            return

        roi_generater = imtool.sphere_roi

        header = self._model.data(self._model.currentIndex(), Qt.UserRole + 11)
        image_affine = self._model.get_affine()
        data = self._model.data(self._model.currentIndex(), Qt.UserRole + 6)
        new_data = np.zeros_like(data).astype(np.uint32)
        try:
            coord_list, radius_list, id_list = get_cord_from_file(header, cord_filepath, image_affine)
        except ValueError, error_info:
            QMessageBox.critical(self, 'Please check the cordinate in the file.', str(error_info))
            return

        for idx in range(len(coord_list)):
            new_data = roi_generater(new_data, coord_list[idx][0],
                                    coord_list[idx][1], coord_list[idx][2],
                                    radius_list[idx], id_list[idx])
        self._model.addItem(new_data,
                            None,
                            out,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        self.done(0)


