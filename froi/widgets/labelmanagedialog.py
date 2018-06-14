# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import glob

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings
from labeleditdialog import LabelEditDialog
from ..core.labelconfig import LabelConfig
from addlabelgroupdialog import AddLabelGroupDialog


class LabelManageDialog(QDialog, DrawSettings):
    """A dialog window for label selection."""
    color_changed = pyqtSignal()
    label_edit_enabled = pyqtSignal()

    def __init__(self, label_configs, list_view_model, label_models, label_config_dir,
                 label_config_suffix, parent=None):
        """Initialize a dialog widget."""
        super(LabelManageDialog, self).__init__(parent)
        self._label_configs = label_configs
        self._label_config_dir = label_config_dir
        self._label_config_suffix = label_config_suffix
        self._label_models = label_models
        self._list_view_model = list_view_model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        self.setWindowTitle('Label Management')
        self.combobox = QComboBox()

        self.list_view = QListView(self)
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_view.setModel(self._list_view_model)

        self.add_btn = QPushButton('Add')
        self.del_btn = QPushButton('Delete')
        self.edit_btn = QPushButton('Edit')

        if self._list_view_model.rowCount() == 0:
            self.del_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.add_btn)
        hbox_layout.addWidget(self.del_btn)
        hbox_layout.addWidget(self.edit_btn)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.list_view)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        """Create some actions."""
        self.add_btn.clicked.connect(self._add_label)
        self.del_btn.clicked.connect(self._del_label)
        self.edit_btn.clicked.connect(self._edit_label)

    def _update_label_color(self, color):
        label = str(self.combobox.currentText())
        if label:
            self._label_config.update_label_color(label, color)
            self.color_changed.emit()

    def _update_button_status(self):
        if self._list_view_model.rowCount() == 0:
            self.del_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
        else:
            self.del_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)

    def _add_label(self):
        """Add a new label."""
        add_label_group_dialog = AddLabelGroupDialog(self)
        add_label_group_dialog.setWindowTitle("Enter a label group name.")
        add_label_group_dialog.exec_()

        new_label_group_name = add_label_group_dialog.get_new_label_group_name()
        if new_label_group_name:
            for label_config in self._label_configs:
                if new_label_group_name == label_config.get_name():
                    QMessageBox.warning(self, "Add label",
                                        "The label %s has exsited!" % new_label_group_name,
                                        QMessageBox.Yes)
                    return

            new_label_group_name = new_label_group_name.replace(" ", "_")
            lbl_path = os.path.join(self._label_config_dir,
                                    new_label_group_name + '.' + self._label_config_suffix)
            f = open(lbl_path, "w")
            f.close()
            new_label_config = map(LabelConfig, glob.glob(lbl_path))
            self._label_configs.append(new_label_config[0])
            self._label_models.append(QStandardItemModel())
            self._list_view_model.appendRow(QStandardItem(new_label_group_name))
            self._update_button_status()

    def _del_label(self):
        """Delete a existing label."""
        row = self.list_view.currentIndex().row()
        if row == -1 and self._list_view_model.rowCount() > 0:
            row = self._list_view_model.rowCount() - 1
        button = QMessageBox.warning(self, "Delete label",
                                     "Are you sure that you want to delete label %s ?" %
                                     self._label_configs[row].get_name(),
                                     QMessageBox.Yes,
                                     QMessageBox.No)
        if button == QMessageBox.Yes:
            os.remove(self._label_configs[row].get_filepath())
            del self._label_configs[row]
            del self._label_models[row]
            self._list_view_model.removeRow(row)
            self._update_button_status()

    def _edit_label(self):
        index = self.list_view.currentIndex().row()
        label_edit_dialog = LabelEditDialog(self._label_models[index], self._label_configs[index])
        label_edit_dialog.setWindowTitle("Edit " + self._label_configs[index].get_name())
        label_edit_dialog.exec_()
