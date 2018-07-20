import numpy as np
from PyQt4 import QtCore, QtGui

from froi.algorithm.imtool import binarize


class ProbabilityMapDialog(QtGui.QDialog):

    def __init__(self, model, parent=None):
        super(ProbabilityMapDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        threshold_label = QtGui.QLabel('Threshold:')
        self._threshold_edit = QtGui.QLineEdit()
        output_label = QtGui.QLabel('OutputName:')
        self._output_edit = QtGui.QLineEdit()
        grid_layout = QtGui.QGridLayout()
        grid_layout.addWidget(threshold_label, 0, 0)
        grid_layout.addWidget(self._threshold_edit, 0, 1)
        grid_layout.addWidget(output_label, 1, 0)
        grid_layout.addWidget(self._output_edit, 1, 1)

        self._run_button = QtGui.QPushButton('Run')
        self._cancel_button = QtGui.QPushButton('Cancel')
        hbox_layout = QtGui.QHBoxLayout()
        hbox_layout.addWidget(self._run_button)
        hbox_layout.addWidget(self._cancel_button)

        vbox_layout = QtGui.QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)

    def _create_actions(self):
        self._run_button.clicked.connect(self._run)
        self._cancel_button.clicked.connect(self.done)

    def _run(self):
        raise NotImplementedError


class SurfProbMapDialog(ProbabilityMapDialog):

    def __init__(self, model, parent=None):
        super(SurfProbMapDialog, self).__init__(model, parent)
        self.index = self._model.current_index()
        depth = self._model.index_depth(self.index)
        if depth != 2:
            QtGui.QMessageBox.warning(self,
                                      'Warning!',
                                      'Get overlay failed!\nYou may have not selected any overlay!',
                                      QtGui.QMessageBox.Yes)
            # raise error to prevent dialog from being created
            raise RuntimeError("You may have not selected any overlay!")

        # fill threshold editor
        thr = self._model.data(self.index, QtCore.Qt.UserRole)
        self._threshold_edit.setText(str(thr))

        # fill output editor
        source_name = self._model.data(self.index, QtCore.Qt.DisplayRole)
        output_name = '_'.join(['prob', source_name])
        self._output_edit.setText(output_name)

    def _run(self):
        thr = self._threshold_edit.text()
        if not thr:
            self._threshold_edit.setFocus()
            return None
        else:
            try:
                thr = float(thr)
            except ValueError:
                self._threshold_edit.selectAll()
                return None

        name = str(self._output_edit.text())
        if not name:
            self._output_edit.setFocus()
            return None

        source_data = self._model.data(self.index, QtCore.Qt.UserRole + 5)
        bin_data = binarize(source_data, thr)
        prob_data = np.mean(bin_data, 1)
        self._model.add_item(self.index, source=prob_data, name=name, colormap='jet')

        self.done(0)
