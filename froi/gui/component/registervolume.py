# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import os
import re
import sys
import nibabel as nib

class RegisterVolumeDialog(QDialog):
    """
    A dialog for register volume.

    """
    def __init__(self, model, source_image_filename, parent=None):
        super(RegisterVolumeDialog, self).__init__(parent)

        self._model = model
        self._temp_dir = None
        self._source_image_filename = source_image_filename
        self._supplement_image_filename = ''

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        target_image_label = QLabel("Target Image :")
        self._target_image_combo = QComboBox()
        vol_list = self._model.getItemList()
        self._target_image_combo.addItems(QStringList(vol_list))

        source_image = QLabel('Source Image :')
        self._source_image_dir = QLineEdit('')
        self._source_image_dir.setEnabled(False)
        self._source_image_dir.setText(self._source_image_filename)

        self._supplement_image_check = QCheckBox('Supplement Image :')
        self._supplement_image_check.setChecked(False)
        self._supplement_image_dir = QLineEdit('')
        self._supplement_image_dir.setReadOnly(True)
        self._supplement_image_dir.setVisible(False)
        self._supplement_image_button = QPushButton('Browse')
        self._supplement_image_button.setVisible(False)

        grid_layout = QGridLayout()
        grid_layout.addWidget(target_image_label, 0, 0, 1, 1)
        grid_layout.addWidget(self._target_image_combo, 0, 1, 1, 2)
        grid_layout.addWidget(source_image, 1, 0, 1, 1)
        grid_layout.addWidget(self._source_image_dir, 1, 1, 1, 2)
        grid_layout.addWidget(self._supplement_image_check, 2, 0, 1, 1)
        grid_layout.addWidget(self._supplement_image_dir, 2, 1, 1, 1)
        grid_layout.addWidget(self._supplement_image_button, 2, 2, 1, 1)

        input_data_group = QGroupBox("Input Data: ")
        input_data_group.setLayout(grid_layout)

        self._fsl_radio = QRadioButton('FSL',self)
        self._spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self._fsl_radio)
        radio_group.addButton(self._spm_radio)
        self._fsl_radio.setChecked(True)

        radio_group_vlayout = QVBoxLayout()
        radio_group_vlayout.addWidget(self._fsl_radio)
        radio_group_vlayout.addWidget(self._spm_radio)

        tools_group = QGroupBox("Tools: ")
        tools_group.setLayout(radio_group_vlayout)

        self._register_button = QPushButton("Register")
        self._register_button.setFixedWidth(100)
        self._register_button.adjustSize()

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setFixedWidth(100)
        self._cancel_button.adjustSize()

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self._register_button)
        hbox_layout.addWidget(self._cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(input_data_group)
        vbox_layout.addWidget(tools_group)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)
        self.setMinimumSize(500, 300)

    def _create_actions(self):
        self._supplement_image_button.clicked.connect(self._supplement_image_browse)
        self._supplement_image_check.clicked.connect(self._supplement_image_checkable)
        self._register_button.clicked.connect(self._register)
        self._cancel_button.clicked.connect(self.done)

    def _supplement_image_browse(self):
        supplement_image_filepath = self._open_file_dialog("Add supplement image file.")
        if supplement_image_filepath is not None:
            self._temp_dir = os.path.dirname(supplement_image_filepath)
            self._supplement_image_dir.setText(supplement_image_filepath)
            self._supplement_image_filename = supplement_image_filepath

    def _supplement_image_checkable(self):
        if self._supplement_image_check.isChecked():
            self._supplement_image_dir.setVisible(True)
            self._supplement_image_button.setVisible(True)
        else:
            self._supplement_image_dir.setVisible(False)
            self._supplement_image_button.setVisible(False)

    def _open_file_dialog(self, title):
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_name = QFileDialog.getOpenFileName(self,
                                                title,
                                                temp_dir,
                                                "Nifti files (*.nii *.nii.gz)")
        import sys
        file_path = None
        if not file_name.isEmpty():
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
        return file_path

    def _register(self):
        target_image_index_row = self._target_image_combo.currentIndex()
        target_image_filename = self._generate_temp_image_file(target_image_index_row)

        if str(self._source_image_dir.text()) is '':
            QMessageBox.warning('The target image cannot be empty!')
            return

        if self._supplement_image_check.isChecked():
            temp_filename = self._source_image_filename
            self._source_image_filename = self._supplement_image_filename
            self._supplement_image_filename = temp_filename
        else:
            self._supplement_image_filename = ''

        if self._fsl_radio.isChecked():
            #fsl register
            rm = RegisterMethod(str(target_image_filename),
                                str(self._source_image_filename),
                                str(self._supplement_image_filename))
            res = rm.fsl_register()
            print 'fsl_register() => res: ', res
        else:
            #spm register
            rm = RegisterMethod(str(target_image_filename),
                                str(self._source_image_filename),
                                str(self._supplement_image_filename))
            res = rm.spm_register()
            print 'spm_register() => res: ', res

        #delete the temp file
        os.remove(target_image_filename)
        if res is not None:
            for filepath in res:
                basename = os.path.basename(filepath.strip('/'))
                filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', basename)
                new_vol = nib.load(filepath).get_data()
                self._model.addItem(new_vol,
                                    None,
                                    filename,
                                    self._model._data[0].get_header(),
                                    None, None, 255, 'red2yellow')
                # #delete the register file
                # os.remove(filepath)
        self.done(0)

    def _generate_temp_image_file(self, row):
        import os

        if not self._temp_dir:
            temp_dir = str(QDir.currentPath())
        else:
            temp_dir = self._temp_dir
        temp_file_path = os.path.join(temp_dir, 'temp_' + str(self._model.data(self._model.index(row), Qt.DisplayRole)) + '.nii')
        if sys.platform == 'win32':
            file_path = unicode(temp_file_path).encode('gb2312')
        else:
            file_path = str(temp_file_path)
        self._model._data[row].save2nifti(file_path)

        return temp_file_path


