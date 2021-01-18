# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import copy
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from matplotlib import pyplot as plt
from matplotlib.widgets import Slider, MultiCursor
from froi.algorithm import regiongrow as rg
from froi.algorithm.regiongrow import RegionGrow
from froi.algorithm.tools import slide_win_smooth, VlineMover


class GrowDialog(QDialog):
    """A dialog for action of intersection."""
    def __init__(self, model, main_win, parent=None):
        super(GrowDialog, self).__init__(parent)
        self._model = model
        self._main_win = main_win
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("Region Growing")

        # initialize widgets
        xyz = self._model.get_cross_pos()
        #source_label = QLabel("Source")
        self.source_combo = QComboBox()
        pointx_label = QLabel("Seed point x")
        self.pointx_edit = QLineEdit()
        self.pointx_edit.setText(str(xyz[0]))
        pointy_label = QLabel("Seed point y")
        self.pointy_edit = QLineEdit()
        self.pointy_edit.setText(str(xyz[1]))
        pointz_label = QLabel("Seed point z")
        self.pointz_edit = QLineEdit()
        self.pointz_edit.setText(str(xyz[2]))


        number_label = QLabel("Number of voxels")
        self.number_edit = QLineEdit()
        self.number_edit.setText('100')

        vol_list = self._model.getItemList()
        self.source_combo.addItems(vol_list)
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)
        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(pointx_label, 0, 0)
        grid_layout.addWidget(self.pointx_edit, 0, 1)
        grid_layout.addWidget(pointy_label, 1, 0)
        grid_layout.addWidget(self.pointy_edit, 1, 1)
        grid_layout.addWidget(pointz_label, 2, 0)
        grid_layout.addWidget(self.pointz_edit, 2, 1)

        grid_layout.addWidget(number_label, 3, 0)
        grid_layout.addWidget(self.number_edit, 3, 1)

        grid_layout.addWidget(out_label, 4, 0)
        grid_layout.addWidget(self.out_edit, 4, 1)

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
        self.run_button.clicked.connect(self._grow)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        source_name = self.source_combo.currentText()
        output_name = '_'.join([str(source_name), 'grow'])
        self.out_edit.setText(output_name)

    def _grow(self):
        vol_name = str(self.out_edit.text())
        pointx = self.pointx_edit.text()
        pointy = self.pointy_edit.text()
        pointz = self.pointz_edit.text()
        number = self.number_edit.text()

        if int(number) <= 0:
            QMessageBox.about(self, self.tr("number error"),self.tr("voxel number is out of range"))
            return
        if int(pointx) < 0 or int(pointx) > self._model.getY() - 1:
            QMessageBox.about(self, self.tr("coordinate error"),self.tr("coordinate x is out of range"))
            return
        if int(pointy) < 0 or int(pointy) > self._model.getX() - 1:
            QMessageBox.about(self, self.tr("coordinate error"),self.tr("coordinate y is out of range"))
            return
        if int(pointz) < 0 or int(pointz) > self._model.getZ() - 1:
            QMessageBox.about(self, self.tr("coordinate error"),self.tr("coordinate z is out of range"))
            return

        if not vol_name:
            self.out_edit.setFocus()
            return
        if not pointx:
            self.pointx_edit.setFocus()
            return
        if not pointy:
            self.pointy_edit.setFocus()
            return
        if not pointz:
            self.pointz_edit.setFocus()
            return
        if not number:
            self.number_edit.setFocus()
            return

        try:
            pointx=int(pointx)
            pointy=int(pointy)
            pointz=int(pointz)
            number=int(number)
        except ValueError :
            self.number_edit.selectAll()
            self.pointx_edit.selectAll()
            self.pointy_edit.selectAll()
            self.pointz_edit.selectAll()
            return

        source_row = self.source_combo.currentIndex()
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 5)
        new_vol =rg.region_growing(source_data, (pointx,pointy,pointz),number)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'red')

        #self._main_win.new_image_action()
        self.done(0)


