# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool


class AutoLabelDialog(QDialog):
    """
    A dialog for auto labeling.
    
    """

    def __init__(self, model, parent=None):
        super(AutoLabelDialog, self).__init__(parent)

        self._model = model
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("Auto Labeling")

        src_label = QLabel("Source")
        self.src_combo = QComboBox()
        tar_label = QLabel("Target")
        self.tar_combo = QComboBox()
        vol_list = self._model.getItemList()
        self.src_combo.addItems(QStringList(vol_list))
        self.tar_combo.addItems(QStringList(vol_list))
        method_label = QLabel("Method")
        self.method_combo = QComboBox()
        self.method_combo.addItem(QString("Nearest"))
        out_label = QLabel("Output")
        self.out_edit = QLineEdit()
        
        grid_layout = QGridLayout()
        grid_layout.addWidget(src_label, 0, 0)
        grid_layout.addWidget(self.src_combo, 0, 1)
        grid_layout.addWidget(tar_label, 1, 0)
        grid_layout.addWidget(self.tar_combo, 1, 1)
        grid_layout.addWidget(method_label, 2, 0)
        grid_layout.addWidget(self.method_combo, 2, 1)
        grid_layout.addWidget(out_label, 3, 0)
        grid_layout.addWidget(self.out_edit, 3, 1)

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
        self.run_button.clicked.connect(self._auto_label)
        self.cancel_button.clicked.connect(self.done)

    def _auto_label(self):
        out_name = str(self.out_edit.text())
        if not out_name:
            self.out_edit.setFocus()
            return

        src_row = self.src_combo.currentIndex()
        tar_row = self.tar_combo.currentIndex()
        src_data = self._model.data(self._model.index(src_row),
                                     Qt.UserRole + 5)
        tar_data = self._model.data(self._model.index(tar_row),
                                       Qt.UserRole + 5)
        new_vol = imtool.nearest_labeling(src_data, tar_data)
        self._model.addItem(new_vol,
                            self._model._data[src_row].label_config,
                            out_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'label')
        self.done(0)
