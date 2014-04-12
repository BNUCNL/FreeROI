# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings


class ROIEraserDialog(QDialog, DrawSettings):
    """
    A dialog window for eraser settings.
    
    """
    eraser_color = QColor(255, 255, 255)

    def __init__(self, parent=None):
        super(ROIEraserDialog, self).__init__(parent)

        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Tool | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self._init_gui()
        
    def _init_gui(self):
        self.setWindowTitle("ROI Eraser")
        vlayout = QVBoxLayout()
        info_label = QLabel("Select an ROI, and it will be removed.")
        vlayout.addWidget(info_label)
        self.setLayout(vlayout)

    # For DrawSettings
    def is_roi_tool(self):
        return True

    def is_drawing_valid(self):
        return True

    def get_drawing_value(self):
        return 0

    def get_drawing_size(self):
        return self.size_edit.value()
    
    def get_drawing_color(self):
        return self.eraser_color
        

