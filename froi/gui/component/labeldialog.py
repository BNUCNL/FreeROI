# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings
from addlabeldialog import *


class LabelDialog(QDialog, DrawSettings):
    """
    A dialog window for label selection.

    """
    color_changed = pyqtSignal()
    label_edit_enabled = pyqtSignal()
    def __init__(self, model, label_config_center, parent=None):
        """
        Initialize a dialog widget.

        """
        super(LabelDialog, self).__init__(parent)
        self._model = model
        self._label_config = model.get_current_label_config()
        self._label_config_center = label_config_center
        
        self.setWindowModality(Qt.NonModal)
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.setWindowTitle('Select a label')
        self.combobox = QComboBox()

        self.add_label = QPushButton('Add')
        self.del_label = QPushButton('Delete')
        self.save_label = QPushButton('Save')

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.add_label)
        hbox_layout.addWidget(self.del_label)
        hbox_layout.addWidget(self.save_label)
        
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self._label_config_center)
        vbox_layout.addLayout(hbox_layout)

        self._label_config_center.size_label.setVisible(False);
        self._label_config_center.size_edit.setVisible(False);
        self.setLayout(vbox_layout)
    
    def _update_combobox(self):
        self.combobox.clear()
        label_list = self._label_config_center.get_current_label_list()
        self.combobox.addItems(QStringList(label_list))
        self._label_config_center._update_labels()
        #pass

    def _create_actions(self):
        """
        Create some actions.

        """
        self.add_label.clicked.connect(self._add_label)
        self.del_label.clicked.connect(self._del_label)
        self.save_label.clicked.connect(self._save_label)

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



