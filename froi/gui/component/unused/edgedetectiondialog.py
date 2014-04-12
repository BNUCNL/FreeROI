# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool

class Edge_detectionDialog(QDialog):
    """
    A dialog for action of edge_detection.

    """
    def __init__(self, model, parent=None):
        super(Edge_detectionDialog, self).__init__(parent)
        self._model = model
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Edge_detection")

        # initialize widgets
        source_label = QLabel("Source")
        self.source_combo = QComboBox()

        vol_list = self._model.getItemList()
        self.source_combo.addItems(vol_list)
        row = self._model.currentIndex().row()

        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(source_label, 0, 0)
        grid_layout.addWidget(self.source_combo, 0, 1)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.out_edit, 1, 1)

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
        self.source_combo.currentIndexChanged.connect(self._create_output)
        self.run_button.clicked.connect(self._edge_detection)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        source_name = self.source_combo.currentText()
        output_name = '_'.join([str(source_name), 'edge'])
        self.out_edit.setText(output_name)

    def _edge_detection(self):
        vol_name = str(self.out_edit.text())

        if not vol_name:
            self.out_edit.setFocus()
            return

        source_row = self.source_combo.currentIndex()
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 5)
        new_vol = imtool.multi_label_edge_detection(source_data)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'green')
        self.done(0)
