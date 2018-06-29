# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from no_gui_tools import gen_label_color

from drawsettings import DrawSettings
from addlabeldialog import *


class LabelEditDialog(QDialog, DrawSettings):
    """A dialog window for label selection."""
    color_changed = pyqtSignal()
    label_edit_enabled = pyqtSignal()

    def __init__(self, label_model, label_configs, parent=None):
        """Initialize a dialog widget."""
        super(LabelEditDialog, self).__init__(parent)
        self._label_model = label_model
        self._label_configs = label_configs
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        self.setWindowModality(Qt.NonModal)

        self.list_view = QListView(self)
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_view.setModel(self._label_model)

        self.add_btn = QPushButton('Add')
        self.del_btn = QPushButton('Delete')
        self.edit_btn = QPushButton('Edit')

        if self._label_model.rowCount() == 0:
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

    def _update_button_status(self):
        if self._label_model.rowCount() == 0:
            self.del_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
        else:
            self.del_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)

    def _add_label(self):
        """Add a new label."""
        add_dialog = AddLabelDialog(self._label_configs)
        add_dialog.setWindowTitle("Add a new label")
        add_dialog.exec_()
        new_label = add_dialog.get_new_label()
        if new_label:
            text_index_icon_item = QStandardItem(gen_label_color(new_label[2]),
                                                 str(new_label[0]) + '  ' + new_label[1])
            self._label_configs.add_label(new_label[1], new_label[0], new_label[2])
            order_index = self._label_configs.get_index_list().index(new_label[0])
            self._label_model.insertRow(order_index, text_index_icon_item)
            self._label_configs.save()
            self._update_button_status()

    def _del_label(self):
        """Delete a existing label."""
        row = self.list_view.currentIndex().row()
        if row == -1 and self._label_model.rowCount() > 0:
            row = self._label_model.rowCount() - 1
        index = self._label_configs.get_index_list()[row]
        label = self._label_configs.get_index_label(index)
        button = QMessageBox.warning(self, "Delete label",
                "Are you sure that you want to delete label %s ?" % label,
                 QMessageBox.Yes,
                 QMessageBox.No)
        if button == QMessageBox.Yes:
            self._label_model.removeRow(row)
            self._label_configs.remove_label(label)
            self._label_configs.save()
            self._update_button_status()

    def _edit_label(self):
        row = self.list_view.currentIndex().row()
        index = self._label_configs.get_index_list()[row]
        label = self._label_configs.get_index_label(index)
        add_dialog = AddLabelDialog(self._label_configs, (str(index), label, self._label_configs.get_label_color(label)))
        add_dialog.setWindowTitle("Edit the label")
        add_dialog.exec_()
        edit_label = add_dialog.get_new_label()

        if edit_label:
            self._label_model.removeRow(row)
            text_index_icon_item = QStandardItem(gen_label_color(edit_label[2]),
                                                 str(edit_label[0]) + '  ' + edit_label[1])
            self._label_model.insertRow(row, text_index_icon_item)
            self._label_configs.edit_label(label, edit_label[1], edit_label[2])
            self._label_configs.save()
