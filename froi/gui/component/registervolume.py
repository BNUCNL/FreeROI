# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import re
import sys
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import nibabel as nib
import numpy as np


class RegisterVolumeDialog(QDialog):
    """A dialog for register volume."""
    def __init__(self, model, source_image_filename, parent=None):
        super(RegisterVolumeDialog, self).__init__(parent)

        self._model = model
        self._temp_dir = os.path.dirname(source_image_filename)
        self._source_image_filename = source_image_filename
        self._auxiliary_image_filename = ''
        self._delta = 0.01

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        target_image_label = QLabel("Target Image :")
        self._target_image_combo = QComboBox()
        vol_list = self._model.getItemList()
        self._target_image_combo.addItems(QStringList(vol_list))

        source_image = QLabel('Source Image :')
        self._source_image_dir = QLabel('')
        self._source_image_dir.setText(os.path.basename(self._source_image_filename.strip('/')))

        self._auxiliary_image_check = QCheckBox('Auxiliary Image :')
        self._auxiliary_image_check.setChecked(False)
        self._auxiliary_image_dir = QLineEdit('')
        self._auxiliary_image_dir.setReadOnly(True)
        self._auxiliary_image_dir.setVisible(False)
        self._auxiliary_image_button = QPushButton('Browse')
        self._auxiliary_image_button.setVisible(False)

        grid_layout = QGridLayout()
        grid_layout.addWidget(target_image_label, 0, 0, 1, 1)
        grid_layout.addWidget(self._target_image_combo, 0, 1, 1, 2)
        grid_layout.addWidget(source_image, 1, 0, 1, 1)
        grid_layout.addWidget(self._source_image_dir, 1, 1, 1, 2)
        grid_layout.addWidget(self._auxiliary_image_check, 2, 0, 1, 1)
        grid_layout.addWidget(self._auxiliary_image_dir, 2, 1, 1, 1)
        grid_layout.addWidget(self._auxiliary_image_button, 2, 2, 1, 1)

        input_data_group = QGroupBox("Input Data: ")
        input_data_group.setLayout(grid_layout)

        self._fsl_radio = QRadioButton('FSL',self)
        self._spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self._fsl_radio)
        radio_group.addButton(self._spm_radio)
        if sys.platform == 'win32':
            self._fsl_radio.setChecked(False)
            self._fsl_radio.setEnabled(False)
            self._spm_radio.setChecked(True)
        else:
            self._fsl_radio.setChecked(True)

        self._nearest_neighbour_cb = QCheckBox('Interpolation: Nearest Neighbour')

        radio_group_vlayout = QVBoxLayout()
        radio_group_vlayout.addWidget(self._fsl_radio)
        radio_group_vlayout.addWidget(self._spm_radio)
        radio_group_vlayout.addWidget(self._nearest_neighbour_cb)

        tools_group = QGroupBox("Tools: ")
        tools_group.setLayout(radio_group_vlayout)

        self._register_button = QPushButton("Register")
        self._register_button.setFixedWidth(120)
        self._register_button.adjustSize()

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setFixedWidth(120)
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

        self._progress_dialog = QProgressDialog(self)
        self._progress_dialog.setMinimumWidth(500)
        self._progress_dialog.setRange(0, 100)
        self._progress_dialog.setWindowTitle('Registering')

        self._progress_value = 0.0
        self._update_timer = QTimer(self)
        self.connect(self._update_timer, SIGNAL("timeout()"), self._update_progress)


    def _create_actions(self):
        self._auxiliary_image_button.clicked.connect(self._auxiliary_image_browse)
        self._auxiliary_image_check.clicked.connect(self._auxiliary_image_checkable)
        self._register_button.clicked.connect(self._register)
        self._cancel_button.clicked.connect(self._regester_canceled)
        self.destroyed.connect(self._regester_canceled)
        self._progress_dialog.destroyed.connect(self._regester_canceled)
        self._progress_dialog.canceled.connect(self._regester_canceled)

    def _auxiliary_image_browse(self):
        auxiliary_image_filepath = self._open_file_dialog("Add auxiliary image file.")
        if auxiliary_image_filepath is not None:
            self._temp_dir = os.path.dirname(auxiliary_image_filepath)
            self._auxiliary_image_dir.setText(os.path.basename(auxiliary_image_filepath.strip('/')))
            self._auxiliary_image_filename = auxiliary_image_filepath

    def _auxiliary_image_checkable(self):
        if self._auxiliary_image_check.isChecked():
            self._auxiliary_image_dir.setVisible(True)
            self._auxiliary_image_button.setVisible(True)
        else:
            self._auxiliary_image_dir.setVisible(False)
            self._auxiliary_image_button.setVisible(False)

    def _open_file_dialog(self, title):
        file_name = QFileDialog.getOpenFileName(self,
                                                title,
                                                self._temp_dir,
                                                "Nifti files (*.nii *.nii.gz)")
        import sys
        file_path = None
        if not file_name.isEmpty():
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
        return file_path

    def _update_progress(self, error_info=None):
        value = (2. / (1 + math.exp(-self._progress_value)) - 1.01) * 100
        self._progress_dialog.setValue(value)
        self._progress_value += self._delta

    def _regester_finished(self, error_info=None):
        self._progress_dialog.setValue(100)
        self._progress_dialog.close()
        self._progress_value = 0
        self._update_timer.stop()

        if error_info is not None:
            QMessageBox.warning(self,
                                'Warning',
                                error_info,
                                QMessageBox.Yes)
            self._progress_dialog.done(0)
        else:
            res = self._register_thread.get_output()
            if res is not None:
                for filepath in res:
                    basename = os.path.basename(filepath.strip('/'))
                    filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', basename)
                    new_vol = nib.load(filepath).get_data()
                    if new_vol.shape != self._model._data[0].get_data_shape():
                        QMessageBox.warning(self,
                                            'Warning',
                                            'This error may be caused by SPM for the wrong calculated boundbingbox, '
                                            'you can use FSL instead.',
                                            QMessageBox.Yes)
                        break

                    self._model.addItem(new_vol,
                                        None,
                                        filename,
                                        self._model._data[0].get_header(),
                                        None, None, 255, 'red2yellow')
                    # #delete the register file
                    # os.remove(filepath)
        #delete the temp file
        os.remove(self._target_image_filename)
        self.done(0)

    def _regester_canceled(self):
        self._progress_dialog.close()
        self._progress_value = 0
        if self._update_timer.isActive():
            self._update_timer.stop()
        self.done(0)


    def _register(self):
        if str(self._source_image_dir.text()) is '':
            QMessageBox.warning(self,
                                'Warning',
                                'The target image cannot be empty!',
                                QMessageBox.Yes)
            return

        if not os.access(os.path.dirname(self._temp_dir), os.W_OK):
            QMessageBox.warning(self,
                                'Warning',
                                'The current directory is not writeable. Please copy the opened file to other directory which can be writeable.',
                                QMessageBox.Yes)
            self.done(0)
            return

        target_image_index_row = self._target_image_combo.currentIndex()
        self._target_image_filename = str(self._generate_temp_image_file(target_image_index_row))
        self._register_button.setEnabled(False)

        if self._auxiliary_image_check.isChecked() and self._auxiliary_image_filename is not '':
            if not str(self._auxiliary_image_filename).endswith('.nii'):
                QMessageBox.warning(self,
                                    'Warning',
                                    'The auxiliary image should be ended with .nii, not .nii.gz or anything else.',
                                    QMessageBox.Yes)
                self._register_button.setEnabled(True)
                return
            self._delta = 0.01
            temp_filename = self._source_image_filename
            self._source_image_filename = self._auxiliary_image_filename
            self._auxiliary_image_filename = temp_filename
        else:
            self._auxiliary_image_filename = ''
            self._delta = 0.03

        self._update_timer.start(500)

        self._register_thread = RegisterThread([self._target_image_filename,
                                               str(self._source_image_filename),
                                               str(self._auxiliary_image_filename),
                                               self._nearest_neighbour_cb.isChecked(),
                                               self._fsl_radio.isChecked()])
        self.connect(self._register_thread, SIGNAL("register"), self._regester_finished)
        self._register_thread.start()
        self.hide()
        self._progress_dialog.exec_()


    def _generate_temp_image_file(self, row):
        import os
        temp_file_path = os.path.join(self._temp_dir, 'temp_' + str(self._model.data(self._model.index(row), Qt.DisplayRole)) + '.nii')
        if sys.platform == 'win32':
            file_path = unicode(temp_file_path).encode('gb2312')
        else:
            file_path = str(temp_file_path)
        self._model._data[row].save2nifti(file_path)

        return temp_file_path

