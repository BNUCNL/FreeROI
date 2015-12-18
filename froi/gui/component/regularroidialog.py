# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool
from froi.io.csv import get_cord_from_file


class RegularROIDialog(QDialog):
    """A dialog for generate a regular ROI."""

    def __init__(self, model, parent=None):
        super(RegularROIDialog, self).__init__(parent)
        self._model = model
        self._temp_dir = None

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("Generate Regular ROI based on seeds image")

        self._seed_image_radio = QRadioButton("Seed Image :")
        self._seed_image_combo = QComboBox()
        vol_list = self._model.getItemList()
        self._seed_image_combo.addItems(QStringList(vol_list))
        self._seed_image_radio.setChecked(True)

        self._cordinate_file_radio= QRadioButton('Cordinate File :')
        self._cordinate_file_dir = QLineEdit('')
        self._cordinate_file_dir.setReadOnly(True)
        self._cordinate_file_button = QPushButton('Browse')
        self._cordinate_file_radio.setChecked(False)
        self._cordinate_file_button.setEnabled(False)
        self._cordinate_file_dir.setEnabled(False)

        radio_button_group = QButtonGroup()
        radio_button_group.addButton(self._seed_image_radio)
        radio_button_group.addButton(self._cordinate_file_radio)

        radius_label = QLabel("Radius of ROI (voxel)")
        self.radius_edit = QLineEdit()
        
        roi_type_label = QLabel("ROI shape")
        self.roi_type_edit = QComboBox()
        self.roi_type_edit.addItems(["Sphere", "Cube"])

        out_label = QLabel("Output")
        self.out_edit = QLineEdit()
        self._create_output()

        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")
        
        grid_layout = QGridLayout()
        grid_layout.addWidget(self._seed_image_radio, 0, 0)
        grid_layout.addWidget(self._seed_image_combo, 0, 1, 1, 2)
        grid_layout.addWidget(self._cordinate_file_radio, 1, 0)
        grid_layout.addWidget(self._cordinate_file_dir, 1, 1)
        grid_layout.addWidget(self._cordinate_file_button, 1, 2)
        grid_layout.addWidget(roi_type_label, 2, 0)
        grid_layout.addWidget(self.roi_type_edit, 2, 1, 1, 2)
        grid_layout.addWidget(radius_label, 3, 0)
        grid_layout.addWidget(self.radius_edit, 3, 1, 1, 2)
        grid_layout.addWidget(out_label, 4, 0)
        grid_layout.addWidget(self.out_edit, 4, 1, 1, 2)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.roi_type_edit.currentIndexChanged.connect(self._update_output_name)

        self.run_button.clicked.connect(self._regular_roi)
        self._cordinate_file_button.clicked.connect(self._cordinate_file_browse)
        self._cordinate_file_radio.clicked.connect(self._cordinate_file_checked)
        self._seed_image_radio.clicked.connect(self._seed_image_checked)
        self.cancel_button.clicked.connect(self.done)

    def _seed_image_checked(self):
        self._seed_image_combo.setEnabled(True)
        self._cordinate_file_dir.setEnabled(False)
        self._cordinate_file_button.setEnabled(False)

    def _cordinate_file_checked(self):
        self._cordinate_file_button.setEnabled(True)
        self._cordinate_file_dir.setEnabled(True)
        self._seed_image_combo.setEnabled(False)

    def _cordinate_file_browse(self):
        import os
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
        shape_name = self.roi_type_edit.currentText()
        output_name = '_'.join([str(vol_name), str(shape_name), 'ROI'])
        self.out_edit.setText(output_name)

    def _create_output(self):
        self.radius_edit.setText('1')
        self._update_output_name()

    def _regular_roi(self):
        radius = self.radius_edit.text()
        shape = self.roi_type_edit.currentText()
        out = self.out_edit.text()
        cord_filepath = str(self._cordinate_file_dir.text())
        if cord_filepath is '' and self._cordinate_file_radio.isChecked():
            QMessageBox.critical(self, "The cordinate cannot be empty!", 'Please select the cordinate file.')
            return

        if not radius:
            self.radisu_edit.setFocus()
            return
        if not out:
            self.out_edit.setFocus()
            return
        
        try:
            radius = int(radius)
        except ValueError:
            self.radius_edit.selectAll()
            return
        try:
            shape = str(shape)
        except ValueError:
            self.roi_type_edit.setFocus()
            return
        try:
            out = str(out)
        except ValueError:
            self.out_edit.setFocus()
            return
        
        if shape == 'Sphere':
            roi_generater = imtool.sphere_roi
        elif shape == 'Cube':
            roi_generater = imtool.cube_roi

        if self._cordinate_file_radio.isChecked():
            target_data = self._model.data(self._model.index(self._seed_image_combo.currentIndex()),
                                       Qt.UserRole + 6)
            data = target_data.copy()
            try:
                coord_list, value_list, new_data = get_cord_from_file(data, cord_filepath, self._model.get_affine())
            except ValueError, error_info:
                QMessageBox.critical(self, 'Please check the cordinate in the file.', str(error_info))
                return
        else:
            center_data = self._model.data(self._model.currentIndex(),
                                           Qt.UserRole + 6)
            coord_list, value_list = imtool.nonzero_coord(center_data)
            new_data = center_data.copy()

        for idx in range(len(coord_list)):
            new_data = roi_generater(new_data, coord_list[idx][0],
                                    coord_list[idx][1], coord_list[idx][2],
                                    radius, value_list[idx])
        self._model.addItem(new_data,
                            None,
                            out,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        self.done(0)


