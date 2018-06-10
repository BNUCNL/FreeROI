__author__ = 'zhouguangfu, chenxiayu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..algorithm import imtool


class BinarizationDialog(QDialog):
    """A dialog for action of binarization."""
    def __init__(self, model, parent=None):
        super(BinarizationDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("Binarization")

        # initialize widgets
        threshold_label = QLabel("Threshold")
        self.threshold_edit = QLineEdit()
        out_label = QLabel("Output name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(threshold_label, 0, 0)
        grid_layout.addWidget(self.threshold_edit, 0, 1)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.out_edit, 1, 1)

        # button config
        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.run_button.clicked.connect(self._binarize)
        self.cancel_button.clicked.connect(self.done)

    def _binarize(self):
        raise NotImplementedError


class VolBinarizationDialog(BinarizationDialog):

    def __init__(self, model, parent=None):
        super(VolBinarizationDialog, self).__init__(model, parent)

        self.index = self._model.currentIndex()

        # fill output editor
        source_name = self._model.data(self.index, Qt.DisplayRole)
        output_name = '_'.join(['bin', source_name])
        self.out_edit.setText(output_name)

        # fill threshold editor
        threshold = self._model.data(self.index, Qt.UserRole)
        self.threshold_edit.setText(str(threshold))

    def _binarize(self):
        out_name = str(self.out_edit.text())
        threshold = self.threshold_edit.text()

        if not out_name:
            self.out_edit.setFocus()
            return None
        if not threshold:
            self.threshold_edit.setFocus()
            return None

        try:
            threshold = float(threshold)
        except ValueError:
            self.threshold_edit.selectAll()
            return None

        source_data = self._model.data(self.index, Qt.UserRole + 6)
        new_vol = imtool.binarize(source_data, threshold)
        self._model.addItem(new_vol,
                            name=out_name,
                            header=self._model.data(self.index, Qt.UserRole + 11))
        self.done(0)


class SurfBinarizationDialog(BinarizationDialog):

    def __init__(self, model, parent=None):
        super(SurfBinarizationDialog, self).__init__(model, parent)

        self.index = self._model.current_index()
        depth = self._model.index_depth(self.index)
        if depth != 2:
            QMessageBox.warning(self,
                                'Warning!',
                                'Get overlay failed!\nYou may have not selected any overlay!',
                                QMessageBox.Yes)
            # raise error to prevent dialog from being created
            raise RuntimeError("You may have not selected any overlay!")

        # fill output editor
        source_name = self._model.data(self.index, Qt.DisplayRole)
        output_name = '_'.join(['bin', source_name])
        self.out_edit.setText(output_name)

        # fill threshold editor
        threshold = self._model.data(self.index, Qt.UserRole)
        self.threshold_edit.setText(str(threshold))

    def _binarize(self):
        out_name = str(self.out_edit.text())
        threshold = self.threshold_edit.text()

        if not out_name:
            self.out_edit.setFocus()
            return None
        if not threshold:
            self.threshold_edit.setFocus()
            return None

        try:
            threshold = float(threshold)
        except ValueError:
            self.threshold_edit.selectAll()
            return None

        source_data = self._model.data(self.index, Qt.UserRole + 5)
        new_data = imtool.binarize(source_data, threshold)
        self._model.add_item(self.index,
                             source=new_data,
                             name=out_name,
                             islabel=True,
                             colormap="blue")
        self.done(0)
