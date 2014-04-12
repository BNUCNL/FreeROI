# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool

class RegularROIDialog(QDialog):
    """
    A dialog for generate a regular ROI

    """

    def __init__(self, model, parent=None):
        super(RegularROIDialog, self).__init__(parent)
        self._model = model 

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("Generate Regular ROI based on seeds image")

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
        grid_layout.addWidget(roi_type_label, 0, 0)
        grid_layout.addWidget(self.roi_type_edit, 0, 1)
        grid_layout.addWidget(radius_label, 1, 0)
        grid_layout.addWidget(self.radius_edit, 1, 1)
        grid_layout.addWidget(out_label, 2, 0)
        grid_layout.addWidget(self.out_edit, 2, 1)

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
        self.cancel_button.clicked.connect(self.done)

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
        
        center_data = self._model.data(self._model.currentIndex(),
                                       Qt.UserRole + 6)
        coord_list, value_list = imtool.nonzero_coord(center_data)
        data = center_data.copy()
        for idx in range(len(coord_list)):
            data = roi_generater(data, coord_list[idx][0],
                                 coord_list[idx][1], coord_list[idx][2],
                                 radius, value_list[idx])
        self._model.addItem(data,
                            None,
                            out,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        self.done(0)

