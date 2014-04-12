# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool

class ROIFilterDialog(QDialog):
    """
    A dialog for action of intersection.

    """
    last_mask_idx = 0
    def __init__(self, model, parent=None):
        super(ROIFilterDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("ROI Filter")

        # initialize widgets
        source_label = QLabel("Source")
        self.source_combo = QComboBox()
        mask_label = QLabel("Mask")
        self.mask_combo = QComboBox()
        vol_list = self._model.getItemList()
        self.source_combo.addItems(QStringList(vol_list))
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)
        self.mask_combo.addItems(QStringList(vol_list))
        self.mask_combo.setCurrentIndex(self.last_mask_idx)
        filter_label = QLabel("Filter")
        self.filter_combo = QComboBox()
        mask_row = self.mask_combo.currentIndex()
        mask_config, current_idx = self._model.data(self._model.index(mask_row),
                                       Qt.UserRole + 7)
        if mask_config is not None:
            roi_list = mask_config.get_label_list()
        else:
            roi_list = []
        self.filter_combo.addItems(QStringList(roi_list))
        if roi_list:
            self.filter_combo.setCurrentIndex(current_idx.row())

        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()
        self._create_output()

        # layout config
        grid_layout = QGridLayout()
        #grid_layout.addWidget(source_label, 0, 0)
        #grid_layout.addWidget(self.source_combo, 0, 1)
        grid_layout.addWidget(mask_label, 0, 0)
        grid_layout.addWidget(self.mask_combo, 0, 1)
        grid_layout.addWidget(filter_label, 1, 0)
        grid_layout.addWidget(self.filter_combo, 1, 1)
        grid_layout.addWidget(out_label, 2, 0)
        grid_layout.addWidget(self.out_edit, 2, 1)

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

    def _create_actions(self):
        self.mask_combo.currentIndexChanged.connect(self._update_filters)
        self.filter_combo.currentIndexChanged.connect(self._create_output)

        self.run_button.clicked.connect(self._run_filter)
        self.cancel_button.clicked.connect(self.done)

    def _update_filters(self):
        mask_row = self.mask_combo.currentIndex()
        #mask_config = self._model.data(self._model.index(mask_row),
        #                               Qt.UserRole + 7)
        #if mask_config is not None:
        #    roi_list = mask_config.get_label_list()
        #else:
        #    roi_list = []
        #self.filter_combo.clear()
        #self.filter_combo.addItems(QStringList(roi_list))
        ROIFilterDialog.last_mask_idx = mask_row

    def _create_output(self):
        output_name = self.filter_combo.currentText()
        self.out_edit.setText(output_name)

    def _run_filter(self):
        """
        Run an intersecting processing.

        """
        vol_name = str(self.out_edit.text())
        source_row = self.source_combo.currentIndex()
        mask_row = self.mask_combo.currentIndex()
        filter = str(self.filter_combo.currentText())
        
        if not vol_name:
            self.out_edit.setFocus()
            return
        if not filter:
            self.filter_combo.setFocus()
            return
        
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 6)
        mask_data = self._model.data(self._model.index(mask_row),
                                     Qt.UserRole + 6)
        mask_config, _ = self._model.data(self._model.index(mask_row),
                                       Qt.UserRole + 7)
        filter_index = mask_config.get_label_index(filter)
        mask_data[mask_data != filter_index] = 0
        new_vol = imtool.roi_filtering(source_data, mask_data)
        self._model.addItem(new_vol, 
                            None,
                            vol_name,
                            self._model._data[0].get_header(), 
                            None, None, 255, 'rainbow')
        self.done(0)
