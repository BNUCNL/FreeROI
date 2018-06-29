# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings


class ROIDialog(QDialog, DrawSettings):
    """ROI toolset."""
    last_target_name = "New Overlay"
    vx_edit_enabled = pyqtSignal()
    roi_edit_enabled = pyqtSignal()
    roi_batch_enabled = pyqtSignal()

    def __init__(self, model, label_config_center, parent=None):
        super(ROIDialog, self).__init__(parent)

        self._model = model
        self.selected_rois = []
        self._last_target_update_enable = True
        self._label_config_center = label_config_center
        self._vx_label = None

    def _init_gui(self):
        self.setWindowModality(Qt.NonModal)
        self.setWindowTitle("Edit")
        screen_geo = QDesktopWidget().screenGeometry()
        self.setMinimumSize(screen_geo.width() * 2 / 15, screen_geo.height() * 8 / 45)
        self.setWindowFlags(Qt.Tool |
                            Qt.CustomizeWindowHint |
                            Qt.WindowTitleHint)

        self.vx_btn = QPushButton(self._vx_label)
        self.ROI_btn = QPushButton("ROI")
        self.ROI_batch_btn = QPushButton("ROI Batch")
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.vx_btn)
        hlayout.addWidget(self.ROI_btn)
        hlayout.addWidget(self.ROI_batch_btn)
        self.vx_btn.setEnabled(False)

        self.ROI_btn.setFocusPolicy(Qt.NoFocus)
        self.vx_btn.setFocusPolicy(Qt.NoFocus)
        self.ROI_batch_btn.setFocusPolicy(Qt.NoFocus)

        self.vlayout = QVBoxLayout()
        self.vlayout.addLayout(hlayout)
        self.vlayout.addWidget(self._label_config_center)

        roi_label = QLabel("Selected ROIs")
        self.roi_edit = QLineEdit()
        self.roi_edit.setReadOnly(True)
        self.add_button = QRadioButton("Select")
        self.add_button.setChecked(True)
        self.del_button = QRadioButton("Deselect")
        self.roi_button_group = QButtonGroup()
        self.roi_button_group.addButton(self.add_button)
        self.roi_button_group.addButton(self.del_button)
        action_label = QLabel("Action")
        self.action_box = QComboBox()
        self.action_box.addItems(['Labeling', 'Copy', 'Split'])
        target_label = QLabel("Target")
        self.target_box = QComboBox()

        grid_layout = QGridLayout()
        grid_layout.addWidget(target_label, 0, 0)
        grid_layout.addWidget(self.target_box, 0, 1)
        grid_layout.addWidget(roi_label, 1, 0)
        grid_layout.addWidget(self.roi_edit, 1, 1)
        grid_layout.addWidget(self.add_button, 2, 0)
        grid_layout.addWidget(self.del_button, 2, 1)
        grid_layout.addWidget(action_label, 3, 0)
        grid_layout.addWidget(self.action_box, 3, 1)

        hbox_layout = QHBoxLayout()
        self.run_button = QPushButton("Run")
        hbox_layout.addWidget(self.run_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)
        self.ROI_tool_widget = QWidget()
        self.ROI_tool_widget.setVisible(False)
        self.ROI_tool_widget.setLayout(vbox_layout)

        self._label_config_center.size_label.setVisible(True)
        self._label_config_center.size_edit.setVisible(True)
        self.vlayout.addWidget(self.ROI_tool_widget)
        self.setLayout(self.vlayout)

    def _create_actions(self):
        self.vx_btn.clicked.connect(self._vx_clicked)
        self.ROI_btn.clicked.connect(self._ROI_clicked)
        self.ROI_batch_btn.clicked.connect(self._ROI_batch_clicked)
        self.target_box.currentIndexChanged.connect(
            self._update_last_target_name)
        # self.action_box.currentIndexChanged[QString].connect(
        #                         self._update_target_box)
        self.action_box.currentIndexChanged[str].connect(
            self._update_target_box)
        self.run_button.pressed.connect(self._run)

    def _vx_clicked(self):
        self._label_config_center.size_label.setVisible(True)
        self._label_config_center.size_edit.setVisible(True)
        self.ROI_tool_widget.setVisible(False)
        self.vx_edit_enabled.emit()
        self.vx_btn.setEnabled(False)
        self.ROI_btn.setEnabled(True)
        self.ROI_batch_btn.setEnabled(True)

    def _ROI_clicked(self):
        self._label_config_center.size_label.setVisible(False)
        self._label_config_center.size_edit.setVisible(False)
        self.ROI_tool_widget.setVisible(False)
        self.roi_edit_enabled.emit()
        self.vx_btn.setEnabled(True)
        self.ROI_btn.setEnabled(False)
        self.ROI_batch_btn.setEnabled(True)

    def _ROI_batch_clicked(self):
        self.selected_rois = []
        self.roi_edit.setText("")
        self._label_config_center.size_label.setVisible(False)
        self._label_config_center.size_edit.setVisible(False)
        self.ROI_tool_widget.setVisible(True)
        self.roi_batch_enabled.emit()
        self.vx_btn.setEnabled(True)
        self.ROI_btn.setEnabled(True)
        self.ROI_batch_btn.setEnabled(False)

    def _fill_target_box(self):
        raise NotImplementedError

    def _update_last_target_name(self):
        if self._last_target_update_enable:
            ROIDialog.last_target_name = str(self.target_box.currentText())

    def _done(self):
        self.done(0)

    def _update_roi(self, id):
        if self.roi_button_group.checkedButton() == self.add_button:
            self._add_roi(id)
        else:
            self._del_roi(id)
        roi_txt = ','.join(map(str, self.selected_rois))
        self.roi_edit.setText(roi_txt)

    def _add_roi(self, id):
        if id not in self.selected_rois:
            self.selected_rois.append(id)

    def _del_roi(self, id):
        if id in self.selected_rois:
            idx = self.selected_rois.index(id)
            del self.selected_rois[idx]

    def _update_target_box(self, s):
        if str(s) == 'Split':
            self.target_box.setDisabled(True)
        else:
            self.target_box.setEnabled(True)

    def is_roi_selection(self):
        return True

    def _run(self):
        if self._label_config_center.get_first_label_config() is None:
            QMessageBox.warning(self, "Invalid label", "Please add some labels first!")
            return None

    def clear_rois(self):
        self.selected_rois = []
        self.roi_edit.clear()

    def show_dialog(self):
        self._model.rowsInserted.connect(self._fill_target_box)
        self._model.rowsMoved.connect(self._fill_target_box)
        self._model.rowsRemoved.connect(self._fill_target_box)
        self._model.dataChanged.connect(self._fill_target_box)
        self._vx_clicked()
        self._fill_target_box()
        self.show()

    def hide_dialog(self):
        self._model.rowsInserted.disconnect(self._fill_target_box)
        self._model.rowsMoved.disconnect(self._fill_target_box)
        self._model.rowsRemoved.disconnect(self._fill_target_box)
        self._model.dataChanged.disconnect(self._fill_target_box)
        self.hide()

    def hideEvent(self, e):
        """Reimplement hide event."""
        self._pos = self.pos()
        e.accept()

    def showEvent(self, e):
        """Reimplement show event."""
        if hasattr(self, '_pos'):
            self.move(self._pos)
        e.accept()


