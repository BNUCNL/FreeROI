# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class RegisterVolumeDialog(QDialog):
    """
    A dialog for adding a new label.

    """
    def __init__(self, model, parent=None):
        super(RegisterVolumeDialog, self).__init__(parent)

        self._model = model
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        input_volume = QLabel('Input Volume:')
        self.input_dir = QLineEdit('')
        self.input_dir.setReadOnly(True)
        self.input_button = QPushButton('Browse')

        reference_volume = QLabel('Reference Volume:')
        self.reference_dir = QLineEdit('')
        self.reference_dir.setReadOnly(True)
        self.reference_button = QPushButton('Browse')

        output_volume = QLabel('Output Volume:')
        self.output_dir = QLineEdit('')
        self.output_dir.setReadOnly(True)
        self.output_button = QPushButton('Browse')

        grid_layout = QGridLayout()
        grid_layout.addWidget(input_volume, 0, 0)
        grid_layout.addWidget(self.input_dir, 0, 1)
        grid_layout.addWidget(self.input_button, 0, 2)
        grid_layout.addWidget(reference_volume, 1, 0)
        grid_layout.addWidget(self.reference_dir, 1, 1)
        grid_layout.addWidget(self.reference_button, 1, 2)
        grid_layout.addWidget(output_volume, 2, 0)
        grid_layout.addWidget(self.output_dir, 2, 1)
        grid_layout.addWidget(self.output_button, 2, 2)

        self.register_button = QPushButton("Register")
        self.register_button.adjustSize()

        self.fsl_radio = QRadioButton('FSL',self)
        self.freesurfer_radio = QRadioButton('FreeSurfer',self)
        self.afni_radio = QRadioButton('AFNI',self)
        self.spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self.fsl_radio)
        radio_group.addButton(self.freesurfer_radio)
        radio_group.addButton(self.afni_radio)
        radio_group.addButton(self.spm_radio)
        self.fsl_radio.setChecked(True)

        radio_group_hlayout = QHBoxLayout()
        radio_group_hlayout.addWidget(self.fsl_radio)
        radio_group_hlayout.addWidget(self.freesurfer_radio)
        radio_group_hlayout.addWidget(self.afni_radio)
        radio_group_hlayout.addWidget(self.spm_radio)

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.register_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addLayout(radio_group_hlayout)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.input_button.clicked.connect(self._input_browse)
        self.reference_button.clicked.connect(self._reference_browse)
        self.output_button.clicked.connect(self._output_browse)

    def _input_browse(self):
        input_dir = str(QFileDialog.getExistingDirectory(self, "Select Input Volume Directory"))
        self.input_dir.setText(input_dir)

    def _reference_browse(self):
        reference_dir = str(QFileDialog.getExistingDirectory(self, "Select Reference Volume Directory"))
        self.reference_dir.setText(reference_dir)

    def _output_browse(self):
        file_path = temp_dir = str(QDir.currentPath())
        file_types = "Compressed NIFTI file(*.nii.gz);;NIFTI file(*.nii)"
        path,filter = QFileDialog.getSaveFileNameAndFilter(
            self,
            'Save image as...',
            file_path,
            file_types,)
        if not path.isEmpty():
            self.output_dir.setText(path)
        import sys
        import os
        if not path.isEmpty():
            if sys.platform == 'win32':
                path = unicode(path).encode('gb2312')
                self._temp_dir = os.path.dirname(unicode(path, 'gb2312'))
            else:
                path = str(path)
        print 'Save output file path: ', path

    def _register(self):
        if self.input_dir is '' or self.reference_dir is '':
            QMessageBox.warning('Input volume or reference volume directory is empty!')
            return






