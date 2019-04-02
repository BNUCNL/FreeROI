# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..algorithm import imtool


class IntersectDialog(QDialog):
    """A dialog for action of intersection."""
    def __init__(self, model, parent=None, is_surf=False):
        super(IntersectDialog, self).__init__(parent)
        self._model = model

        self._init_gui(is_surf)
        self._create_actions()

    def _init_gui(self, is_surf):
        """Initialize GUI."""
        # set dialog title
        self.setWindowTitle("Intersect")

        # initialize widgets
        mask_label = QLabel("Mask")
        self.mask_combo = QComboBox()
        out_label = QLabel("Output name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(mask_label, 0, 0)
        grid_layout.addWidget(self.mask_combo, 0, 1)
        grid_layout.addWidget(out_label, 1, 0)
        grid_layout.addWidget(self.out_edit, 1, 1)
        if is_surf:
            mask_label_label = QLabel('Mask label')
            self.mask_label_edit = QLineEdit()
            self.mask_label_edit.setText('nonzero')
            substitution_label = QLabel('Substitution')
            self.substitution_edit = QLineEdit()
            self.substitution_edit.setText('0')
            grid_layout.addWidget(mask_label_label, 2, 0)
            grid_layout.addWidget(self.mask_label_edit, 2, 1)
            grid_layout.addWidget(substitution_label, 3, 0)
            grid_layout.addWidget(self.substitution_edit, 3, 1)

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
        self.mask_combo.currentIndexChanged.connect(self._create_output_name)
        self.run_button.clicked.connect(self._run_intersect)
        self.cancel_button.clicked.connect(self.done)

    def _create_output_name(self):
        raise NotImplementedError

    def _run_intersect(self):
        raise NotImplementedError


class VolIntersectDialog(IntersectDialog):

    def __init__(self, model, parent=None):
        super(VolIntersectDialog, self).__init__(model, parent)

        self._index = self._model.currentIndex()
        item_list = self._model.getItemList()
        # self.mask_combo.addItems(QStringList(item_list))
        self.mask_combo.addItems(item_list)

    def _create_output_name(self):
        src_name = self._model.data(self._index, Qt.DisplayRole)
        mask_name = self.mask_combo.currentText()
        out_name = '&'.join([src_name, mask_name])
        self.out_edit.setText(out_name)

    def _run_intersect(self):
        output_name = str(self.out_edit.text())
        if not output_name:
            QMessageBox.critical(self, "No output name",
                                 "Please specify output name!")
            return None

        mask_idx = self._model.index(self.mask_combo.currentIndex())
        src_data = self._model.data(self._index, Qt.UserRole + 4)
        mask_data = self._model.data(mask_idx, Qt.UserRole + 4)
        new_vol = imtool.intersect(src_data, mask_data)
        self._model.addItem(new_vol,
                            name=output_name,
                            header=self._model.data(self._index, Qt.UserRole + 11),
                            colormap=self._model.data(self._index, Qt.UserRole + 3)
                            )
        self.done(0)


class SurfIntersectDialog(IntersectDialog):

    def __init__(self, model, parent=None):
        super(SurfIntersectDialog, self).__init__(model, parent, True)

        self._index = self._model.current_index()
        depth = self._model.index_depth(self._index)
        if depth != 2:
            QMessageBox.warning(self,
                                'Warning!',
                                'Get overlay failed!\nYou may have not selected any overlay!',
                                QMessageBox.Yes)
            # raise error to prevent dialog from being created
            raise RuntimeError("You may have not selected any overlay!")
        item_list = self._model.get_overlay_list(self._index)
        self.mask_combo.addItems(item_list)

    def _create_output_name(self):
        src_name = self._model.data(self._index, Qt.DisplayRole)
        mask_name = self.mask_combo.currentText()
        out_name = '&'.join([src_name, mask_name])
        self.out_edit.setText(out_name)

    def _run_intersect(self):
        output_name = str(self.out_edit.text())
        if not output_name:
            self.out_edit.setFocus()
            return None

        mask_label = str(self.mask_label_edit.text())
        if not mask_label:
            self.mask_label_edit.setFocus()
            return None
        elif mask_label == 'nonzero':
            mask_label = None
        else:
            mask_label = float(mask_label)

        substitution = str(self.substitution_edit.text())
        if not substitution:
            self.substitution_edit.setFocus()
            return None
        elif substitution != 'min' and substitution != 'max':
            substitution = float(substitution)

        mask_idx = self._model.index(self.mask_combo.currentIndex(), 0,
                                     self._model.get_surface_index(self._index))
        src_data = self._model.data(self._index, Qt.UserRole + 10)
        mask_data = self._model.data(mask_idx, Qt.UserRole + 10)
        new_data = imtool.intersect2(src_data, mask_data, mask_label, substitution)
        self._model.add_item(self._index,
                            source=new_data,
                            name=output_name,
                            colormap=self._model.data(self._index, Qt.UserRole + 3))
        self.done(0)
