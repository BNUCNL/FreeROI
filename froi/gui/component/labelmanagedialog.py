# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings
from addlabeldialog import *
from labelconfigcenter import ConfigLabelModel
from labeleditdialog import LabelEditDialog


class LabelManageDialog(QDialog, DrawSettings):
    """
    A dialog window for label selection.

    """
    color_changed = pyqtSignal()
    label_edit_enabled = pyqtSignal()
    def __init__(self, model, label_configs, parent=None):
        """
        Initialize a dialog widget.

        """
        super(LabelManageDialog, self).__init__(parent)
        self._model = model
        self._label_configs = label_configs
        self._label_model = map(ConfigLabelModel, label_configs)
        self.setWindowModality(Qt.NonModal)
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.setWindowTitle('Label Management')
        self.combobox = QComboBox()

        self.list_view = QListView(self)
        self.list_view.setWindowTitle('Edit Label')

        list_view_model = QStandardItemModel(self.list_view)
        # list_view_model.appendRow(QStandardItem("None"))
        for x in self._label_configs:
            list_view_model.appendRow(QStandardItem(x.get_name()))
        self.list_view.setModel(list_view_model)

        self.add_label = QPushButton('Add')
        self.del_label = QPushButton('Delete')
        self.edit_label = QPushButton('Edit')

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.add_label)
        hbox_layout.addWidget(self.del_label)
        hbox_layout.addWidget(self.edit_label)
        
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.list_view)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)
    
    def _update_combobox(self):
        self.combobox.clear()
        # label_list = self._label_config_center.get_current_label_list()
        # self.combobox.addItems(QStringList(label_list))
        # self._label_config_center._update_labels()
        #pass

    def _create_actions(self):
        """
        Create some actions.

        """
        self.add_label.clicked.connect(self._add_label)
        self.del_label.clicked.connect(self._del_label)
        self.edit_label.clicked.connect(self._edit_label)

    def _update_items(self):
        """
        Add items for combo box.

        """
        index = self._model.currentIndex()
        label_pairs = self._model.data(index, Qt.UserRole + 4)
        label_names = label_pairs.keys()
        self.combobox.clear()
        self.combobox.addItems(label_names)

    def _update_label_color(self, color):
        label = str(self.combobox.currentText())
        if label:
            self._label_config.update_label_color(label, color)
            self.color_changed.emit()
        
    def _add_label(self):
        """
        Add a new label.

        """
        add_dialog = AddLabelDialog(self._label_config)
        add_dialog.exec_()
        self._update_combobox()

    def _del_label(self):
        """
        Delete a existing label.

        """
        label = self.combobox.currentText()
        if label:
            button = QMessageBox.warning(self, "Delete label", 
                    "Are you sure that you want to delete label %s ?" % label,
                    QMessageBox.Yes,
                    QMessageBox.No)
            if button == QMessageBox.Yes:
                self._label_config.remove_current_label(str(label))
                self._update_combobox()

    def _edit_label(self):
        index = self.list_view.currentIndex().row()
        label_edit_dialog = LabelEditDialog(self._model, self._label_model[index], self._label_configs[index])
        label_edit_dialog.setWindowTitle(self._label_configs[index].get_name())
        label_edit_dialog.exec_()

    def _save_label(self):
        self._label_config.current_save()
        
    def is_valid_label(self):
        return self.combobox.currentText()

    def get_current_label(self):
        if self.is_valid_label():
            return str(self.combobox.currentText())
        raise ValueError, "Current label invalid"

    def get_current_index(self):
        if self.is_valid_label():
            return self._label_config.get_label_index(self.get_current_label())
        raise ValueError, "Current label invalid"

    def get_current_color(self):
        if self.is_valid_label():
            return self._label_config.get_label_color(self.get_current_label())



