import numpy as np
from PyQt4 import QtGui, QtCore
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, MultiCursor

from ..algorithm.regiongrow import RegionGrow
from ..algorithm.tools import slide_win_smooth, VlineMover
from ..algorithm.meshtool import get_n_ring_neighbor, LabelAssessment


class SurfaceRGDialog(QtGui.QDialog):

    rg_types = ['srg', 'arg', 'crg']

    def __init__(self, model, surf_view, parent=None):
        super(SurfaceRGDialog, self).__init__(parent)
        self.setWindowTitle("surfRG")
        self._surf_view = surf_view
        self.model = model

        self.rg_type = 'arg'
        self.seeds_id = []
        self.stop_criteria = [500]
        self.n_ring = 1
        self.group_idx = 'new'  # specify current seed group's index
        self.cut_line = []  # a list of vertices' id which plot a line
        self.r_idx_sm = None
        self.smoothness = None
        self.vertices_count = None
        self._is_cutting = False

        self._init_gui()
        self._create_actions()

        self._surf_view.seed_flag = True

    def _init_gui(self):
        # Initialize widgets
        rg_type_label = QtGui.QLabel('RG-type')
        self._rg_type_combo = QtGui.QComboBox()
        self._rg_type_combo.addItems(self.rg_types)
        self._rg_type_combo.setCurrentIndex(self.rg_types.index(self.rg_type))

        group_idx_label = QtGui.QLabel('seed group:')
        self._group_idx_combo = QtGui.QComboBox()
        self._group_idx_combo.addItem(self.group_idx)

        seeds_label = QtGui.QLabel("seeds:")
        self._seeds_edit = QtGui.QLineEdit()
        self._seeds_edit.setText('peak value vertex')

        self._stop_label = QtGui.QLabel("stop_criteria:")
        self._stop_edit = QtGui.QLineEdit()
        self._stop_edit.setText(str(self.stop_criteria[0]))

        ring_label = QtGui.QLabel("n_ring:")
        self._ring_spin = QtGui.QSpinBox()
        self._ring_spin.setMinimum(1)
        self._ring_spin.setValue(self.n_ring)

        self._mask_label = QtGui.QLabel("mask:")
        self._mask_combo = QtGui.QComboBox()
        self._fill_mask_box()

        self._threshold_label = QtGui.QLabel("threshold:")
        self._threshold_edit = QtGui.QLineEdit()
        self._threshold_label.setVisible(False)
        self._threshold_edit.setVisible(False)

        self._cutoff_button1 = QtGui.QPushButton('start cutoff')
        self._cutoff_button2 = QtGui.QPushButton('stop cutoff')
        self._cutoff_button1.setVisible(False)
        self._cutoff_button2.setVisible(False)
        self._cutoff_button2.setEnabled(False)

        self._ok_button = QtGui.QPushButton("OK")
        self._cancel_button = QtGui.QPushButton("Cancel")

        # layout
        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(rg_type_label, 0, 0)
        grid_layout.addWidget(self._rg_type_combo, 0, 1)
        grid_layout.addWidget(group_idx_label, 1, 0)
        grid_layout.addWidget(self._group_idx_combo, 1, 1)
        grid_layout.addWidget(seeds_label, 2, 0)
        grid_layout.addWidget(self._seeds_edit, 2, 1)
        grid_layout.addWidget(self._stop_label, 3, 0)
        grid_layout.addWidget(self._stop_edit, 3, 1)
        grid_layout.addWidget(ring_label, 4, 0)
        grid_layout.addWidget(self._ring_spin, 4, 1)
        grid_layout.addWidget(self._mask_label, 5, 0)
        grid_layout.addWidget(self._mask_combo, 5, 1)
        grid_layout.addWidget(self._threshold_label, 6, 0)
        grid_layout.addWidget(self._threshold_edit, 6, 1)
        grid_layout.addWidget(self._cutoff_button1, 7, 0)
        grid_layout.addWidget(self._cutoff_button2, 7, 1)
        grid_layout.addWidget(self._ok_button, 8, 0)
        grid_layout.addWidget(self._cancel_button, 8, 1)
        self.setLayout(grid_layout)

    def _create_actions(self):
        # connect
        self._rg_type_combo.currentIndexChanged.connect(self._set_rg_type)
        self._group_idx_combo.currentIndexChanged.connect(self._set_group_idx)
        self.connect(self._seeds_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_seeds_id)
        self.connect(self._stop_edit, QtCore.SIGNAL("textEdited(QString)"), self._set_stop_criteria)
        self.connect(self._ring_spin, QtCore.SIGNAL("valueChanged"), self._set_n_ring)
        self.connect(self._cutoff_button1, QtCore.SIGNAL("clicked()"), self._start_cutoff)
        self.connect(self._cutoff_button2, QtCore.SIGNAL("clicked()"), self._stop_cutoff)
        self.connect(self._ok_button, QtCore.SIGNAL("clicked()"), self._start_surfRG)
        self.connect(self._cancel_button, QtCore.SIGNAL("clicked()"), self.close)
        self._surf_view.seed_picked.connect(self._set_seeds_edit_text)
        self.model.rowsMoved.connect(self._fill_mask_box)
        self.model.rowsMoved.connect(self._init_thr_editor)
        self.model.rowsInserted.connect(self._fill_mask_box)
        self.model.rowsInserted.connect(self._init_thr_editor)
        self.model.rowsRemoved.connect(self._fill_mask_box)
        self.model.rowsRemoved.connect(self._init_thr_editor)
        self.model.dataChanged.connect(self._fill_mask_box)
        self.model.dataChanged.connect(self._init_thr_editor)
        self.connect(self.model, QtCore.SIGNAL("currentIndexChanged"), self._fill_mask_box)
        self.connect(self.model, QtCore.SIGNAL("currentIndexChanged"), self._init_thr_editor)

    def _start_cutoff(self):
        self._cutoff_button1.setEnabled(False)
        self._cutoff_button2.setEnabled(True)
        self._surf_view.seed_flag = False
        self._surf_view.scribing_flag = True
        self.cut_line = []
        self._is_cutting = True

    def _stop_cutoff(self):
        self._surf_view.seed_flag = True
        self._surf_view.scribing_flag = False
        self._cutoff_button1.setEnabled(True)
        self._cutoff_button2.setEnabled(False)
        self.cut_line = list(self._surf_view.path)
        self._surf_view.plot_start = None
        self._surf_view.path = []
        self._is_cutting = False

    def _set_group_idx(self):

        self.group_idx = str(self._group_idx_combo.currentText())
        if self.group_idx == 'new':
            self._seeds_edit.setText('')
        else:
            idx = int(self.group_idx)
            text = ','.join(map(str, self.seeds_id[idx]))
            self._seeds_edit.setText(text)

    def _set_rg_type(self):
        self.rg_type = str(self._rg_type_combo.currentText())
        if self.rg_type == 'crg':
            self._stop_label.setVisible(False)
            self._stop_edit.setVisible(False)
            self._mask_label.setVisible(False)
            self._mask_combo.setVisible(False)
            self._threshold_label.setVisible(True)
            self._threshold_edit.setVisible(True)
            self._cutoff_button1.setVisible(True)
            self._cutoff_button2.setVisible(True)
            self._init_thr_editor()
        else:
            self._stop_label.setVisible(True)
            self._stop_edit.setVisible(True)
            self._mask_label.setVisible(True)
            self._mask_combo.setVisible(True)
            self._threshold_label.setVisible(False)
            self._threshold_edit.setVisible(False)
            self._cutoff_button1.setVisible(False)
            self._cutoff_button2.setVisible(False)
            if self._is_cutting:
                self._stop_cutoff()
                self.cut_line = []

    def _set_seeds_edit_text(self):

        if self.group_idx == 'new':
            idx = len(self.seeds_id)
            self.seeds_id.append([self._surf_view.point_id])
            self.group_idx = str(idx)
            self._group_idx_combo.addItem(self.group_idx)
            self._group_idx_combo.setCurrentIndex(idx+1)
        else:
            idx = int(self.group_idx)
            self.seeds_id[idx].append(self._surf_view.point_id)
        text = ','.join(map(str, self.seeds_id[idx]))
        self._seeds_edit.setText(text)

    def _set_stop_criteria(self):

        text_list = self._stop_edit.text().split(',')
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

        text_list = self._seeds_edit.text().split(',')
        while '' in text_list:
            text_list.remove('')
        if self.group_idx == 'new':
            if text_list:
                idx = len(self.seeds_id)
                self.seeds_id.append(map(int, text_list))
                self.group_idx = str(idx)
                self._group_idx_combo.addItem(self.group_idx)
                self._group_idx_combo.setCurrentIndex(idx+1)
        else:
            idx = int(self.group_idx)
            if text_list:
                self.seeds_id[idx] = map(int, text_list)
            else:
                end_item_idx = len(self.seeds_id)
                self.seeds_id.pop(idx)
                self._group_idx_combo.removeItem(end_item_idx)
                self.group_idx = 'new'
                self._group_idx_combo.setCurrentIndex(0)
        self._set_stop_criteria()

    def _set_n_ring(self):
        self.n_ring = int(self._ring_spin.value())

    def _fill_mask_box(self):
        self._mask_combo.clear()
        overlay_name_list = self.model.get_overlay_list()
        self._mask_combo.addItem("None")
        self._mask_combo.addItems(overlay_name_list)

        index = self.model.current_index()
        depth = self.model.index_depth(index)
        if depth == 2:
            name = self.model.data(index, QtCore.Qt.DisplayRole)
            row = overlay_name_list.index(name) + 1
        else:
            row = 0

        self._mask_combo.setCurrentIndex(row)

    def _get_current_mask(self):
        row = self._mask_combo.currentIndex()
        if row == 0:
            return None
        else:
            row -= 1
            surface_idx = self.model.get_surface_index()
            mask_idx = self.model.index(row, 0, surface_idx)
            mask = self.model.data(mask_idx, QtCore.Qt.UserRole + 5)
            mask = np.mean(mask, 1)  # FIXME not suitable for multi-feature data
            mask = mask.reshape((mask.shape[0],))
            if self.model.data(mask_idx, QtCore.Qt.UserRole + 7):
                mask = mask != 0
            else:
                thresh = self.model.data(mask_idx, QtCore.Qt.UserRole)
                mask = mask > thresh
            return mask

    def _init_thr_editor(self):

        index = self.model.current_index()
        depth = self.model.index_depth(index)
        if depth == 2:
            thr = self.model.data(index, QtCore.Qt.UserRole)
            self._threshold_edit.setText(str(thr))
            self._threshold_edit.setEnabled(True)
        else:
            self._threshold_edit.setText("None")
            self._threshold_edit.setEnabled(False)

    def _start_surfRG(self):

        index = self.model.current_index()
        depth = self.model.index_depth(index)
        if depth == 1:
            geometry = self.model.data(index, QtCore.Qt.UserRole + 6)
        elif depth == 2:
            geometry = self.model.data(index.parent(), QtCore.Qt.UserRole + 6)
        else:
            QtGui.QMessageBox.warning(
                self, 'Error',
                'Get surface failed!\nYou may have not selected any surface!',
                QtGui.QMessageBox.Yes
            )
            return None
        self.vertices_count = geometry.vertices_count()

        rg = RegionGrow()
        if self.rg_type == 'arg':
            if depth != 2:
                QtGui.QMessageBox.warning(
                    self,
                    'Warning',
                    'Get overlay failed!\nYou may have not selected any overlay!',
                    QtGui.QMessageBox.Yes
                )
                return None
            scalar_data = self.model.data(index, QtCore.Qt.UserRole + 5)
            mask = self._get_current_mask()

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
                rg.surf2regions(geometry, scalar_data, mask, self.n_ring)
                rg_result, self.evolved_regions, self.region_assessments, self.assess_step, r_outer_mean, r_inner_min\
                    = rg.arg_parcel(self.seeds_id, self.stop_criteria, whole_results=True)

                # -----------------plot diagrams------------------
                num_axes = len(self.evolved_regions)
                fig, self.axes = plt.subplots(num_axes, 2)
                if num_axes == 1:
                    self.axes = np.array([self.axes])
                self.vline_movers = np.zeros_like(self.axes[:, 0])  # store vline movers
                self.cursors = np.zeros_like(self.axes)  # store cursors, hold references
                self.slider_axes = np.zeros_like(self.axes[:, 0])
                self.sm_sliders = []  # store smooth sliders, hold references
                for r_idx, r in enumerate(self.evolved_regions):
                    # plot region outer boundary assessment curve
                    self.axes[r_idx][1].plot(r_outer_mean[r_idx], 'b.-', label='r_outer_mean')
                    self.axes[r_idx][1].plot(r_inner_min[r_idx], 'r.-', label='r_inner_min')
                    self.axes[r_idx][1].legend()
                    self.axes[r_idx][1].set_ylabel('amplitude')
                    self.axes[r_idx][1].set_title('related values for seed {}'.format(r_idx))

                    # plot assessment curve
                    self.r_idx_sm = r_idx
                    self.smoothness = 0
                    self._sm_update_axes()

                    # add slider
                    ax_pos = self.axes[r_idx][0].get_position()
                    slider_ax = fig.add_axes([ax_pos.x1-0.15, ax_pos.y0+0.005, 0.15, 0.015])
                    sm_slider = Slider(slider_ax, 'smoothness', 0, 10, 0, '%d', dragging=False)
                    sm_slider.on_changed(self._on_smooth_changed)
                    self.slider_axes[r_idx] = slider_ax
                    self.sm_sliders.append(sm_slider)

                self.axes[-1][0].set_xlabel('contrast step/component')
                self.axes[-1][1].set_xlabel('contrast step/component')
                self.cursor = MultiCursor(fig.canvas, self.axes.ravel(),
                                          ls='dashed', lw=0.5, c='g', horizOn=True)
                fig.canvas.set_window_title('assessment curves')
                fig.canvas.mpl_connect('button_press_event', self._on_clicked)
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
            if depth != 2:
                QtGui.QMessageBox.warning(
                    self,
                    'Warning',
                    'Get overlay failed!\nYou may have not selected any overlay!',
                    QtGui.QMessageBox.Yes
                )
                return None
            scalar_data = self.model.data(index, QtCore.Qt.UserRole + 5)
            mask = self._get_current_mask()

            rg.surf2regions(geometry, scalar_data, mask, self.n_ring)
            rg_result = rg.srg_parcel(self.seeds_id, self.stop_criteria)

        elif self.rg_type == 'crg':

            if depth == 1:
                edge_list = get_n_ring_neighbor(geometry.faces, n=self.n_ring)
                for cut_vtx in self.cut_line:
                    edge_list[cut_vtx] = set()
                rg_result = rg.connectivity_grow(self.seeds_id, edge_list)

            elif depth == 2:
                scalar_data = self.model.data(index, QtCore.Qt.UserRole + 5)
                scalar_data = np.mean(scalar_data, 1)  # FIXME not suitable for multi-feature data
                mask_data = scalar_data.reshape((scalar_data.shape[0],))
                neighbors = get_n_ring_neighbor(geometry.faces)

                self.thresholds = self._threshold_edit.text().split(',')
                while '' in self.thresholds:
                    self.thresholds.remove('')

                self.crg_results = list()
                for thr in self.thresholds:
                    if thr == "None":
                        edge_list = get_n_ring_neighbor(geometry.faces, n=self.n_ring)
                    else:
                        mask = mask_data > float(thr)
                        edge_list = get_n_ring_neighbor(geometry.faces, n=self.n_ring, mask=mask)

                    for cut_vtx in self.cut_line:
                        edge_list[cut_vtx] = set()

                    self.crg_results.append(rg.connectivity_grow(self.seeds_id, edge_list))

                if len(self.thresholds) > 1:
                    n_region = len(self.seeds_id)
                    # get assessments, and rg_result
                    self.crg_results = np.array(self.crg_results)
                    label_assess = LabelAssessment()
                    self.region_assessments = list()
                    rg_result = list()
                    for r_idx in range(n_region):
                        multi_thr_regions = map(list, self.crg_results[:, r_idx])
                        assessment = list()
                        for region in multi_thr_regions:
                            assessment.append(label_assess.transition_level(region, scalar_data, None, neighbors))
                        best_thr_idx = np.argmax(assessment)
                        rg_result.append(self.crg_results[best_thr_idx, r_idx])
                        self.region_assessments.append(assessment)

                    # plot
                    fig, self.axes = plt.subplots(n_region)
                    _ = np.zeros(self.axes.shape)
                    self.axes = np.c_[self.axes, _]
                    self.vline_movers = np.zeros_like(self.axes[:, 0])  # store vline movers
                    self.cursors = np.zeros_like(self.axes)  # store cursors, hold references
                    self.slider_axes = np.zeros_like(self.axes[:, 0])
                    self.sm_sliders = []  # store smooth sliders, hold references
                    for r_idx in range(n_region):
                        # plot assessment curve
                        self.r_idx_sm = r_idx
                        self.smoothness = 0
                        self._sm_update_axes()

                        # add slider
                        ax_pos = self.axes[r_idx][0].get_position()
                        slider_ax = fig.add_axes([ax_pos.x1 - 0.15, ax_pos.y0 + 0.005, 0.15, 0.015])
                        sm_slider = Slider(slider_ax, 'smoothness', 0, 10, 0, '%d', dragging=False)
                        sm_slider.on_changed(self._on_smooth_changed)
                        self.slider_axes[r_idx] = slider_ax
                        self.sm_sliders.append(sm_slider)

                    self.axes[-1][0].set_xlabel('thresholds')
                    self.cursor = MultiCursor(fig.canvas, self.axes[:, 0],
                                              ls='dashed', lw=0.5, c='g', horizOn=True)
                    fig.canvas.set_window_title('assessment curves')
                    fig.canvas.mpl_connect('button_press_event', self._on_clicked)
                    plt.show()
                else:
                    rg_result = self.crg_results[0]
            else:
                return

        else:
            raise RuntimeError("The region growing type must be arg, srg and crg at present!")

        self._show_result(rg_result)
        self.close()

    def _show_result(self, rg_result):
        """
        Add RG's result as tree items
        """
        for r in rg_result:
            if self.rg_type == 'srg' or self.rg_type == 'arg':
                labeled_vertices = r.get_vertices()
            elif self.rg_type == 'crg':
                labeled_vertices = list(r)
            else:
                raise RuntimeError("The region growing type must be arg, srg and crg at present!")
            data = np.zeros((self.vertices_count,), np.int)
            data[labeled_vertices] = 1
            self.model.add_item(self.model.current_index(), data,
                                islabel=True, colormap='blue')

    def _on_clicked(self, event):
        if event.button == 3 and event.inaxes in self.axes[:, 0]:
            # do something on right click
            r_idx = np.where(self.axes[:, 0] == event.inaxes)[0][0]
            index = int(self.vline_movers[r_idx].x[0])

            if self.rg_type == "arg":
                # find current evolved region
                r = self.evolved_regions[r_idx]

                # get vertices included in the evolved region
                end_index = int((index+1) * self.assess_step)
                labeled_vertices = set()
                for region in r.get_component()[:end_index]:
                    labeled_vertices.update(region.get_vertices())
                labeled_vertices = list(labeled_vertices)
            elif self.rg_type == "crg":
                labeled_vertices = list(self.crg_results[index][r_idx])
            else:
                return

            # visualize these labeled vertices
            data = np.zeros((self.vertices_count,), np.int)
            data[labeled_vertices] = 1
            self.model.add_item(self.model.current_index(), data,
                                islabel=True, colormap='blue')
        elif event.button == 1 and event.inaxes in self.slider_axes:
            # do something on left click
            # find current evolved region
            self.r_idx_sm = np.where(self.slider_axes == event.inaxes)[0][0]
            if self.smoothness is not None:
                # indicate that self._on_click is performed later than self._on_smooth_changed
                # to ensure that self.r_idx_sm is got before smoothing
                self._sm_update_axes()

    def _on_smooth_changed(self, val):
        self.smoothness = int(val)
        if self.r_idx_sm is not None:
            # indicate that self._on_click is performed earlier than self._on_smooth_changed
            # to ensure that self.r_idx_sm is got before smoothing
            self._sm_update_axes()

    def _sm_update_axes(self):
        self.axes[self.r_idx_sm][0].cla()
        smoothed_curve = slide_win_smooth(self.region_assessments[self.r_idx_sm], self.smoothness)
        if self.rg_type == "crg":
            self.axes[self.r_idx_sm][0].plot(self.thresholds, smoothed_curve, "b.-")
        elif self.rg_type == "arg":
            self.axes[self.r_idx_sm][0].plot(smoothed_curve, "b.-")
        else:
            return
        self.axes[self.r_idx_sm][0].set_title('curve for seed {}'.format(self.r_idx_sm))
        self.axes[self.r_idx_sm][0].set_ylabel('assessed value')

        # initialize vline
        max_index = np.argmax(smoothed_curve)
        vline = self.axes[self.r_idx_sm][0].axvline(max_index)
        # instance VlineMover
        self.vline_movers[self.r_idx_sm] = VlineMover(vline, True)

        # reset
        self.r_idx_sm = None
        self.smoothness = None

    def close(self):

        self._surf_view.seed_picked.disconnect(self._set_seeds_edit_text)
        self.model.rowsMoved.disconnect(self._fill_mask_box)
        self.model.rowsMoved.disconnect(self._init_thr_editor)
        self.model.rowsInserted.disconnect(self._fill_mask_box)
        self.model.rowsInserted.disconnect(self._init_thr_editor)
        self.model.rowsRemoved.disconnect(self._fill_mask_box)
        self.model.rowsRemoved.disconnect(self._init_thr_editor)
        self.model.dataChanged.disconnect(self._fill_mask_box)
        self.model.dataChanged.disconnect(self._init_thr_editor)
        self.disconnect(self.model, QtCore.SIGNAL("currentIndexChanged"), self._fill_mask_box)
        self.disconnect(self.model, QtCore.SIGNAL("currentIndexChanged"), self._init_thr_editor)

        if self._is_cutting:
            self._stop_cutoff()
            self.cut_line = []

        self._surf_view.seed_flag = False
        QtGui.QDialog.close(self)
