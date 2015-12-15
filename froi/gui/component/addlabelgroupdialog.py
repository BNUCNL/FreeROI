# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtGui import *

class AddLabelGroupDialog(QDialog):
    """A dialog for adding a new label."""
    def __init__(self, parent=None):
        super(AddLabelGroupDialog, self).__init__(parent)
        self._new_label_group_name = None
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        label_group_name = QLabel("Label")
        self.label_group_name_edit = QLineEdit()

        hbox_layout1 = QHBoxLayout()
        hbox_layout1.addWidget(label_group_name)
        hbox_layout1.addWidget(self.label_group_name_edit)

        self.add_button = QPushButton("Add")
        self.cancel_button = QPushButton("Cancel")

        hbox_layout2 = QHBoxLayout()
        hbox_layout2.addWidget(self.add_button)
        hbox_layout2.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(hbox_layout1)
        vbox_layout.addLayout(hbox_layout2)
        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.add_button.clicked.connect(self._add_label_group)
        self.cancel_button.clicked.connect(self.done)

    def _add_label_group(self):
        self._new_label_group_name = str(self.label_group_name_edit.text())
        if not self._new_label_group_name:
            QMessageBox.critical(self, "No label name",
                                 "Please speicify your label name.")
            return
        self.done(0)

    def get_new_label_group_name(self):
         return self._new_label_group_name

