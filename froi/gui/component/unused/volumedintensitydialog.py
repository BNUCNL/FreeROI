__author__ = 'zhouguangfu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar


class VolumeIntensityDialog(QDialog):
    """
    A dialog for action of voxel time point curve display.

    """

    def __init__(self, model,parent=None):
        super(VolumeIntensityDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()
        self._plot()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget,it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def _create_actions(self):
        self._model.time_changed.connect(self._plot)

    def _plot(self):
        ''' plot time time point curve.'''
        volume_data = self._model.data(self._model.currentIndex(),Qt.UserRole + 5)
        if self._model.data(self._model.currentIndex(),Qt.UserRole + 8):
            data = volume_data[:,:,:,self._model.get_current_time_point()]
            self.points = data[data!=0]
            # self.points = volume_data[volume_data[:,:,:,self._model.get_current_time_point()]!=0l,
            #                                     self._model.get_current_time_point()]
        else:
            self.points = volume_data[volume_data!=0]

        # create an axis
        ax = self.figure.add_subplot(111)
        ax.hold(False)
        ax.hist(self.points,50)
        plt.xlabel("Intensity")
        plt.ylabel("Number")
        plt.grid()
        self.canvas.draw()

    def closeEvent(self, QCloseEvent):
        self._model.time_changed.disconnect(self._plot)

