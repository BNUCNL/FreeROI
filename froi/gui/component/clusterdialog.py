# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool

class ClusterDialog(QDialog):
    """
    A dialog for cluster processing.

    """
    def __init__(self, model, parent=None):
        super(ClusterDialog, self).__init__(parent)
        self._model = model
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Cluster")

        # initialize widgets
        threshold_label = QLabel("Threshold")
        self.threshold_edit = QLineEdit()
        row = self._model.currentIndex().row()
        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()
        self._create_output()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(threshold_label, 0, 0)
        grid_layout.addWidget(self.threshold_edit, 0, 1)
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

    def _create_actions(self):
        self.run_button.clicked.connect(self._cluster)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        current_row = self._model.currentIndex().row()
        vol_view_min = self._model.data(self._model.index(current_row),
                                        Qt.UserRole)
        self.threshold_edit.setText(str(vol_view_min))
        vol_name = self._model.data(self._model.index(current_row),
                                    Qt.DisplayRole)
        output_name = '_'.join(['cluster', str(vol_name)])
        self.out_edit.setText(output_name)

    def _cluster(self):
        vol_name = str(self.out_edit.text())
        threshold = self.threshold_edit.text()

        if not vol_name:
            self.out_edit.setFocus()
            return
        if not threshold:
            self.threshold_edit.setFocus()
            return

        try:
            threshold = float(threshold)
        except ValueError:
            self.threshold_edit.selectAll()
            return

        current_row = self._model.currentIndex().row()
        source_data = self._model.data(self._model.index(current_row),
                                       Qt.UserRole + 6)
        new_vol = imtool.cluster_labeling(source_data, threshold)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        self.done(0)

