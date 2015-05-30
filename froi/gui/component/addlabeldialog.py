__author__ = 'liuzhaoguo'
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class AddLabelDialog(QDialog):
    """
    A dialog for adding a new label.

    """
    def __init__(self, label_config, parent=None):
        super(AddLabelDialog, self).__init__(parent)
        self._label_config = label_config

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        self.setWindowTitle("Add a new label")
        label_label = QLabel("Label")
        self.label_edit = QLineEdit()
        index_label = QLabel("Index")
        self.index_edit = QLineEdit()
        #self.index_edit.setText(str(self._label_config.new_index()))
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

    def _create_actions(self):
        self.add_button.clicked.connect(self._add_label)
        self.cancel_button.clicked.connect(self.done)

    def _add_label(self):
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

        if self._label_config.has_current_label(label):
            button = QMessageBox.warning(self, "Label exists!",
                                         "The label you input already exists, if you change its "
                                         "index, the old voxel valuse you've write won't be "
                                         "updated. Are you sure that you "
                                         "want to overwrite its settings?",
                                         QMessageBox.Yes,
                                         QMessageBox.No)
            if button != QMessageBox.Yes:
                self.label_edit.setFocus()
                return
            self._label_config.remove_label(label)
        if self._label_config.has_current_index(index):
            QMessageBox.critical(self, "Index exists!",
                                 "The index you input already exists, you must choose"
                                 " another index!")
            self.index_edit.setFocus()
            return
        self._label_config.add_current_label(label, index, color)
        self.done(0)

class ColorButton(QPushButton):
    """
    Button to choose color from a color dialog.

    """
    default_color = QColor(255, 0, 0)
    icon_size = QSize(32, 32)
    color_changed = pyqtSignal(QColor)

    def __init__(self, init_color=None, parent=None):
        super(ColorButton, self).__init__(parent)
        if init_color is None:
            init_color = self.default_color
        self.current_color = init_color
        self._update_icon()
        self.clicked.connect(self._choose_color)

    def _update_icon(self):
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