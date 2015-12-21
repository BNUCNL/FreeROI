# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings


class LabelDialog(QDialog, DrawSettings):
    """
    A dialog window for label selection.

    """
    color_changed = pyqtSignal()
    def __init__(self, model, parent=None):
        """
        Initialize a dialog widget.

        """
        super(LabelDialog, self).__init__(parent)
        self._model = model
        self._label_config = model.get_current_label_config()
        self._label_config_center = model.get_label_config_center()
        
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self._init_gui()
        self._create_actions()
        #self._update_items()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.setWindowTitle('Select a label')
        name_label = QLabel('Label:')
        self.combobox = QComboBox()
        self._update_combobox()

        color_label = QLabel('Color:')
        label = str(self.combobox.currentText())
        if label:
            self.color_button = ColorButton(self._label_config.get_label_color(label))
        else:
            self.color_button = ColorButton()

        size_label = QLabel('Size:')
        self.size_edit = QSpinBox()
        self.size_edit.setRange(1, 10)
        self.size_edit.setValue(4)
        
        self.add_label = QPushButton('Add')
        self.del_label = QPushButton('Delete')
        self.save_label = QPushButton('Save')

        grid_layout = QGridLayout()
        grid_layout.addWidget(name_label, 0, 0)
        grid_layout.addWidget(self.combobox, 0 ,1)
        grid_layout.addWidget(color_label, 1, 0)
        grid_layout.addWidget(self.color_button, 1, 1)
        grid_layout.addWidget(size_label, 2, 0)
        grid_layout.addWidget(self.size_edit, 2, 1)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.add_label)
        hbox_layout.addWidget(self.del_label)
        hbox_layout.addWidget(self.save_label)
        
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)
    
    def _update_combobox(self):
        self.combobox.clear()
        label_list = self._label_config.get_label_list()
        self.combobox.addItems(QStringList(label_list))

    def _create_actions(self):
        """
        Create some actions.

        """
        #self._model.dataChanged.connect(self._update_items)
        # --
        # select a label and change current pen value
        # --
        self.combobox.currentIndexChanged[QString].connect(self._update_color)   
        self.color_button.color_changed.connect(self._update_label_color)
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

    def _update_color(self, s):
        s = str(s)
        if s:
            self.color_button.set_current_color(self._label_config.get_label_color(s))
        
    def _update_label_color(self, color):
        label = str(self.combobox.currentText())
        if label:
            self._label_config.update_label_color(label, color)
            self.color_changed.emit()
        
    def _add_label(self):
        """
        Add a new label.

        """
        #name, name_ok = QInputDialog.getText(self, '', 'Input a label name:')
        #if name_ok and not name.isEmpty():
        #    index = self._model.currentIndex()
        #    if name in self._model.data(index, Qt.UserRole + 4):
        #        QMessageBox.warning(self, 'Warning',
        #                            'Label name you input exists!')
        #    else:
        #        idx, idx_ok = QInputDialog.getText(self, '', 'Input a value:')
        #        if idx_ok and not idx.isEmpty():
        #            temp = self._model.data(index, Qt.UserRole + 4)
        #            if int(idx) in temp.values():
        #                QMessageBox.warning(self, 'Warning',
        #                                    'Label value you input exits!')
        #            else:
        #                x = (str(name), int(idx))
        #                self._model.setData(index, Qt.UserRole + 4, x)
        
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
                self._label_config.remove_label(str(label))
                self._update_combobox()

    def _save_label(self):
        self._label_config.save()
        
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

    def get_current_size(self):
        if self.is_valid_label():
            return self.size_edit.value()

    # For DrawSettings
    def is_brush(self):
        return True
    
    def is_drawing_valid(self):
        return self.is_valid_label()

    def get_drawing_value(self):
        return self.get_current_index()    

    def get_drawing_size(self):
        return self.get_current_size()

    def get_drawing_color(self):
        return self.get_current_color()


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
        self.index_edit.setText(str(self._label_config.new_index()))
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
       
        if self._label_config.has_label(label):
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
        if self._label_config.has_index(index):
            QMessageBox.critical(self, "Index exists!",
                    "The index you input already exists, you must choose"
                    " another index!")
            self.index_edit.setFocus()
            return
        self._label_config.add_label(label, index, color)
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