class VolumeRGDialog(QDialog):

    rg_types = ['srg', 'arg']

    def __init__(self, model, parent=None):
        super(VolumeRGDialog, self).__init__(parent)
        self.model = model

        self.rg_type = 'srg'
        self.seeds_id = []
        self.stop_criteria = [500]
        self._data_selection = ["current map", "current series"]
        self.group_idx = 'new'  # specify current seed group's index
        self.r_idx_sm = None
        self.smoothness = None
        self.vol_shape = None

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        # Initialize widgets
        self.setWindowTitle("volRG")
        rg_type_label = QLabel('RG-type')
        self._rg_type_combo = QComboBox()
        self._rg_type_combo.addItems(self.rg_types)
        self._rg_type_combo.setCurrentIndex(self.rg_types.index(self.rg_type))

        group_idx_label = QLabel('seed group:')
        self._group_idx_combo = QComboBox()
        self._group_idx_combo.addItem(self.group_idx)

        self._stop_label = QLabel("stop_criteria:")
        self._stop_edit = QLineEdit()
        self._stop_edit.setText(str(self.stop_criteria[0]))
        self._stop_label.setVisible(True)
        self._stop_edit.setVisible(True)

        xyz = self.model.get_cross_pos()
        pointx_label = QLabel("Seed x")
        self._pointx_edit = QLineEdit()
        self._pointx_edit.setText(str(xyz[0]))
        pointy_label = QLabel("Seed y")
        self._pointy_edit = QLineEdit()
        self._pointy_edit.setText(str(xyz[1]))
        pointz_label = QLabel("Seed z")
        self._pointz_edit = QLineEdit()
        self._pointz_edit.setText(str(xyz[2]))
        self._set_seeds_id()

        self._data_label = QLabel("data:")
        self._data_combo = QComboBox()
        self._data_combo.addItems(self._data_selection)
        self._data_label.setVisible(True)
        self._data_combo.setVisible(True)

        self._ok_button = QPushButton("OK")
        self._cancel_button = QPushButton("Cancel")

        # layout
        grid_layout = QGridLayout()
        grid_layout.addWidget(rg_type_label, 0, 0)
        grid_layout.addWidget(self._rg_type_combo, 0, 1)
        grid_layout.addWidget(group_idx_label, 1, 0)
        grid_layout.addWidget(self._group_idx_combo, 1, 1)
        grid_layout.addWidget(pointx_label, 2, 0)
        grid_layout.addWidget(self._pointx_edit, 2, 1)
        grid_layout.addWidget(pointy_label, 3, 0)
        grid_layout.addWidget(self._pointy_edit, 3, 1)
        grid_layout.addWidget(pointz_label, 4, 0)
        grid_layout.addWidget(self._pointz_edit, 4, 1)
        grid_layout.addWidget(self._stop_label, 5, 0)
        grid_layout.addWidget(self._stop_edit, 5, 1)
        grid_layout.addWidget(self._data_label, 6, 0)
        grid_layout.addWidget(self._data_combo, 6, 1)
        grid_layout.addWidget(self._ok_button, 7, 0)
        grid_layout.addWidget(self._cancel_button, 7, 1)
        self.setLayout(grid_layout)

    def _create_actions(self):
        # connect
        self._rg_type_combo.currentIndexChanged.connect(self._set_rg_type)
        self._group_idx_combo.currentIndexChanged.connect(self._set_group_idx)
        self.connect(self._pointx_edit, SIGNAL("textEdited(QString)"), self._set_seeds_id)
        self.connect(self._pointy_edit, SIGNAL("textEdited(QString)"), self._set_seeds_id)
        self.connect(self._pointz_edit, SIGNAL("textEdited(QString)"), self._set_seeds_id)
        self.connect(self._stop_edit, SIGNAL("textEdited(QString)"), self._set_stop_criteria)
        self.connect(self._ok_button, SIGNAL("clicked()"), self._start_volRG)
        self.connect(self._cancel_button, SIGNAL("clicked()"), self.close)

    def _set_rg_type(self):
        self.rg_type = str(self._rg_type_combo.currentText())

    def _set_group_idx(self):
        self.group_idx = str(self._group_idx_combo.currentText())
        if self.group_idx == 'new':
            self._pointx_edit.setText('')
            self._pointy_edit.setText('')
            self._pointz_edit.setText('')
        else:
            idx = int(self.group_idx)
            xs, ys, zs = [], [], []
            for seed in self.seeds_id[idx]:
                xs.append(str(seed[0]))
                ys.append(str(seed[1]))
                zs.append(str(seed[2]))
            self._pointx_edit.setText(','.join(xs))
            self._pointy_edit.setText(','.join(ys))
            self._pointz_edit.setText(','.join(zs))

    def _set_seeds_id(self):
        xs = self._pointx_edit.text().split(',')
        while '' in xs:
            xs.remove('')
        ys = self._pointy_edit.text().split(',')
        while '' in ys:
            ys.remove('')
        zs = self._pointz_edit.text().split(',')
        while '' in zs:
            zs.remove('')
        n_x, n_y, n_z = len(xs), len(ys), len(zs)
        if n_x == n_y and n_y == n_z:
            if self.group_idx == 'new':
                if n_x != 0:
                    idx = len(self.seeds_id)
                    seeds = []
                    for i in range(n_x):
                        seeds.append((int(xs[i]), int(ys[i]), int(zs[i])))
                    self.seeds_id.append(seeds)
                    self.group_idx = str(idx)
                    self._group_idx_combo.addItem(self.group_idx)
                    self._group_idx_combo.setCurrentIndex(idx+1)
            else:
                idx = int(self.group_idx)
                if n_x != 0:
                    seeds = []
                    for i in range(n_x):
                        seeds.append((int(xs[i]), int(ys[i]), int(zs[i])))
                    self.seeds_id[idx] = seeds
                else:
                    end_item_idx = len(self.seeds_id)
                    self.seeds_id.pop(idx)
                    self._group_idx_combo.removeItem(end_item_idx)
                    self.group_idx = 'new'
                    self._group_idx_combo.setCurrentIndex(0)
            self._set_stop_criteria()

    def _set_stop_criteria(self):
        text_list = self._stop_edit.text().split(',')
        while '' in text_list:
            text_list.remove('')
        if len(text_list) == len(self.seeds_id):
            self.stop_criteria = np.array(text_list, dtype="int")
        elif len(text_list) == 0:
            self.stop_criteria = []
        else:
            # If the number of stop_criteria is not equal to seeds,
            # then we use its first stop criteria for all seeds.
            self.stop_criteria = np.array([text_list[0]], dtype="int")

    def _start_volRG(self):
        self.rg_qmodel_idx = self.model.currentIndex()
        if self._data_combo.currentText() == self._data_selection[0]:
            data = self.model.data(self.rg_qmodel_idx, Qt.UserRole + 14)
        else:
            data = self.model.data(self.rg_qmodel_idx, Qt.UserRole + 6)
        if data.ndim == 3:
            threshold = self.model.data(self.rg_qmodel_idx, Qt.UserRole)
            mask = data > threshold
            data = data[:, :, :, None]
        else:
            mask = None
        assert data.ndim == 4
        self.vol_shape = data.shape[:3]

        rg = RegionGrow()
        if self.rg_type == 'arg':
            # ------------------select a assessment function-----------------
            assess_type, ok = QInputDialog.getItem(
                    self,
                    'select a assessment function',
                    'assessments:',
                    rg.get_assess_types())

            # ------------------If ok, start arg!-----------------
            if ok and assess_type != '':
                rg.set_assessment(assess_type)
                rg.vol2regions(data, mask)
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
                QMessageBox.warning(
                    self,
                    'Warning',
                    'You have to specify a assessment function for arg!',
                    QMessageBox.Yes
                )
                return None

        elif self.rg_type == 'srg':
            rg.vol2regions(data, mask)
            rg_result = rg.srg_parcel(self.seeds_id, self.stop_criteria)

        else:
            raise RuntimeError("The region growing type must be arg, srg and crg at present!")

        self._show_result(rg_result)
        self.close()

    def _show_result(self, rg_result):
        """
        Add RG's result as tree items
        """
        data = np.zeros(self.vol_shape, np.uint8)
        label = 1
        for r in rg_result:
            labeled_vertices = r.get_vertices()
            if np.any([data[_] for _ in labeled_vertices]):
                QMessageBox.warning(self, 'Warning',
                                    "Group{0}'s result has overlap with other groups".format(label-1),
                                    QMessageBox.Yes)
            for v in labeled_vertices:
                data[v] = label
            label += 1

        name = 'rg_' + self.model.data(self.rg_qmodel_idx, Qt.DisplayRole)
        if self.model.data(self.rg_qmodel_idx, Qt.UserRole + 8):
            map_idx = self.model.data(self.rg_qmodel_idx, Qt.UserRole + 9)
            name += '_' + str(map_idx)

        header = copy.deepcopy(self.model._data[0].get_header())
        header.set_data_shape(self.vol_shape)
        self.model.addItem(data, colormap='blue', name=name, header=header)

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
            data = np.zeros(self.vol_shape, np.int)
            for v in labeled_vertices:
                data[v] = 1
            name = 'rg_' + self.model.data(self.rg_qmodel_idx, Qt.DisplayRole)
            if self.model.data(self.rg_qmodel_idx, Qt.UserRole + 8):
                name += str(self.model.data(self.rg_qmodel_idx, Qt.UserRole + 9))
            name += '_{}'.format(r_idx)
            header = copy.deepcopy(self.model._data[0].get_header())
            header.set_data_shape(self.vol_shape)
            self.model.addItem(data, colormap='blue', name=name, header=header)
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
        QDialog.close(self)
