
__author__ = 'zhouguangfu'
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from scipy.ndimage import morphology

class GreyerosionDialog(QDialog):
    """
    A dialog for action of greyerosion.

    """
    def __init__(self, model, parent=None):
        super(GreyerosionDialog, self).__init__(parent)
        self._model = model

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Greyerosion")

        # initialize widgets
        source_label = QLabel("Source")
        self.source_combo = QComboBox()

        vol_list = self._model.getItemList()
        self.source_combo.addItems(vol_list)
        row = self._model.currentIndex().row()
        self.source_combo.setCurrentIndex(row)


        size_label = QLabel("Size")
        self.size_combo = QComboBox()
        self.size_combo.addItem("3x3")
        self.size_combo.addItem("5x5")
        self.size_combo.addItem("7x7")
        self.size_combo.addItem("9x9")
        mode_label = QLabel("mode")
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("reflect")
        self.mode_combo.addItem("constant")
        self.mode_combo.addItem("nearest")
        self.mode_combo.addItem("mirror")
        self.mode_combo.addItem("wrap")
        cval_label = QLabel("Cval")
        self.cval_edit = QLineEdit()
        self.cval_edit.setText('0')
        self.cval_edit.setEnabled(False)

        out_label = QLabel("Output volume name")
        self.out_edit = QLineEdit()
        

        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(size_label, 0, 0)
        grid_layout.addWidget(self.size_combo, 0, 1)
        grid_layout.addWidget(mode_label, 1, 0)
        grid_layout.addWidget(self.mode_combo, 1, 1)
        grid_layout.addWidget(cval_label, 2, 0)
        grid_layout.addWidget(self.cval_edit, 2, 1)
        grid_layout.addWidget(out_label, 3, 0)
        grid_layout.addWidget(self.out_edit, 3, 1)

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
        self.run_button.clicked.connect(self._grey_erosion)
        self.cancel_button.clicked.connect(self.done)
        self.mode_combo.currentIndexChanged.connect(self._mode_cval_change)

    def _create_output(self):
        source_name = self.source_combo.currentText()
        output_name = '_'.join([str(source_name), 'greyerosion'])
        self.out_edit.setText(output_name)

    def _grey_erosion(self):
        vol_name = str(self.out_edit.text())
        num = self.size_combo.currentIndex() + 3
        size = (num, num, num)
        mode = self.mode_combo.currentText()
        cval = self.cval_edit.text()


        if not vol_name:
            self.out_edit.setFocus()
            return

        try:
            cval = int(cval)
        except ValueError:
            self.cval_edit.selectAll()
            return

        if cval>255 or cval<0:
            print "cval must be 0-255!"
            return

        source_row = self.source_combo.currentIndex()
        source_data = self._model.data(self._model.index(source_row),
                                       Qt.UserRole + 5)

        new_vol = morphology.grey_erosion(source_data,size=size,mode=mode,cval=cval)
        self._model.addItem(new_vol,
                            None,
                            vol_name,
                            self._model._data[0].get_header())
        self.done(0)
        
    def _mode_cval_change(self):
        if self.mode_combo.currentText() == "constant":
            self.cval_edit.setEnabled(True)
        else:
            self.cval_edit.setEnabled(False)
