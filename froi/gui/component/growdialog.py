# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import regiongrow as rg

class GrowDialog(QDialog):
    """
    A dialog for action of intersection.

    """
    def __init__(self, model, main_win, parent=None):
        super(GrowDialog, self).__init__(parent)
        self._model = model
        self._main_win = main_win
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Region Growing")

        # initialize widgets
        #source_label = QLabel("Source")
        self.source_combo = QComboBox()
        pointx_label = QLabel("Seed point x")
        self.pointx_edit = QLineEdit()
        self.pointx_edit.setText('45')
        pointy_label = QLabel("Seed point y")
        self.pointy_edit = QLineEdit()
        self.pointy_edit.setText('60')
        pointz_label = QLabel("Seed point z")
        self.pointz_edit = QLineEdit()
        self.pointz_edit.setText('45')


        number_label = QLabel("Number of voxels")
        self.number_edit = QLineEdit()
        self.number_edit.setText('100')

        vol_list = self._model.getItemList()
        self.source_combo.addItems(vol_list)
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)
        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(pointx_label, 0, 0)
        grid_layout.addWidget(self.pointx_edit, 0, 1)
        grid_layout.addWidget(pointy_label, 1, 0)
        grid_layout.addWidget(self.pointy_edit, 1, 1)
        grid_layout.addWidget(pointz_label, 2, 0)
        grid_layout.addWidget(self.pointz_edit, 2, 1)

        grid_layout.addWidget(number_label, 3, 0)
        grid_layout.addWidget(self.number_edit, 3, 1)

        grid_layout.addWidget(out_label, 4, 0)
        grid_layout.addWidget(self.out_edit, 4, 1)

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
        self._create_output()

    def _create_actions(self):
        self.source_combo.currentIndexChanged.connect(self._create_output)
        self.run_button.clicked.connect(self._grow)
        self.cancel_button.clicked.connect(self.done)

    def _create_output(self):
        source_name = self.source_combo.currentText()
        output_name = '_'.join([str(source_name), 'grow'])
        self.out_edit.setText(output_name)

    def _grow(self):
        vol_name = str(self.out_edit.text())
        pointx = self.pointx_edit.text()
        pointy = self.pointy_edit.text()
        pointz = self.pointz_edit.text()
        number = self.number_edit.text()

        if not vol_name:
            self.out_edit.setFocus()
            return
        if not pointx:
            self.pointx_edit.setFocus()
            return
        if not pointy:
            self.pointy_edit.setFocus()
            return
        if not pointz:
            self.pointz_edit.setFocus()
            return
        if not number:
            self.number_edit.setFocus()
            return

        try:
            pointx=int(pointx)
            pointy=108-int(pointy)
            pointz=int(pointz)
            number=int(number)
        except ValueError:
            self.number_edit.selectAll()
            return

        source_row = self.source_combo.currentIndex()
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 5)
        new_vol =rg.region_growing(source_data, (pointx,pointy,pointz),number)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header(),
                            None, None, 255, 'red')

        #self._main_win.new_image_action()
        self.done(0)

