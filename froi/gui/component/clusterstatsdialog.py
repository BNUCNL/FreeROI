# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ClusterStatsDialog(QDialog):
    """
    A dialog for reporting cluster stats.

    """
    def __init__(self, cluster_info, parent=None):
        super(ClusterStatsDialog, self).__init__(parent)
        self._cluster_info = cluster_info
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Cluster Stats")

        # initialize widgets
        cluster_idx = QLabel("Cluster Index")
        peak_val = QLabel("Peak")
        peak_coord_x = QLabel("Peak X")
        peak_coord_y = QLabel("Peak Y")
        peak_coord_z = QLabel("Peak Z")
        cluster_extent = QLabel("Size")

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(cluster_idx, 0, 0)
        grid_layout.addWidget(peak_val, 0, 1)
        grid_layout.addWidget(peak_coord_x, 0, 2)
        grid_layout.addWidget(peak_coord_y, 0, 3)
        grid_layout.addWidget(peak_coord_z, 0, 4)
        grid_layout.addWidget(cluster_extent, 0, 5)

        # add cluster information
        row_idx = 1
        for line in self._cluster_info:
            idx = QLabel(str(line[0]))
            peak_val = QLabel(str(line[1]))
            coord_x = QLabel(str(line[2]))
            coord_y = QLabel(str(line[3]))
            coord_z = QLabel(str(line[4]))
            extent = QLabel(str(line[5]))
            grid_layout.addWidget(cluster_idx, row_idx, 0)
            grid_layout.addWidget(peak_val, row_idx, 1)
            grid_layout.addWidget(peak_coord_x, row_idx, 2)
            grid_layout.addWidget(peak_coord_y, row_idx, 3)
            grid_layout.addWidget(peak_coord_z, row_idx, 4)
            grid_layout.addWidget(cluster_extent, row_idx, 5)

        # button config
        #self.save_button = QPushButton("Run")
        self.cancel_button = QPushButton("Close")

        hbox_layout = QHBoxLayout()
        #hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        #self.run_button.clicked.connect(self._cluster)
        self.cancel_button.clicked.connect(self.done)

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

