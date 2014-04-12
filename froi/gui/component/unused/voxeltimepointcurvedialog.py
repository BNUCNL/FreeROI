__author__ = 'zhouguangfu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.ticker import MultipleLocator


class VoxelTimePointCurveDialog(QDialog):
    """
    A dialog for action of voxel time point curve display.

    """

    def __init__(self, model, is_voxel=True, mask_row=None,parent=None):
        super(VoxelTimePointCurveDialog, self).__init__(parent)
        self._model = model
        self._is_voxel = is_voxel
        self._mask_row = mask_row

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

        self.meanlabel = QLabel("Mean:")
        self.varlabel = QLabel("Variance:")
        self.save_data = QPushButton("Save Data")

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.meanlabel)
        hlayout.addWidget(self.varlabel)
        hlayout.addWidget(self.save_data)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def _create_actions(self):
        ''' create actions.'''
        self._model.cross_pos_changed.connect(self._plot)
        self.save_data.clicked.connect(self._save_data)

    def _save_data(self):
        """
        Save points data to a txt file.

        """
        index = self._model.currentIndex()
        temp_dir = str(QDir.currentPath())
        filename = QFileDialog.getSaveFileName(
            self,
            'Save data as...',
            temp_dir,
            'Txt files (*.txt,*.csv)')
        if not filename.isEmpty():
            np.savetxt(str(filename), self.points, fmt="%f", delimiter="\n")
        else:
            print "Path is empty!"

    def _plot(self):
        ''' plot time time point curve.'''
        xyz = self._model.get_cross_pos()
        if self._is_voxel:
            self.points = self._model.get_current_value([xyz[1], xyz[0], xyz[2]],time_course=True)
            if not self._model.data(self._model.currentIndex(),Qt.UserRole + 8):
                self.points = np.array((self.points,))
        else:
            volume_data = self._model.data(self._model.currentIndex(),Qt.UserRole + 5)
            mask_data = self._model.data(self._model.index(self._mask_row),Qt.UserRole + 5)

            if self._model.data(self._model.currentIndex(),Qt.UserRole + 8):
                self.points = volume_data[mask_data == self._model.get_row_value(
                    [xyz[1], xyz[0], xyz[2]],self._mask_row)].mean(axis=0)
            else:
                self.points = volume_data[mask_data == self._model.get_row_value(
                    [xyz[1], xyz[0], xyz[2]],self._mask_row)].mean()
                self.points = np.array((self.points,))

        self.meanlabel.setText("Mean:"+str(self.points.mean()))
        self.varlabel.setText("Variance:"+str(self.points.var()))
        # create an axis
        ax = self.figure.add_subplot(111)
        ax.hold(False)
        ax.plot(self.points, '*-')
        ax.xaxis.set_major_locator(MultipleLocator(2))
        plt.xlabel("Time Point")
        if(isinstance(self.points,np.ndarray)):
            plt.xlim(0,self.points.shape[0])
        else:
            plt.xlim(0,1)
        plt.ylabel("Intensity")
        plt.grid()
        self.canvas.draw()

    def closeEvent(self, QCloseEvent):
        self._model.cross_pos_changed.disconnect(self._plot)
