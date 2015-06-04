# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.gui.base.utils import *
from hosubcorticaldialog import HOsubcorticalDialog
from hocorticaldialog import HOCorticalDialog

class AtlasTabWidget(QDialog):
    """
    Model for atlas tabwidget.

    """

    def __init__(self, model, main_win, parent=None):
        super(AtlasTabWidget, self).__init__(parent)
        self._icon_dir = get_icon_dir()

        self._init_gui()
        self._create_actions()
        self._main_win = main_win
        self._model = model

    def _init_gui(self):
        """
        Initialize GUI.
        """
        self.HOsubcortical_button = QPushButton()
        self.HOsubcortical_button.setFocusPolicy(Qt.NoFocus)
        self.HOsubcortical_button.setIcon(QIcon(os.path.join(self._icon_dir, 'H-O subcortical.png')))
        self.HOsubcortical_button.setEnabled(True)
        self.HOsubcortical_button.setToolTip("Harvard-Oxford SubCortical Atlas")

        self.HOcortical_button = QPushButton()
        self.HOcortical_button.setFocusPolicy(Qt.NoFocus)
        self.HOcortical_button.setIcon(QIcon(os.path.join(self._icon_dir, 'H-O cortical.png')))
        self.HOcortical_button.setEnabled(True)
        self.HOcortical_button.setToolTip("Harvard-Oxford Cortical Atlas")


        gridlayout = QGridLayout(self)
        gridlayout.addWidget(self.HOsubcortical_button, 0, 0)
        gridlayout.addWidget(self.HOcortical_button, 0, 1)


    def _create_actions(self):
        """
        Create actions about the button
        """
        self.HOsubcortical_button.clicked.connect(self._HOsubcortical_clicked)
        self.HOcortical_button.clicked.connect(self._HOcortical_clicked)


    def _HOsubcortical_clicked(self):
        '''
        Harvard-Oxford SubCortical clicked
        '''
        if self.HOsubcortical_button.isEnabled():
            new_dialog = HOsubcorticalDialog(self._model, self._main_win)
            new_dialog.exec_()

    def _HOcortical_clicked(self):
        '''
        Harvard-Oxford Cortical clicked
        '''
        if self.HOcortical_button.isEnabled():
            new_dialog = HOCorticalDialog(self._model, self._main_win)
            new_dialog.exec_()