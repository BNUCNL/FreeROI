#!/usr/bin/env python
#code by Dangxiaobin at 2013-11-28

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import roi2gwmi as r2i


class Roi2gwmiDialog(QDialog):
    """
    A dialog for action of intersection.

    """
    def __init__(self, model, parent=None):
        super(Roi2gwmiDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.
        """
        # set dialog title
        self.setWindowTitle("Project ROI to interface")

        # initialize widgets
        self.mode_list = ['bin','count','value']
        self.source_label = QLabel("ROI volume:")
        self.interface_label = QLabel("Target volume:")
        self.mode_label = QLabel(" Threshold mode:")
        self.roi_volume = QComboBox()
        self.interface_volume = QComboBox()
        
        self.modeComboBox = QComboBox()
        self.modeComboBox.addItems(self.mode_list)
        self.thr_label = QLabel(" Threshold :")
        self.thr_edit = QLineEdit()
        self.thr_edit.setText("1.0")
        
        vol_list = self._model.getItemList()
        self.roi_volume.addItems(vol_list)
        self.interface_volume.addItems(vol_list)
        
        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.source_label, 0, 0)
        grid_layout.addWidget(self.roi_volume, 0, 1)
        grid_layout.addWidget(self.interface_label, 1, 0)
        grid_layout.addWidget(self.interface_volume, 1, 1)
        grid_layout.addWidget(self.mode_label, 2,0)
        grid_layout.addWidget(self.modeComboBox, 2,1)
        grid_layout.addWidget(self.thr_label, 3,0)
        grid_layout.addWidget(self.thr_edit, 3,1)

        grid_layout.addWidget(out_label, 4, 0)
        grid_layout.addWidget(self.out_edit, 4, 1)

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
        self.roi_volume.currentIndexChanged.connect(self._create_output)
        self.run_button.clicked.connect(self._roi2interface)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        source_name = self.roi_volume.currentText()
        output_name = '_'.join([str(source_name), 'interface'])
        self.out_edit.setText(output_name)

    def _roi2interface(self):
        vol_name = str(self.out_edit.text())
        
        roi_volume = self.roi_volume.currentIndex()
        interface_volume = self.interface_volume.currentIndex()
        mode = self.modeComboBox.currentIndex()
        thr = self.thr_edit.text()
        roi_data = self._model.data(self._model.index(roi_volume),
                                       Qt.UserRole + 5)
        interface_data = self._model.data(self._model.index(interface_volume),
                                       Qt.UserRole + 5)
       
        new_vol =r2i.roi_projection(roi_data, interface_data,100,thr,mode)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'red')

        self.done(0)


