# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..interface import csv


class ClusterStatsDialog(QDialog):
    """A dialog for reporting cluster stats."""
    def __init__(self, cluster_info, parent=None):
        super(ClusterStatsDialog, self).__init__(parent)
        self._cluster_info = cluster_info

        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Tool | \
                            Qt.CustomizeWindowHint | \
                            Qt.WindowTitleHint)

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("Cluster Stats")

        # initialize widgets
        scroll_content = QWidget()
        cluster_idx = QLabel("Index")
        cluster_idx.setAlignment(Qt.AlignCenter)
        peak_val = QLabel("Peak")
        peak_val.setAlignment(Qt.AlignCenter)
        peak_coord_x = QLabel("Peak_X")
        peak_coord_x.setAlignment(Qt.AlignCenter)
        peak_coord_y = QLabel("Peak_Y")
        peak_coord_y.setAlignment(Qt.AlignCenter)
        peak_coord_z = QLabel("Peak_Z")
        peak_coord_z.setAlignment(Qt.AlignCenter)
        cluster_extent = QLabel("Size")
        cluster_extent.setAlignment(Qt.AlignCenter)

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
            idx.setAlignment(Qt.AlignCenter)
            peak_val = QLabel(str(line[1]))
            peak_val.setAlignment(Qt.AlignCenter)
            coord_x = QLabel(str(line[2]))
            coord_x.setAlignment(Qt.AlignCenter)
            coord_y = QLabel(str(line[3]))
            coord_y.setAlignment(Qt.AlignCenter)
            coord_z = QLabel(str(line[4]))
            coord_z.setAlignment(Qt.AlignCenter)
            extent = QLabel(str(line[5]))
            extent.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(idx, row_idx, 0)
            grid_layout.addWidget(peak_val, row_idx, 1)
            grid_layout.addWidget(coord_x, row_idx, 2)
            grid_layout.addWidget(coord_y, row_idx, 3)
            grid_layout.addWidget(coord_z, row_idx, 4)
            grid_layout.addWidget(extent, row_idx, 5)
            row_idx += 1

        # add labels into a scroll area
        scroll_content.setLayout(grid_layout)
        scrollarea = QScrollArea()
        scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #scrollarea.setWidgetResizable(False)
        scrollarea.setWidget(scroll_content)
        
        # button config
        self.save_button = QPushButton("Export to csv file")
        self.cancel_button = QPushButton("Close")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.save_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(scrollarea)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.save_button.clicked.connect(self._save)
        self.cancel_button.clicked.connect(self.done)

    def _save(self):
        """Export cluster stats info to a file."""
        path = QFileDialog.getSaveFileName(self, 'Save file as ...',
                                           'output.csv',
                                           'csv files (*.csv *.txt)')
        if path:
            labels = ['index', 'max value', 'X', 'Y', 'Z', 'size']
            csv.nparray2csv(self._cluster_info, labels, path)
            self.done(0)


