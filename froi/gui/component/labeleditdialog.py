# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings
from addlabeldialog import *

class LabelEditDialog(QDialog, DrawSettings):
    """
    A dialog window for label selection.

    """
    color_changed = pyqtSignal()
    label_edit_enabled = pyqtSignal()
    def __init__(self, label_model, label_configs, parent=None):
        """
        Initialize a dialog widget.

        """
        super(LabelEditDialog, self).__init__(parent)
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
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
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

    def get_icon(self, color):
        icon_image = QImage(QSize(32, 32), QImage.Format_RGB888)
        icon_image.fill(color.rgb())
        icon_image = icon_image.rgbSwapped()
        icon_pixmap = QPixmap.fromImage(icon_image)
        return QIcon(icon_pixmap)

    def _add_label(self):
        """
        Add a new label.

        """
        add_dialog = AddLabelDialog(self)
        add_dialog.setWindowTitle("Add a new label")
        add_dialog.exec_()
        new_label = add_dialog.get_new_label()
        if new_label:
            text_index_icon_item = QStandardItem(self.get_icon(new_label[2]),
                                             str(new_label[0]) + '  ' + new_label[1])
            self._label_model.appendRow(text_index_icon_item)
            self._label_configs.add_label(new_label[1], new_label[0], new_label[2])
            self._label_configs.save()

    def _del_label(self):
        """
        Delete a existing label.

        """
        row = self.list_view.currentIndex().row()
        label = self._label_configs.get_label_list()[row]
        button = QMessageBox.warning(self, "Delete label",
                "Are you sure that you want to delete label %s ?" % label,
                 QMessageBox.Yes,
                 QMessageBox.No)
        if button == QMessageBox.Yes:
            self._label_model.removeRow(row)
            self._label_configs.remove_label(label)
            self._label_configs.save()

    def _edit_label(self):
        row = self.list_view.currentIndex().row()
        label = self._label_configs.get_label_list()[row]
        index = self._label_configs.get_label_index(label)
        add_dialog = AddLabelDialog(self, (str(index), label, self._label_configs.get_label_color(label)))
        add_dialog.setWindowTitle("Edit the label")
        add_dialog.exec_()
        edit_label = add_dialog.get_new_label()

        if edit_label:
            self._label_model.removeRow(row)
            text_index_icon_item = QStandardItem(self.get_icon(edit_label[2]),
                                                 str(edit_label[0]) + '  ' + edit_label[1])
            self._label_model.insertRow(row, text_index_icon_item)
            self._label_configs.edit_label(label, edit_label[1], edit_label[2])
            self._label_configs.save()


