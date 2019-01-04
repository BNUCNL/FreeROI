# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ..algorithm import imtool
from clusterstatsdialog import ClusterStatsDialog
from froi.algorithm.meshtool import get_n_ring_neighbor, get_patch_by_crg


class ClusterDialog(QDialog):
    """A dialog for cluster processing."""
    def __init__(self, model, parent=None):
        super(ClusterDialog, self).__init__(parent)
        self._model = model
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("Cluster")

        # initialize widgets
        threshold_label = QLabel("Threshold")
        self.threshold_edit = QLineEdit()
        out_label = QLabel("Output name")
        self.out_edit = QLineEdit()

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

    def _cluster(self):
        raise NotImplementedError


class VolClusterDialog(ClusterDialog):

    def __init__(self, model, parent=None):
        super(VolClusterDialog, self).__init__(model, parent)

        self._index = self._model.currentIndex()
        vmin = self._model.data(self._index, Qt.UserRole)
        self.threshold_edit.setText(str(vmin))
        name = self._model.data(self._index, Qt.DisplayRole)
        out_name = '_'.join(['cluster', name])
        self.out_edit.setText(out_name)

    def _cluster(self):
        out_name = str(self.out_edit.text())
        threshold = self.threshold_edit.text()

        if not out_name:
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

        src_data = self._model.data(self._index, Qt.UserRole + 6)
        new_vol = imtool.cluster_labeling(src_data, threshold)
        self._model.addItem(new_vol,
                            None,
                            out_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'rainbow')
        # self.hide()
        image_affine = self._model.get_affine()
        cluster_info = imtool.cluster_stats(src_data, new_vol, image_affine)
        stats_dialog = ClusterStatsDialog(cluster_info)
        stats_dialog.exec_()
        self.done(0)


class SurfClusterDialog(ClusterDialog):

    def __init__(self, model, parent=None):
        super(SurfClusterDialog, self).__init__(model, parent)

        self._index = self._model.current_index()
        depth = self._model.index_depth(self._index)
        if depth != 2:
            QMessageBox.warning(self,
                                'Warning!',
                                'Get overlay failed!\nYou may have not selected any overlay!',
                                QMessageBox.Yes)
            # raise error to prevent dialog from being created
            raise RuntimeError("You may have not selected any overlay!")

        # fill output editor
        name = self._model.data(self._index, Qt.DisplayRole)
        out_name = '_'.join(['cluster', name])
        self.out_edit.setText(out_name)

        # fill threshold editor
        threshold = self._model.data(self._index, Qt.UserRole)
        self.threshold_edit.setText(str(threshold))

    def _cluster(self):
        out_name = str(self.out_edit.text())
        threshold = self.threshold_edit.text()

        if not out_name:
            self.out_edit.setFocus()
            return None
        if not threshold:
            self.threshold_edit.setFocus()
            return None

        try:
            threshold = float(threshold)
        except ValueError:
            self.threshold_edit.selectAll()
            return None

        src_data = self._model.data(self._index, Qt.UserRole + 10)
        geo = self._model.data(self._index.parent(), Qt.UserRole + 6)
        vertices_thr = np.where(src_data > threshold)[0]
        mask = np.zeros(geo.coords.shape[0])
        mask[vertices_thr] = 1
        neighbors = get_n_ring_neighbor(geo.faces, mask=mask)
        clusters = get_patch_by_crg(set(vertices_thr), neighbors)
        trg_data = np.zeros(geo.coords.shape[0], dtype=np.uint16)
        for idx, cluster in enumerate(clusters):
            trg_data[cluster] = idx + 1
        self._model.add_item(self._index,
                             source=trg_data,
                             name=out_name,
                             islabel=True,
                             colormap='rainbow')
        self.done(0)
