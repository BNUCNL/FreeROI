import numpy as np
from PyQt4 import QtGui, QtCore
from scipy.spatial.distance import cdist

from ..io.surf_io import read_data
from ..algorithm.surfaceRG import SurfaceToRegions, AdaptiveRegionGrowing, SeededRegionGrowing


class SurfaceRGDialog(QtGui.QDialog):

    def __init__(self, surf_view, parent=None):
        super(SurfaceRGDialog, self).__init__(parent)
        self.setWindowTitle("surfRG")
        self._surf_view = surf_view
        hemi_list = surf_view.surface_model.get_data()

        self._surf_view.surfRG_flag = True

        # Initialize widgets
        count_label = QtGui.QLabel("seeds counts:")
        count_edit = QtGui.QLineEdit()

        stop_label = QtGui.QLabel("stop_criteria:")
        stop_edit = QtGui.QLineEdit()

        ring_label = QtGui.QLabel("n_ring:")
        ring_edit = QtGui.QLineEdit()

        rg_type_label = QtGui.QLabel('RG-type')
        rg_type_edit = QtGui.QLineEdit()

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
        self.connect(ring_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_n_ring)
        self.connect(rg_type_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_rg_type)
        self.connect(scalar_button, QtCore.SIGNAL("clicked()"), self._scalar_dialog)
        self.connect(mask_button, QtCore.SIGNAL("clicked()"), self._mask_dialog)
        self._surf_view.seed_picked.seed_picked.connect(self._set_count_edit_text)

        # fields
        # FIXME only support the RG which is based on the first hemisphere at present.
        # FIXME 'white' should be replaced with surf_type in the future
        self.surf = hemi_list[0].surf['white']
        self.hemi_vtx_number = self.surf.get_vertices_num()
        self.seed_pos = []
        self.stop_criteria = 1000
        self.n_ring = 1
        self.stop_edit = stop_edit
        self.ring_edit = ring_edit
        self.count_edit = count_edit
        self.rg_type_edit = rg_type_edit
        self.rg_type = 'arg'
        self.scalars = []
        self.mask = None

    def _mask_dialog(self):

        fpath = QtGui.QFileDialog().getOpenFileName(self, 'Open mask file', './',
                                                    'mask files(*.nii *.nii.gz *.mgz *.mgh)')
        if not fpath:
            return
        self.mask = read_data(fpath, self.hemi_vtx_number)[0]

    def _scalar_dialog(self):

        fpaths = QtGui.QFileDialog().getOpenFileNames(self, "Open scalar file", "./")

        if not fpaths:
            return
        for fpath in fpaths:
            data_list = read_data(fpath, self.hemi_vtx_number)
            for data in data_list:
                self.scalars.append(data)

    def _set_rg_type(self):

        text_unicode = self.rg_type_edit.text()
        self.rg_type = str(text_unicode)

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

        text_unicode = self.ring_edit.text()
        self.n_ring = int(text_unicode)

    def _start_surfRG(self):

        self.close()

        self._surf_view.surfRG_flag = False

        coords = self.surf.get_coords()
        # We should exclude the labels within scalar_dict in future version
        s2r = SurfaceToRegions(self.surf, self.scalars, self.mask, self.n_ring)
        regions, v_id2r_id = s2r.get_regions()

        seed_regions = []
        seed_ids = []

        # get the seed's vertex id
        for seed in self.seed_pos:
            distance = cdist(coords, seed)
            seed_id = np.argmin(distance)
            # To avoid repeatedly picking a same seed
            if seed_id not in seed_ids:
                seed_ids.append(seed_id)

        if v_id2r_id:
            for index in seed_ids:
                seed_r_id = v_id2r_id.get(index)
                if seed_r_id is None:
                    raise RuntimeError("At least one of your seeds is out of the mask!")
                seed_regions.append(regions[seed_r_id])
        else:
            for index in seed_ids:
                seed_regions.append(regions[index])

        if not seed_regions:
            seed_regions = s2r.get_seed_region()  # The method seems can't deal with the 4-D data at present.

        if self.rg_type == 'arg':
            surf_rg = AdaptiveRegionGrowing(seed_regions, self.stop_criteria)
        elif self.rg_type == 'srg':
            surf_rg = SeededRegionGrowing(seed_regions, self.stop_criteria)
        else:
            raise RuntimeError("The region growing type must be arg or srg at present!")

        surf_rg.region2text()

    def close(self):

        self._surf_view.surfRG_flag = False
        self._surf_view.seed_pos = []  # clear the seed_pos for next using

        QtGui.QDialog.close(self)
