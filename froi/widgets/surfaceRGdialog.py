import numpy as np
from PyQt4 import QtGui, QtCore
import matplotlib.pyplot as plt

from ..io.surf_io import read_data
from ..algorithm.regiongrow import RegionGrow
from ..algorithm.tools import get_curr_hemi, get_curr_overlay


class SurfaceRGDialog(QtGui.QDialog):

    rg_types = ['srg', 'arg']

    def __init__(self, model, tree_view_control, surf_view, parent=None):
        super(SurfaceRGDialog, self).__init__(parent)
        self.setWindowTitle("surfRG")
        self._surf_view = surf_view
        self.tree_view_control = tree_view_control
        self.model = model

        self._surf_view.surfRG_flag = True

        self.rg_type = 'arg'
        self.mask = None
        self.seeds_id = []
        self.stop_criteria = 500
        self.n_ring = 1
        self.group_idx = 'new'  # specify current seed group's index

        # Initialize widgets
        group_idx_label = QtGui.QLabel('seed group:')
        group_idx_combo = QtGui.QComboBox()
        group_idx_combo.addItem(self.group_idx)

        seeds_label = QtGui.QLabel("seeds:")
        seeds_edit = QtGui.QLineEdit()
        # seeds_edit.setReadOnly(True)
        seeds_edit.setText('peak value vertex')

        stop_label = QtGui.QLabel("stop_criteria:")
        stop_edit = QtGui.QLineEdit()
        stop_edit.setText(str(self.stop_criteria))

        ring_label = QtGui.QLabel("n_ring:")
        ring_spin = QtGui.QSpinBox()
        ring_spin.setMinimum(1)
        ring_spin.setValue(self.n_ring)

        rg_type_label = QtGui.QLabel('RG-type')
        rg_type_combo = QtGui.QComboBox()
        rg_type_combo.addItems(self.rg_types)
        rg_type_combo.setCurrentIndex(self.rg_types.index(self.rg_type))

        scalar_button = QtGui.QPushButton("add scalar")
        mask_button = QtGui.QPushButton('add mask')

        ok_button = QtGui.QPushButton("OK")
        cancel_button = QtGui.QPushButton("Cancel")

        # layout
        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(group_idx_label, 0, 0)
        grid_layout.addWidget(group_idx_combo, 0, 1)
        grid_layout.addWidget(seeds_label, 1, 0)
        grid_layout.addWidget(seeds_edit, 1, 1)
        grid_layout.addWidget(stop_label, 2, 0)
        grid_layout.addWidget(stop_edit, 2, 1)
        grid_layout.addWidget(ring_label, 3, 0)
        grid_layout.addWidget(ring_spin, 3, 1)
        grid_layout.addWidget(rg_type_label, 4, 0)
        grid_layout.addWidget(rg_type_combo, 4, 1)
        grid_layout.addWidget(scalar_button, 5, 0)
        grid_layout.addWidget(mask_button, 5, 1)
        grid_layout.addWidget(ok_button, 6, 0)
        grid_layout.addWidget(cancel_button, 6, 1)
        self.setLayout(grid_layout)

        # connect
        self.connect(ok_button, QtCore.SIGNAL("clicked()"), self._start_surfRG)
        # self.connect(cancel_button, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("close()"))
        self.connect(cancel_button, QtCore.SIGNAL("clicked()"), self.close)
        self.connect(seeds_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_seeds_id)
        self.connect(stop_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_stop_criteria)
        ring_spin.valueChanged.connect(self._set_n_ring)
        rg_type_combo.currentIndexChanged.connect(self._set_rg_type)
        group_idx_combo.currentIndexChanged.connect(self._set_group_idx)
        self.connect(scalar_button, QtCore.SIGNAL("clicked()"), self._scalar_dialog)
        self.connect(mask_button, QtCore.SIGNAL("clicked()"), self._mask_dialog)
        self._surf_view.seed_picked.connect(self._set_seeds_edit_text)

        # ---------------fields--------------------
        self.stop_edit = stop_edit
        self.ring_spin = ring_spin
        self.seeds_edit = seeds_edit
        self.rg_type_combo = rg_type_combo
        self.group_idx_combo = group_idx_combo

        self.hemi = self._get_curr_hemi()
        # FIXME 'white' should be replaced with surf_type in the future
        self.surf = self.hemi.surf['white']
        self.hemi_vtx_number = self.surf.get_vertices_num()
        # NxM array, N is the number of vertices,
        # M is the number of measurements or time points.
        self.X = None

    def _mask_dialog(self):

        fpath = QtGui.QFileDialog().getOpenFileName(self, 'Open mask file', './',
                                                    'mask files(*.nii *.nii.gz *.mgz *.mgh *.label)')
        if not fpath:
            return
        self.mask = read_data(fpath, self.hemi_vtx_number)

    def _scalar_dialog(self):

        fpaths = QtGui.QFileDialog().getOpenFileNames(self, "Open scalar file", "./")

        if not fpaths:
            return
        self.X = np.zeros((self.hemi_vtx_number,))
        for fpath in fpaths:
            data = read_data(fpath, self.hemi_vtx_number)
            self.X = np.c_[self.X, data]
        self.X = np.delete(self.X, 0, 1)

    def _set_group_idx(self):

        self.group_idx = str(self.group_idx_combo.currentText())
        if self.group_idx == 'new':
            self.seeds_edit.setText('')
        else:
            idx = int(self.group_idx)
            text = ','.join(map(str, self.seeds_id[idx]))
            self.seeds_edit.setText(text)

    def _set_rg_type(self):
        self.rg_type = str(self.rg_type_combo.currentText())

    def _set_seeds_edit_text(self):

        if self.group_idx == 'new':
            idx = len(self.seeds_id)
            self.seeds_id.append([self._surf_view.point_id])
            self.group_idx = str(idx)
            self.group_idx_combo.addItem(self.group_idx)
            self.group_idx_combo.setCurrentIndex(idx+1)
        else:
            idx = int(self.group_idx)
            self.seeds_id[idx].append(self._surf_view.point_id)
        text = ','.join(map(str, self.seeds_id[idx]))
        self.seeds_edit.setText(text)

    def _set_stop_criteria(self):

        text_list = self.stop_edit.text().split(',')
        while '' in text_list:
            text_list.remove('')
        if len(text_list) == len(self.seeds_id):
            self.stop_criteria = np.array(text_list, dtype="int")
        elif len(text_list) == 0:
            pass
        else:
            # If the number of stop_criteria is not equal to seeds,
            # then we use its first stop criteria for all seeds.
            self.stop_criteria = np.array(text_list[0], dtype="int")

    def _set_seeds_id(self):

        text_list = self.seeds_edit.text().split(',')
        while '' in text_list:
            text_list.remove('')
        if self.group_idx == 'new':
            if text_list:
                idx = len(self.seeds_id)
                self.seeds_id.append(map(int, text_list))
                self.group_idx = str(idx)
                self.group_idx_combo.addItem(self.group_idx)
                self.group_idx_combo.setCurrentIndex(idx+1)
        else:
            idx = int(self.group_idx)
            if text_list:
                self.seeds_id[idx] = map(int, text_list)
            else:
                end_item_idx = len(self.seeds_id)
                self.seeds_id.pop(idx)
                self.group_idx_combo.removeItem(end_item_idx)
                self.group_idx = 'new'
                self.group_idx_combo.setCurrentIndex(0)
        self._set_stop_criteria()

    def _set_n_ring(self):
        self.n_ring = int(self.ring_spin.value())

    def _start_surfRG(self):

        if self.X is None:
            overlay = self._get_curr_overlay()
            if not overlay:
                return None
            else:
                self.X = overlay.get_data()

        rg = RegionGrow(self.seeds_id, self.stop_criteria)
        if self.rg_type == 'arg':
            # ------------------select a assessment function-----------------
            assess_type, ok = QtGui.QInputDialog.getItem(
                    self,
                    'select a assessment function',
                    'assessments:',
                    rg.get_assess_types()
            )

            # ------------------If ok, start arg!-----------------
            if ok and assess_type != '':
                rg.set_assessment(assess_type)
                self._surf_view.surfRG_flag = False
                rg.surf2regions(self.surf, self.X, self.mask, self.n_ring)
                rg_regions, evolved_regions, region_assessments =\
                    rg.arg_parcel(whole_results=True)

                # plot diagrams
                for r_idx, r in enumerate(evolved_regions):
                    plt.figure(r_idx)
                    plt.plot(region_assessments[r_idx], 'b*')
                    plt.xlabel('contrast step/component')
                    plt.ylabel('assessed value')
                plt.show()
            else:
                QtGui.QMessageBox.warning(
                    self,
                    'Warning',
                    'You have to specify a assessment function for arg!',
                    QtGui.QMessageBox.Yes
                )
                return None
        elif self.rg_type == 'srg':
            self._surf_view.surfRG_flag = False
            rg.surf2regions(self.surf, self.X, self.mask, self.n_ring)
            rg_regions = rg.srg_parcel()
        else:
            raise RuntimeError("The region growing type must be arg or srg at present!")

        self.close()

        # add RG's result as tree items
        for r in rg_regions:
            labeled_vertices = r.get_vertices()
            data = np.zeros((self.hemi_vtx_number,), np.int)
            data[labeled_vertices] = 1
            self.model.add_item(self.tree_view_control.currentIndex(), data)

    def _get_curr_hemi(self):

        hemi = get_curr_hemi(self.tree_view_control.currentIndex())
        if not hemi:
            QtGui.QMessageBox.warning(
                    self, 'Error',
                    'Get hemisphere failed!\nYou may have not selected any hemisphere!',
                    QtGui.QMessageBox.Yes
            )
            self.close()  # FIXME may be a bug
        return hemi

    def _get_curr_overlay(self):
        """
        If no scalar data is selected, the program will
        get current overlay's data as region growing's data.
        """

        ol = get_curr_overlay(self.tree_view_control.currentIndex())
        if not ol:
            QtGui.QMessageBox.warning(
                    self,
                    'Warning',
                    'Get overlay failed!\nYou may have not selected any overlay!',
                    QtGui.QMessageBox.Yes
            )
        return ol

    def close(self):

        self._surf_view.surfRG_flag = False
        QtGui.QDialog.close(self)
