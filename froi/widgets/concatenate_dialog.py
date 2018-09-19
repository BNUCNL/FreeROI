import numpy as np

from PyQt4 import QtGui, QtCore


class ConcatenateDialog(QtGui.QDialog):

    def __init__(self, model, parent=None):
        super(ConcatenateDialog, self).__init__(parent)
        self._model = model
        self._layer_names = []
        self._name_editable = True

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        from_label = QtGui.QLabel('From')
        self._from_combo = QtGui.QComboBox()
        to_label = QtGui.QLabel('To')
        self._to_combo = QtGui.QComboBox()
        self._update_layers()
        from_to_layout = QtGui.QGridLayout()
        from_to_layout.addWidget(from_label, 0, 0)
        from_to_layout.addWidget(self._from_combo, 0, 1)
        from_to_layout.addWidget(to_label, 1, 0)
        from_to_layout.addWidget(self._to_combo, 1, 1)

        self._candidate_list = QtGui.QListWidget()
        self._update_list()

        out_label = QtGui.QLabel('Output layer')
        self._out_edit = QtGui.QLineEdit()
        self._out_edit.setText('conc_' + self._candidate_list.item(0).text())
        out_layout = QtGui.QHBoxLayout()
        out_layout.addWidget(out_label)
        out_layout.addWidget(self._out_edit)

        self._ok_button = QtGui.QPushButton('OK')
        self._cancel_button = QtGui.QPushButton('Cancel')
        ok_cancel_layout = QtGui.QHBoxLayout()
        ok_cancel_layout.addWidget(self._ok_button)
        ok_cancel_layout.addWidget(self._cancel_button)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(from_to_layout)
        layout.addWidget(self._candidate_list)
        layout.addLayout(out_layout)
        layout.addLayout(ok_cancel_layout)
        self.setLayout(layout)

    def _create_actions(self):
        self._from_combo.currentIndexChanged.connect(self._update_list)
        self._to_combo.currentIndexChanged.connect(self._update_list)
        self._candidate_list.currentRowChanged.connect(self._update_outname)
        self._ok_button.clicked.connect(self._concatenate)
        self._cancel_button.clicked.connect(self.done)

    def _update_layers(self):
        raise NotImplementedError

    def _update_list(self):
        # get candidate list
        from_idx = self._from_combo.currentIndex()
        to_idx = self._to_combo.currentIndex()
        count = len(self._layer_names)
        if from_idx <= to_idx:
            candidate_list = self._layer_names[from_idx:to_idx+1]
        else:
            candidate_list = self._layer_names[from_idx-count:to_idx-count-1:-1]

        # update candidate list widget
        self._name_editable = False
        self._candidate_list.clear()
        self._candidate_list.addItems(candidate_list)
        self._name_editable = True

    def _update_outname(self):
        if self._name_editable:
            self._out_edit.setText('conc_' + self._candidate_list.currentItem().text())

    def _concatenate(self):
        raise NotImplementedError


class SurfConcatenateDialog(ConcatenateDialog):

    def __init__(self, model, parent=None):
        super(SurfConcatenateDialog, self).__init__(model, parent)

    def _create_actions(self):
        super(SurfConcatenateDialog, self)._create_actions()
        self._model.rowsMoved.connect(self._update_layers)
        self._model.rowsInserted.connect(self._update_layers)
        self._model.rowsRemoved.connect(self._update_layers)
        self._model.dataChanged.connect(self._update_layers)
        self.connect(self._model, QtCore.SIGNAL("currentIndexChanged"), self._update_layers)

    def _update_layers(self):
        self._layer_names = self._model.get_overlay_list()

        self._from_combo.clear()
        self._from_combo.addItems(self._layer_names)
        self._from_combo.setCurrentIndex(0)
        self._to_combo.clear()
        self._to_combo.addItems(self._layer_names)
        self._to_combo.setCurrentIndex(len(self._layer_names)-1)

    def _concatenate(self):
        name = str(self._out_edit.text())
        if not name:
            self._out_edit.setFocus()
            return

        # get candidate layers
        index = self._model.get_surface_index()
        surface = index.internalPointer()
        from_idx = self._from_combo.currentIndex()
        to_idx = self._to_combo.currentIndex()
        count = len(surface.overlays)
        if from_idx <= to_idx:
            candidate_layers = surface.overlays[-from_idx-1:-to_idx-2:-1]
        else:
            candidate_layers = surface.overlays[count-from_idx-1:count-to_idx]

        # concatenate layers to a new layer
        data = candidate_layers[0].get_data()
        for layer in candidate_layers[1:]:
            data = np.c_[data, layer.get_data()]
        colormap = candidate_layers[0].get_colormap()
        is_labels = [layer.is_label() for layer in candidate_layers]
        self._model.add_item(index,
                             source=data,
                             colormap=colormap,
                             islabel=np.all(is_labels),
                             name=name)

        self.done(0)