class RegisterMethod(object):
    def __init__(self, target_image_filename, source_image_filename, supplement_image_filename, parent=None):
        self._target_image_filename = target_image_filename
        self._source_image_filename = source_image_filename
        self._supplement_image_filename = supplement_image_filename

    #-------------------------------------------- fsl register ---------------------------------------
    def fsl_register(self):
        # Reference link
        # http://nipy.org/nipype/interfaces/generated/nipype.interfaces.fsl.preprocess.html
        # Use FSL FLIRT for coregistration.
        if self._target_image_filename is not '' and self._supplement_image_filename is not '':
            return self._fsl_register_supplement_image()
        elif self._source_image_filename is not '' and self._supplement_image_filename is '':
            return [self._fsl_register(self._target_image_filename, self._source_image_filename)[0]]
        else:
            print 'FSL register error as for the wrong input!'
            return None

    def _fsl_register(self, target_image, source_image, omat=None):
        from nipype.interfaces import fsl

        flirt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
        flirt.inputs.in_file = source_image
        flirt.inputs.reference = target_image
        flirt.inputs.output_type = "NIFTI"

        if omat is not None:
            flirt.inputs.in_matrix_file = omat
            flirt.inputs.apply_xfm = True

        res = flirt.run()

        return res.outputs.out_file, res.outputs.out_matrix_file

    def _fsl_register_supplement_image(self):
        #register mean function image to anatomy image
        # r_apply_to_source_filename , a_to_s_matrix = self._fsl_register(self._source_image_filename,
        #                                                             self._supplement_image_filename)

        r_source_image_filename , apply_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._source_image_filename)

        # apply_matrix = str(QDir.currentPath() + QDir.separator()) + 'apply_matrix.mat'
        # command = "convert_xfm " + " -omat " + apply_matrix + " -concat " + a_to_s_matrix + \
        #   " " + s_to_t_matrix
        #
        # import os
        # os.system(command)

        #register anamoty image to template image
        r_supplement_image_filename , result_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._supplement_image_filename,
                                                                    omat=apply_matrix)
        return r_source_image_filename, r_supplement_image_filename


    #-------------------------------------------- spm normalize ---------------------------------------
    def spm_register(self):
        if self._target_image_filename is not '' and self._supplement_image_filename is not '':
            return self._spm_normalize_supplement_image()
        elif self._source_image_filename is not '' and self._supplement_image_filename is '':
            return [self._spm_normalize(self._target_image_filename, self._source_image_filename)[0]]
        else:
            print 'SPM normalize error as for the wrong input!'
            return None

    def _spm_normalize(self, target_image, source_image, omat=None):
        '''SPM Normalize'''
        # Reference link
        # http://www.mit.edu/~satra/nipype-nightly/interfaces/generated/nipype.interfaces.spm.preprocess.html
        # http://nipy.org/nipype/users/examples/fmri_spm_dartel.html

        import nipype.interfaces.spm as spm
        norm = spm.Normalize()

        if omat is not None:
            norm.inputs.apply_to_files = source_image
            norm.inputs.jobtype = 'write'
            norm.inputs.parameter_file = omat
        else:
            norm.inputs.template = target_image
            norm.inputs.source = source_image

        #Should be auto calculated based on the given template image !!!!
        norm.inputs.write_bounding_box = self._compute_boundingbox()
        res = norm.run()

        if omat is None:
            return res.outputs.normalized_source, res.outputs.normalization_parameters
        else:
            return res.outputs.normalized_files, res.outputs.normalization_parameters

    def _spm_normalize_supplement_image(self):
        #register anamoty image to template image
        w_source_image_filename , out_parameters_matrix = self._spm_normalize(self._target_image_filename,
                                                                                self._source_image_filename)

        w_supplement_image_filename, out_matrix = self._spm_normalize(self._target_image_filename,
                                                                 self._supplement_image_filename,
                                                                 out_parameters_matrix)

        return w_source_image_filename, w_supplement_image_filename

    def _compute_boundingbox(self):
        #Compute the bounding_box parameter based on the target_image
        import nibabel as nib
        from nibabel.affines import apply_affine
        import numpy as np

        target_image = nib.load(self._target_image_filename)
        target_shape = target_image.get_shape()
        target_origin = apply_affine(np.linalg.inv(target_image.affine), [0, 0, 0])
        bounding_box = [[0-2 * target_origin[0], 0-2 * target_origin[1], 0-2 * target_origin[2]],
                        [2 * (target_shape[0] - 1 - target_origin[0]), 2 * (target_shape[1] - 1 - target_origin[1]),
                         2 * (target_shape[2] - 1 - target_origin[2])]]

        print 'bounding_box: ', bounding_box
        return bounding_box


