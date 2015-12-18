# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class AddLabelDialog(QDialog):
    """A dialog for adding a new label."""
    def __init__(self, label_configs, edit_label=None, parent=None):
        super(AddLabelDialog, self).__init__(parent)
        self._edit_label = edit_label
        self._new_label = []
        self._label_configs = label_configs
        self._is_valid_label = False
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        label_label = QLabel("Label")
        self.label_edit = QLineEdit()
        index_label = QLabel("Index")
        self.index_edit = QLineEdit()
        regx = QRegExp("[0-9]+$")
        validator = QRegExpValidator(regx, self.index_edit)
        self.index_edit.setValidator(validator)

        self.index_edit.setEnabled(self._edit_label is None)
        color_label = QLabel("Color")
        self.color_button = ColorButton()

        grid_layout = QGridLayout()
        grid_layout.addWidget(label_label, 0, 0)
        grid_layout.addWidget(self.label_edit, 0, 1)
        grid_layout.addWidget(index_label, 1, 0)
        grid_layout.addWidget(self.index_edit, 1, 1)
        grid_layout.addWidget(color_label, 2, 0)
        grid_layout.addWidget(self.color_button, 2, 1)

        self.add_button = QPushButton("Add")
        self.cancel_button = QPushButton("Cancel")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.add_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

        if self._edit_label:
            self.index_edit.setText(self._edit_label[0])
            self.label_edit.setText(self._edit_label[1])
            self.color_button._set_current_color(self._edit_label[2])
            self.add_button.setText("OK")

    def _create_actions(self):
        self.add_button.clicked.connect(self._add_label)
        self.cancel_button.clicked.connect(self.done)

    def _add_label(self):
        self._new_label = []
        label = str(self.label_edit.text())
        if not label:
            QMessageBox.critical(self, "No label name",
                                 "Please speicify your label name.")
            return

        index = self.index_edit.text()
        if not index:
            QMessageBox.critical(self, "No index",
                                 "Please specify a index for your label.")
            return
        index = int(str(self.index_edit.text()))

        color = self.color_button.get_current_color()
        if not color.isValid():
            QMessageBox.critical(self, "Color invalid",
                                 "Please choose a valid color for your label.")
            return
        label = str(label)
        self._new_label.append(index)
        self._new_label.append(str(label.replace(" ", "_")))
        self._new_label.append(color)

        if self._new_label[1] in self._label_configs.get_label_list():
            if self._edit_label is None or self._edit_label[1] != self._new_label[1]:
                QMessageBox.warning(self, "Add label",
                                    "The label %s has exsited!" % self._new_label[1],
                                    QMessageBox.Yes)
                return
        if not self._edit_label:
            if self._new_label[0] in self._label_configs.get_index_list():
                QMessageBox.warning(self, "Add label",
                                    "The index %s has exsited!" % self._new_label[0],
                                    QMessageBox.Yes)
                return

        self._is_valid_label = True
        self.done(0)

    def get_new_label(self):
        if self._is_valid_label:
            return self._new_label
        else:
            return None

class ColorButton(QPushButton):
    """Button to choose color from a color dialog."""
    default_color = QColor(255, 0, 0)
    icon_size = QSize(32, 32)
    color_changed = pyqtSignal(QColor)

    def __init__(self, init_color=None, parent=None):
        super(ColorButton, self).__init__(parent)
        if not init_color:
            init_color = self.default_color
        self.current_color = init_color
        self._update_icon()
        self.clicked.connect(self._choose_color)

    def _update_icon(self):
        if self.current_color:
            icon_image = QImage(self.icon_size, QImage.Format_RGB888)
            icon_image.fill(self.current_color.rgb())
            icon_image = icon_image.rgbSwapped()
            icon_pm = QPixmap.fromImage(icon_image)
            self.setIcon(QIcon(icon_pm))

    def _choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self._set_current_color(color)

    def _set_current_color(self, color):
        self.set_current_color(color)
        self.color_changed.emit(color)

    def set_current_color(self, color):
        self.current_color = color
        self._update_icon()

    def get_current_color(self):
        return self.current_color