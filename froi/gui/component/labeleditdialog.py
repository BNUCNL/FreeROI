# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings
from addlabeldialog import *
from labelconfigcenter import ConfigLabelModel


class LabelEditDialog(QDialog, DrawSettings):
    """
    A dialog window for label selection.

    """
    color_changed = pyqtSignal()
    label_edit_enabled = pyqtSignal()
    def __init__(self, model, label_model, label_configs, parent=None):
        """
        Initialize a dialog widget.

        """
        super(LabelEditDialog, self).__init__(parent)
        self._model = model
        self._label_model = label_model
        self._label_configs = label_configs
        self.setWindowModality(Qt.NonModal)
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.setWindowModality(Qt.NonModal)

        self.list_view = QListView(self)
        self.list_view.setWindowTitle('Edit Label')
        self.list_view.setModel(self._label_model)

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
        item_text = self.list_view.currentIndex().data().toString().split(' ')
        index = item_text[0]
        label = item_text[1]
        print 'label: ', label
        button = QMessageBox.warning(self, "Delete label",
                "Are you sure that you want to delete label %s ?" % label,
                 QMessageBox.Yes,
                QMessageBox.No)
        if button == QMessageBox.Yes:
            print 'index: ', self._label_configs.get_label_index(str(label))
            self._label_model.removeRow(self.list_view.currentIndex().row())
            self._label_configs.remove_label(str(label))
            self._label_configs.save()

    def _edit_label(self):
        self._label_config.current_save()

    def _save_label(self):
        self._label_config.current_save()
        
    def is_valid_label(self):
        return self.combobox.currentText()