class VolROIDialog(ROIDialog):
    """Volume ROI toolset."""

    def __init__(self, model, label_config_center, parent=None):
        super(VolROIDialog, self).__init__(model, label_config_center, parent)
        self._vx_label = "Voxel"

        self._init_gui()
        self._create_actions()

    def _fill_target_box(self):
        self._last_target_update_enable = False
        self.target_box.clear()
        vol_list = self._model.getItemList()
        self.target_box.addItem("New Overlay")
        # self.target_box.addItems(QStringList(vol_list))
        self.target_box.addItems(vol_list)
        last_target_idx = 0
        for idx, name in enumerate(vol_list):
            if name == ROIDialog.last_target_name:
                last_target_idx = idx + 1
                break
        self.target_box.setCurrentIndex(last_target_idx)
        self._last_target_update_enable = True

    def _run(self):
        super(VolROIDialog, self)._run()

        if self.target_box.isEnabled() and \
                str(self.target_box.currentText()) == "New Overlay":
            self._model.new_image(None, None, 'rainbow')

        run_text = str(self.action_box.currentText())
        if run_text == 'Labeling':
            target_row = self.target_box.currentIndex()
            if target_row != 0:
                target_row -= 1
            if not self._model.get_label_config_center().is_drawing_valid():
                QMessageBox.critical(self, "Invalid ROI Drawing Value",
                                     "Please specify an valid drawing value")
            else:
                for roi in self.selected_rois:
                    value = self._model.get_label_config_center().get_drawing_value()
                    self._model.modify_voxels(None, value, roi, target_row, False)
        elif run_text == 'Copy':
            target_row = self.target_box.currentIndex()
            if target_row != 0:
                target_row -= 1
            for roi in self.selected_rois:
                self._model.modify_voxels(None, roi, roi, target_row, False)
        elif run_text == 'Split':
            for roi in self.selected_rois:
                self._model.new_image(None, None, 'rainbow')
                self._model.modify_voxels(None, roi, roi, 0, False)
        self.selected_rois = []
        self.roi_edit.clear()


