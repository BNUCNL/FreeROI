import numpy as np
from PyQt4 import QtGui, QtCore
from scipy.spatial.distance import cdist

from ..io.surf_io import read_data
from ..algorithm.regiongrow import RegionGrow


class SurfaceRGDialog(QtGui.QDialog):

    rg_types = ['arg', 'srg']

    def __init__(self, index, surf_view, parent=None):
        super(SurfaceRGDialog, self).__init__(parent)
        self.setWindowTitle("surfRG")
        self._surf_view = surf_view
        self.index = index

        self._surf_view.surfRG_flag = True

        # Initialize widgets
        count_label = QtGui.QLabel("seeds counts:")
        count_edit = QtGui.QLineEdit()
        count_edit.setReadOnly(True)

        stop_label = QtGui.QLabel("stop_criteria:")
        stop_edit = QtGui.QLineEdit()

        ring_label = QtGui.QLabel("n_ring:")
        ring_edit = QtGui.QSpinBox()
        ring_edit.setMinimum(1)

        rg_type_label = QtGui.QLabel('RG-type')
        rg_type_edit = QtGui.QComboBox()
        rg_type_edit.addItems(self.rg_types)

        scalar_button = QtGui.QPushButton("add scalar")
        mask_button = QtGui.QPushButton('add mask')

        ok_button = QtGui.QPushButton("OK")
        cancel_button = QtGui.QPushButton("Cancel")

        # layout
        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(count_label, 0, 0)
        grid_layout.addWidget(count_edit, 0, 1)
        grid_layout.addWidget(stop_label, 1, 0)
        grid_layout.addWidget(stop_edit, 1, 1)
        grid_layout.addWidget(ring_label, 2, 0)
        grid_layout.addWidget(ring_edit, 2, 1)
        grid_layout.addWidget(rg_type_label, 3, 0)
        grid_layout.addWidget(rg_type_edit, 3, 1)
        grid_layout.addWidget(scalar_button, 4, 0)
        grid_layout.addWidget(mask_button, 4, 1)
        grid_layout.addWidget(ok_button, 5, 0)
        grid_layout.addWidget(cancel_button, 5, 1)
        self.setLayout(grid_layout)

        # connect
        self.connect(ok_button, QtCore.SIGNAL("clicked()"), self._start_surfRG)
        # self.connect(cancel_button, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("close()"))
        self.connect(cancel_button, QtCore.SIGNAL("clicked()"), self.close)
        self.connect(stop_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_stop_criteria)
        ring_edit.valueChanged.connect(self._set_n_ring)
        rg_type_edit.currentIndexChanged.connect(self._set_rg_type)
        self.connect(scalar_button, QtCore.SIGNAL("clicked()"), self._scalar_dialog)
        self.connect(mask_button, QtCore.SIGNAL("clicked()"), self._mask_dialog)
        self._surf_view.seed_picked.seed_picked.connect(self._set_count_edit_text)

        # ---------------fields--------------------
        self.stop_edit = stop_edit
        self.ring_edit = ring_edit
        self.count_edit = count_edit
        self.rg_type_edit = rg_type_edit

        self.rg_type = 'arg'
        self.mask = None
        self.seed_pos = []
        self.stop_criteria = 1000
        self.n_ring = 1
        self.hemi = self._get_curr_hemi()
        # FIXME 'white' should be replaced with surf_type in the future
        self.surf = self.hemi.surf['white']
        self.hemi_vtx_number = self.surf.get_vertices_num()
        # NxM array, N is the number of vertices,
        # M is the number of measurements or time points.
        self.X = None

    def _mask_dialog(self):

        fpath = QtGui.QFileDialog().getOpenFileName(self, 'Open mask file', './',
                                                    'mask files(*.nii *.nii.gz *.mgz *.mgh)')
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

    def _set_rg_type(self):
        self.rg_type = str(self.rg_type_edit.currentText())

    def _set_count_edit_text(self):

        self.seed_pos = list(self._surf_view.seed_pos)  # make a copy
        self.count_edit.setText(str(len(self.seed_pos)))

    def _set_stop_criteria(self):

        text_unicode = self.stop_edit.text()
        text_list = text_unicode.split(',')
        if len(text_list) == len(self.seed_pos):
            if text_list[-1] != "":
                self.stop_criteria = np.array(text_list, dtype="int")
                print self.stop_criteria
        elif not self.seed_pos:
            self.stop_criteria = np.array(text_list[0], dtype="int")
            print self.stop_criteria

    def _set_n_ring(self):
        self.n_ring = int(self.ring_edit.value())

    def _start_surfRG(self):

        if self.X is None:
            overlay = self._get_curr_overlay()
            if not overlay:
                return None
            else:
                self.X = overlay.get_data()

        self.close()
        self._surf_view.surfRG_flag = False

        coords = self.surf.get_coords()
        seeds_id = []
        # get the seed's vertex id
        for seed in self.seed_pos:
            distance = cdist(coords, seed)
            seed_id = np.argmin(distance)
            # To avoid repeatedly picking a same seed
            if seed_id not in seeds_id:
                seeds_id.append(seed_id)

        rg = RegionGrow(seeds_id, self.stop_criteria)

        if self.rg_type == 'arg':
            evolved_regions = rg.arg_parcel(self.surf, self.X, self.mask, self.n_ring)
        elif self.rg_type == 'srg':
            evolved_regions = rg.srg_parcel(self.surf, self.X, self.mask, self.n_ring)
        else:
            raise RuntimeError("The region growing type must be arg or srg at present!")
        rg.region2text(evolved_regions)

    def _get_curr_hemi(self):

        if not self.index.isValid():
            QtGui.QMessageBox.warning(self, 'Error',
                                      'You have not specified a surface!',
                                      QtGui.QMessageBox.Yes)
            self.close()  # FIXME may be a bug
        else:
            parent = self.index.parent()
            if not parent.isValid():
                # add_item = Hemisphere(source)
                hemi_item = self.index.internalPointer()
            else:
                hemi_item = parent.internalPointer()
            return hemi_item

    def _get_curr_overlay(self):
        """
        If no scalar data is selected, the program will
        get current overlay's data as region growing's data.
        """

        parent = self.index.parent()
        if not parent.isValid():
            QtGui.QMessageBox.warning(self, 'Warning',
                                      'You have not specified any overlay!',
                                      QtGui.QMessageBox.Yes)
            return 0
        else:
            hemi_item = parent.internalPointer()
            row = self.index.row()
            idx = hemi_item.overlay_idx[hemi_item.overlay_count()-1-row]
            overlay = hemi_item.overlay_list[idx]
            return overlay

    def close(self):

        self._surf_view.surfRG_flag = False
        self._surf_view.seed_pos = []  # clear the seed_pos for next using

        QtGui.QDialog.close(self)
