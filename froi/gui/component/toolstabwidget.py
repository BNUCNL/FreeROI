# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from no_gui_tools import edge_detection
from roimergedialog import ROIMergeDialog
from roi2gwmidialog import Roi2gwmiDialog
from regularroidialog import RegularROIDialog
from froi.gui.base.utils import *

class ToolsTabWidget(QDialog):
    """
    Model for tools tabwidget.

    """

    def __init__(self, model, main_win, parent=None):
        super(ToolsTabWidget, self).__init__(parent)
        self._icon_dir = get_icon_dir()

        self._init_gui()
        self._create_actions()
        self._main_win = main_win
        self._model = model

    def _init_gui(self):
        """
        Initialize GUI.
        """
        self.detection_button = QPushButton()
        self.detection_button.setFocusPolicy(Qt.NoFocus)
        self.detection_button.setIcon(QIcon(os.path.join(self._icon_dir,
                                                         'edge_detection.png')))
        self.detection_button.setEnabled(True)
        self.detection_button.setToolTip("edge detection")

        self.roimerge_button = QPushButton()
        self.roimerge_button.setFocusPolicy(Qt.NoFocus)
        self.roimerge_button.setIcon(QIcon(os.path.join(self._icon_dir,
                                                        'merging.png')))
        self.roimerge_button.setEnabled(True)
        self.roimerge_button.setToolTip("ROI Merging")

        self.roi2interface_button = QPushButton()
        self.roi2interface_button.setFocusPolicy(Qt.NoFocus)
        self.roi2interface_button.setIcon(QIcon(os.path.join(self._icon_dir,
                                                             'r2i.png')))
        self.roi2interface_button.setEnabled(True)
        self.roi2interface_button.setToolTip("ROI2Interface")

        self.regularroi_button = QPushButton()
        self.regularroi_button.setFocusPolicy(Qt.NoFocus)
        self.regularroi_button.setIcon(QIcon(os.path.join(self._icon_dir,
                                                         'sphere_and_cube.png')))
        self.regularroi_button.setEnabled(True)
        self.regularroi_button.setToolTip("Regular ROI")

        gridlayout = QGridLayout(self)
        gridlayout.addWidget(self.detection_button, 0, 0)
        gridlayout.addWidget(self.roimerge_button, 0, 1)
        gridlayout.addWidget(self.roi2interface_button, 0, 2)
        gridlayout.addWidget(self.regularroi_button, 1, 0)

    def _create_actions(self):
        """
        Create actions about the toobar
        """
        self.detection_button.clicked.connect(self._edge_detection_clicked)
        self.roimerge_button.clicked.connect(self._roimerge_clicked)
        self.roi2interface_button.clicked.connect(self._r2i_clicked)
        self.regularroi_button.clicked.connect(self._regular_roi_clicked)

    def _edge_detection_clicked(self):
        '''
        edge detection clicked
        '''
        if self.detection_button.isEnabled():
            edge_detection(self._model)

    def _roimerge_clicked(self):
        '''
        roi merge clicked
        '''
        if self.roimerge_button.isEnabled():
            new_dialog = ROIMergeDialog(self._model)
            new_dialog.exec_()

    def _r2i_clicked(self):
        '''
        roi2interface clicked
        '''
        if self.roi2interface_button.isEnabled():
            new_dialog = Roi2gwmiDialog(self._model)
            new_dialog.exec_()

    def _regular_roi_clicked(self):
        '''
        regular roi clicked
        '''
        if self.regularroi_button.isEnabled():
            new_dialog = RegularROIDialog(self._model)
            new_dialog.exec_()
