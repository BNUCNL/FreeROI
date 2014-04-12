# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

from PyQt4.QtGui import *

from volumedintensitydialog import VolumeIntensityDialog
from roiorvoxelcurvedialog import  ROIOrVoxelCurveDialog
from froi.gui.base.utils import *

class StatsWidget(QDialog):
    """
    Model for tools tabwidget.

    """

    def __init__(self, model, main_win, parent=None):
        super(StatsWidget, self).__init__(parent)

        self._icon_dir = get_icon_dir()

        self._init_gui()
        self._create_actions()
        self._main_win = main_win
        self._model = model


    def _init_gui(self):
        """
        Initialize GUI.
        """

        self.volume_button = QPushButton()
        #self.volume_button.setFlat(True)
        #self.volume_button.setFocusPolicy(Qt.NoFocus)
        self.volume_button.setIcon(QIcon(os.path.join(self._icon_dir, 'volume_intensity.png')))
        self.volume_button.setEnabled(True)
        self.volume_button.setToolTip("Volume intensity")

        self.roiorvoxel_button = QPushButton()
        #self.roiorvoxel_button.setFlat(True)
        #self.roiorvoxel_button.setFocusPolicy(Qt.NoFocus)
        self.roiorvoxel_button.setIcon(QIcon(os.path.join(self._icon_dir, 'voxel_curve.png')))
        self.roiorvoxel_button.setEnabled(True)
        self.roiorvoxel_button.setToolTip("Roiorvoxelcurve")

        gridlayout = QGridLayout(self)
        gridlayout.addWidget(self.volume_button, 1, 0)
        gridlayout.addWidget(self.roiorvoxel_button, 1, 1)


    def _create_actions(self):
        """
        Create actions about the toobar
        """
        # self.brush_pushbutton.clicked.connect(self._mainwindow._brush_enable)
        # self.roibrush_pushbutton.clicked.connect(self._mainwindow._roibrush_enable)
        self.volume_button.clicked.connect(self._volume_intensity_clicked)
        self.roiorvoxel_button.clicked.connect(self._voxel_curve_clicked)


    def _volume_intensity_clicked(self):
        '''
        region growing clicked
        '''
        if self.volume_button.isEnabled():
            new_dialog = VolumeIntensityDialog(self._model, self._main_win)
            new_dialog.exec_()

    def _voxel_curve_clicked(self):
        '''
        watershed clicked
        '''
        if self.roiorvoxel_button.isEnabled():
            self.new_dialog = ROIOrVoxelCurveDialog(self._model, self)
            self.new_dialog.exec_()









