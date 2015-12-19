# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings


class EraserDialog(QDialog, DrawSettings):
    """
    A dialog window for eraser settings.
    
    """
    eraser_color = QColor(255, 255, 255)

    def __init__(self, parent=None):
        super(EraserDialog, self).__init__(parent)

        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self._init_gui()
        
    def _init_gui(self):
        size_label = QLabel("Size:")
        self.size_edit = QSpinBox()
        self.size_edit.setRange(1, 10)
        self.size_edit.setValue(4)
        
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(size_label)
        hbox_layout.addWidget(self.size_edit)

        self.setLayout(hbox_layout)

    # For DrawSettings
    def is_eraser(self):
        return True

    def is_drawing_valid(self):
        return True

    def get_drawing_value(self):
        return 0

    def get_drawing_size(self):
        return self.size_edit.value()
    
    def get_drawing_color(self):
        return self.eraser_color
        