class SurfROIDialog(ROIDialog):
    """Surface ROI toolset"""

    def __init__(self, model, label_config_center, parent=None):
        super(SurfROIDialog, self).__init__(model, label_config_center, parent)
        self._vx_label = "Vertex"

        self._init_gui()
        self._create_actions()

    def _fill_target_box(self):
        self._last_target_update_enable = False
        self.target_box.clear()
        overlay_list = self._model.get_overlay_list()
        self.target_box.addItem("New Overlay")
        self.target_box.addItems(overlay_list)
        last_target_idx = 0
        for idx, name in enumerate(overlay_list):
            if name == ROIDialog.last_target_name:
                last_target_idx = idx + 1
                break
        self.target_box.setCurrentIndex(last_target_idx)
        self._last_target_update_enable = True

    def show_dialog(self):
        self.connect(self._model, SIGNAL("currentIndexChanged"), self._fill_target_box)
        super(SurfROIDialog, self).show_dialog()

    def hide_dialog(self):
        self.disconnect(self._model, SIGNAL("currentIndexChanged"), self._fill_target_box)
        super(SurfROIDialog, self).hide_dialog()

    def _run(self):
        super(SurfROIDialog, self)._run()

        if self.target_box.isEnabled() and \
           str(self.target_box.currentText()) == "New Overlay":
            self._model.add_item(self._model.current_index(), islabel=True)

        run_text = str(self.action_box.currentText())

        if run_text == 'Labeling':
            target_row = self.target_box.currentIndex()
            if target_row != 0:
                target_row -= 1
            if not self._label_config_center.is_drawing_valid():
                QMessageBox.critical(self, "Invalid ROI Drawing Value",
                                     "Please specify an valid drawing value")
            else:
                for roi in self.selected_rois:
                    value = self._label_config_center.get_drawing_value()
                    self._model.set_vertices_value(value, roi=roi,
                                                   target_row=target_row)
        elif run_text == 'Copy':
            target_row = self.target_box.currentIndex()
            if target_row != 0:
                target_row -= 1
            for roi in self.selected_rois:
                self._model.set_vertices_value(value=roi, roi=roi,
                                               target_row=target_row)
        elif run_text == 'Split':
            for roi in self.selected_rois:
                self._model.add_item(self._model.current_index(), islabel=True)
                self._model.set_vertices_value(value=roi, roi=roi,
                                               target_row=0)
        self.clear_rois()