class RegisterThread(QThread):
    def __init__(self, subreddits):
        QThread.__init__(self)
        self._subreddits = subreddits

        self._target_image_filename = subreddits[0]
        self._source_image_filename = subreddits[1]
        self._auxiliary_image_filename = subreddits[2]
        self._interpolation_method = subreddits[3]
        self._is_fsl = subreddits[4]
        self._output = None

    def __del__(self):
        self.wait()

    def run(self):
        rm = RegisterMethod(self._target_image_filename,
                            self._source_image_filename,
                            self._auxiliary_image_filename,
                            self._interpolation_method)
        res = None
        try:
            if self._is_fsl:
                #fsl register
                res = rm.fsl_register()
            else:
                #detect if the chose file is ended with '.nii', because spm cannot process the .nii.gz file.
                if not str(self._source_image_filename).endswith('.nii'):
                    rm.set_error_info("The source image should be ended with .nii, not .nii.gz or anything else.")
                else:
                    #spm register
                    res = rm.spm_register()
        except:
            # 'Register error occur!'
            rm.set_error_info("Unknown error!")

        self._output = res
        self.emit(SIGNAL('register'), rm.get_error_info())

    def get_output(self):
        return self._output


class RegisterMethod(object):
    def __init__(self,
                 target_image_filename,
                 source_image_filename,
                 auxiliary_image_filename,
                 interpolation_method,
                 parent=None):
        self._target_image_filename = target_image_filename
        self._source_image_filename = source_image_filename
        self._auxiliary_image_filename = auxiliary_image_filename
        self._interpolation_method = interpolation_method
        self._error_info = None

    #-------------------------------------------- fsl register ---------------------------------------
    def fsl_register(self):
        # Reference link
        # http://nipy.org/nipype/interfaces/generated/nipype.interfaces.fsl.preprocess.html
        # Use FSL FLIRT for coregistration.
        if self._target_image_filename is not '' and self._auxiliary_image_filename is not '':
            return self._fsl_register_auxiliary_image()
        elif self._source_image_filename is not '' and self._auxiliary_image_filename is '':
            return [self._fsl_register(self._target_image_filename, self._source_image_filename)[0]]
        else:
            self.set_error_info('FSL register error as for the wrong input!')
            return None

    def _fsl_register(self, target_image, source_image, omat=None):
        from nipype.interfaces import fsl

        flirt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
        flirt.inputs.in_file = source_image
        flirt.inputs.reference = target_image
        flirt.inputs.output_type = "NIFTI"

        output_basename = os.path.basename(source_image.strip('/'))
        output_filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', output_basename)
        output_filename_path = os.path.join(os.path.dirname(source_image), output_filename + '_flirt.nii')
        out_matrix_filename_path = os.path.join(os.path.dirname(source_image), output_filename + '_flirt.mat')

        if sys.platform == 'win32':
            output_filename_path = unicode(output_filename_path).encode('gb2312')
            out_matrix_filename_path = unicode(out_matrix_filename_path).encode('gb2312')
        else:
            output_filename_path = str(output_filename_path)
            out_matrix_filename_path = str(out_matrix_filename_path)
        flirt.inputs.out_file = output_filename_path
        flirt.inputs.out_matrix_file = out_matrix_filename_path
        if self._interpolation_method:
            flirt.inputs.interp = 'nearestneighbour'

        if omat is not None:
            flirt.inputs.in_matrix_file = omat
            flirt.inputs.apply_xfm = True
        try:
            res = flirt.run()
        except:
            self.set_error_info('FSL error occured! Make sure the fsl path is in the environment variable ' + \
                                'or the parameter is correct.')
            return
        return res.outputs.out_file, res.outputs.out_matrix_file

    def _fsl_register_auxiliary_image(self):
        #register mean function image to anatomy image
        r_source_image_filename , apply_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._source_image_filename)

        apply_matrix = None
        #register anamoty image to template image
        r_auxiliary_image_filename , result_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._auxiliary_image_filename,
                                                                    omat=apply_matrix)
        return r_source_image_filename, r_auxiliary_image_filename


    #-------------------------------------------- spm normalize ---------------------------------------
    def spm_register(self):
        #detect whether the matlab is exsited.
        import nipype.interfaces.matlab as mlab      # how to run matlab
        try:
            mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")
            mlab.MatlabCommand.run()
        except:
            self.set_error_info('Cannot find the matlab! Make sure the matlab path has been added to the system ' + \
                                'environment path.')
            return 
        
        if self._target_image_filename is not '' and self._auxiliary_image_filename is not '':
            return self._spm_normalize_auxiliary_image()
        elif self._source_image_filename is not '' and self._auxiliary_image_filename is '':
            return [self._spm_normalize(self._target_image_filename, self._source_image_filename)[0]]
        else:
            self.set_error_info('SPM normalize error as for the wrong input!')
            return None

    def _spm_normalize(self, target_image, source_image, omat=None):
        """SPM Normalize"""
        # Reference link
        # http://www.mit.edu/~satra/nipype-nightly/interfaces/generated/nipype.interfaces.spm.preprocess.html
        # http://nipy.org/nipype/users/examples/fmri_spm_dartel.html

        import nipype.interfaces.spm as spm
        norm = spm.Normalize()
        zooms = nib.load(target_image).get_header().get_zooms()
        voxel_sizes = [float(zooms[0]), float(zooms[1]), float(zooms[2])]
        norm.inputs.write_voxel_sizes = voxel_sizes
        if omat is not None:
            norm.inputs.apply_to_files = source_image
            norm.inputs.jobtype = 'write'
            norm.inputs.parameter_file = omat
        else:
            norm.inputs.template = target_image
            norm.inputs.source = source_image

        #Should be auto calculated based on the given template image !!!!
        norm.inputs.write_bounding_box = self._compute_boundingbox()
        if self._interpolation_method:
            norm.inputs.write_interp = 0
        try:
            res = norm.run()
        except:
            self.set_error_info('Spm error occured! Make sure the spm path has been added to the matlab path ' + \
                                'or the parameter is correct.')
            return 

        if omat is None:
            self._spm_nan_to_number(res.outputs.normalized_source)
            return res.outputs.normalized_source, res.outputs.normalization_parameters
        else:
            self._spm_nan_to_number(res.outputs.normalized_files)
            return res.outputs.normalized_files, res.outputs.normalization_parameters

    def _spm_normalize_auxiliary_image(self):
        #register anamoty image to template image
        w_source_image_filename , out_parameters_matrix = self._spm_normalize(self._target_image_filename,
                                                                              self._source_image_filename)

        w_auxiliary_image_filename, out_matrix = self._spm_normalize(self._target_image_filename,
                                                                      self._auxiliary_image_filename,
                                                                      out_parameters_matrix)
        return w_source_image_filename, w_auxiliary_image_filename

    def _spm_nan_to_number(self, filename):
        nan_img = nib.load(filename)
        nan_data = nan_img.get_data()
        nan_affine = nan_img.get_affine()
        nan_data = np.nan_to_num(nan_data)

        nib.save(nib.Nifti1Image(nan_data, nan_affine), filename)

    def _compute_boundingbox(self):
        #Compute the bounding_box parameter based on the target_image
        target_image = nib.load(self._target_image_filename)
        bounds = self._get_bounds(target_image.shape, target_image.get_affine())

        bounding_box = [[i[0] for i in bounds], [j[1] for j in bounds]]

        return bounding_box

    def _get_bounds(self, shape, affine):
        """ Return the world-space bounds occupied by an array given an affine.
        """
        adim, bdim, cdim = shape
        adim -= 1
        bdim -= 1
        cdim -= 1
        # form a collection of vectors for each 8 corners of the box
        box = np.array([[0.,   0,    0,    1],
                        [adim, 0,    0,    1],
                        [0,    bdim, 0,    1],
                        [0,    0,    cdim, 1],
                        [adim, bdim, 0,    1],
                        [adim, 0,    cdim, 1],
                        [0,    bdim, cdim, 1],
                        [adim, bdim, cdim, 1] ]).T
        box = np.dot(affine, box)[:3]
        bounding_box = list(zip(box.min(axis=-1), box.max(axis=-1)))

        return bounding_box

    def set_error_info(self, error_info):
        self._error_info = error_info

    def get_error_info(self):
        return self._error_info

