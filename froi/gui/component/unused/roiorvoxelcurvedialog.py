__author__ = 'zhouguangfu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.gui.component.voxeltimepointcurvedialog import VoxelTimePointCurveDialog

class ROIOrVoxelCurveDialog(QDialog):
    """
    A dialog for action of binarydilation.

    """
    listview_current_index_change = pyqtSignal()

    def __init__(self, model, parent=None):
        super(ROIOrVoxelCurveDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("RoiOrVoxelCurveDialog")

        # initialize widgets
        self.ROI_radio = QRadioButton("ROI")
        self.voxel_raido = QRadioButton("Voxel")
        self.voxel_raido.setChecked(True)

        mask_label = QLabel("ROI Mask")
        self.mask_combo = QComboBox()
        vol_list = self._model.getItemList()
        self.mask_combo.addItems(vol_list)
        row = self._model.currentIndex().row()
        self.mask_combo.setCurrentIndex(row)
        self.mask_combo.setEnabled(False)

        # data_label = QLabel("Data")
        # self.data_combo = QComboBox()
        # self.data_combo.addItems(vol_list)
        # row = self._model.currentIndex().row()
        # self.data_combo.setCurrentIndex(row)

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.voxel_raido, 0, 0)
        grid_layout.addWidget(self.ROI_radio, 0, 1)
        grid_layout.addWidget(mask_label, 1, 0)
        grid_layout.addWidget(self.mask_combo, 1, 1)
        # grid_layout.addWidget(data_label, 2, 0)
        # grid_layout.addWidget(self.data_combo, 2, 1)

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
        self._create_actions()

    def _create_actions(self):
        self.voxel_raido.clicked.connect(self._roi_or_voxel_selected)
        self.ROI_radio.clicked.connect(self._roi_or_voxel_selected)
        self.run_button.clicked.connect(self._ROI_or_voxel_curve_display)
        self.cancel_button.clicked.connect(self.done)

    def _roi_or_voxel_selected(self):
        """
        Select a voxel or a region of interest.

        """
        if self.voxel_raido.isChecked():
            self.mask_combo.setEnabled(False)
        else:
            self.mask_combo.setEnabled(True)
    def listview_current_index_changed(self):
        self.listview_current_index_change.emit()

    def _ROI_or_voxel_curve_display(self):
        mask_row = self.mask_combo.currentIndex()

        self.voxeltimepointcurve = VoxelTimePointCurveDialog(self._model, self.voxel_raido.isChecked(), mask_row)
        self.listview_current_index_change.connect(self.voxeltimepointcurve._plot)
        self.voxeltimepointcurve.setModal(False)
        self.voxeltimepointcurve.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.voxeltimepointcurve.show()
        self.close()




