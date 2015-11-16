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
        self._temp_dir = None

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        template_image = QLabel('Template Image:')
        self._template_image_dir = QLineEdit('')
        self._template_image_dir.setReadOnly(False)
        self._template_image_button = QPushButton('Browse')

        anatomy_image = QLabel('Anatomy Image:')
        self._anatomy_image_dir = QLineEdit('')
        self._anatomy_image_dir.setReadOnly(False)
        self._anatomy_image_button = QPushButton('Browse')

        mean_function_image = QLabel('Mean Function Image:')
        self._mean_function_image_dir = QLineEdit('')
        self._mean_function_image_dir.setReadOnly(False)
        self._mean_function_image_button = QPushButton('Browse')

        grid_layout = QGridLayout()
        grid_layout.addWidget(template_image, 0, 0, 1, 1)
        grid_layout.addWidget(self._template_image_dir, 0, 1, 1, 1)
        grid_layout.addWidget(self._template_image_button, 0, 2, 1, 1)
        grid_layout.addWidget(anatomy_image, 1, 0, 1, 1)
        grid_layout.addWidget(self._anatomy_image_dir, 1, 1, 1, 1)
        grid_layout.addWidget(self._anatomy_image_button, 1, 2, 1, 1)
        grid_layout.addWidget(mean_function_image, 2, 0, 1, 1)
        grid_layout.addWidget(self._mean_function_image_dir, 2, 1, 1, 1)
        grid_layout.addWidget(self._mean_function_image_button, 2, 2, 1, 1)

        input_data_group = QGroupBox("Input Data: ")
        input_data_group.setLayout(grid_layout)

        self._native_space_radio = QRadioButton('Native Space',self)
        self._template_space_radio = QRadioButton('Template Space',self)
        space_group = QButtonGroup()
        space_group.addButton(self._native_space_radio)
        space_group.addButton(self._native_space_radio)
        self._template_space_radio.setChecked(True)

        space_group_vlayout = QVBoxLayout()
        space_group_vlayout.addWidget(self._template_space_radio)
        space_group_vlayout.addWidget(self._native_space_radio)

        space_group = QGroupBox("Space: ")
        space_group.setLayout(space_group_vlayout)

        self._fsl_radio = QRadioButton('FSL',self)
        self._spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self._fsl_radio)
        radio_group.addButton(self._spm_radio)
        self._fsl_radio.setChecked(True)

        self._spm_dir = QLineEdit('')
        self._spm_dir.setEnabled(True)
        self._spm_dir_button = QPushButton('Browse')
        self._spm_dir.setVisible(False)
        self._spm_dir_button.setVisible(False)

        spm_dir_vlayout = QHBoxLayout()
        spm_dir_vlayout.addWidget(self._spm_radio)
        spm_dir_vlayout.addWidget(self._spm_dir)
        spm_dir_vlayout.addWidget(self._spm_dir_button)

        radio_group_vlayout = QVBoxLayout()
        radio_group_vlayout.addWidget(self._fsl_radio)
        radio_group_vlayout.addLayout(spm_dir_vlayout)

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
        vbox_layout.addWidget(space_group)
        vbox_layout.addWidget(tools_group)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)
        self.setMinimumSize(600, 300)

    def _create_actions(self):
        self._template_image_button.clicked.connect(self._template_image_browse)
        self._anatomy_image_button.clicked.connect(self._anatomy_image_browse)
        self._mean_function_image_button.clicked.connect(self._mean_function_image_browse)
        self._register_button.clicked.connect(self._register)
        self._cancel_button.clicked.connect(self.done)
        self._spm_radio.clicked.connect(self._spm_radio_checked)
        self._fsl_radio.clicked.connect(self._fsl_radio_checked)
        self._spm_dir_button.clicked.connect(self._spm_dir_browse)

    def _template_image_browse(self):
        template_image_filepath = self._open_file_dialog("Add template image file.")
        if template_image_filepath is None:
            QMessageBox.warning("Please choose the template file.")
        else:
            self._temp_dir = template_image_filepath
            self._template_image_dir.setText(template_image_filepath)

    def _anatomy_image_browse(self):
        anatomy_image_filepath = self._open_file_dialog("Add anatomy image file.")
        if anatomy_image_filepath is None:
            QMessageBox.warning("No anatomy image file was choosed.")
        else:
            self._temp_dir = anatomy_image_filepath
            self._anatomy_image_dir.setText(anatomy_image_filepath)

    def _mean_function_image_browse(self):
        mean_function_image_filepath = self._open_file_dialog("Add mean function image file.")
        if mean_function_image_filepath is None:
            QMessageBox.warning("No mean function image file was choosed.")
        else:
            self._temp_dir = mean_function_image_filepath
            self._mean_function_image_dir.setText(mean_function_image_filepath)

    def _reference_browse(self):
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_name = QFileDialog.getOpenFileName(self,
                                                'Add new file',
                                                temp_dir,
                                                "Nifti files (*.nii *.nii.gz)")
        import sys
        if not file_name.isEmpty():
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
        self.anatomy_image_dir.setText(file_path)
        self._temp_dir = file_path

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

    def _spm_radio_checked(self):
        self._spm_dir.setVisible(True)
        self._spm_dir_button.setVisible(True)

    def _fsl_radio_checked(self):
        self._spm_dir.setVisible(False)
        self._spm_dir_button.setVisible(False)

    def _spm_dir_browse(self):
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        path = QFileDialog.getExistingDirectory(None,
                                                'Select SPM folder:',
                                                temp_dir,
                                                QFileDialog.ShowDirsOnly)
        import sys
        import os
        if not path.isEmpty():
            if sys.platform == 'win32':
                path = unicode(path).encode('gb2312')
                self._temp_dir = os.path.dirname(unicode(path, 'gb2312'))
            else:
                path = str(path)
        self._temp_dir = path
        self._spm_dir.setText(path)


    def _register(self):
        #default spm path:
        # ['/nfs/j3/userhome/zhouguangfu/workingdir/spm']

        if str(self._anatomy_image_dir.text()) is '':
            QMessageBox.warning('The template image cannot be empty!')
            return

        if str(self._template_image_dir.text()) is '' and str(self._mean_function_image_dir.text()) is '':
            QMessageBox.warning('The anatomy or mean function image must be choosed one at least!')
            return

        isNative = False
        if self._template_space_radio.isChecked():
            #template space
            isNative = False
        else:
            #native space
            isNative = True

        if self._fsl_radio.isChecked():
            #fsl register
            rm = RegisterMethod(str(self._template_image_dir.text()),
                                str(self._anatomy_image_dir.text()),
                                str(self._mean_function_image_dir.text()),
                                isNative)
            res = rm.fsl_register()
            print 'fsl_register() => res: ', res
        else:
            #spm register
            spm_path = self._spm_dir.text()
            if spm_path is '':
                QMessageBox.warning("Please choose the spm path!")
                return
            rm = RegisterMethod(str(self._template_image_dir.text()),
                                str(self._anatomy_image_dir.text()),
                                str(self._mean_function_image_dir.text()),
                                isNative,
                                str(spm_path))
            res = rm.spm_normalize()


            print 'spm_normalize() => res: ', res

        self.close()


class RegisterMethod(object):
    def __init__(self,
                 template_image_filename,
                 anatomy_image_filename,
                 mean_function_filename,
                 isNative=False,
                 spm_path=None,
                 parent=None):

        self._template_image_filename = template_image_filename
        self._anatomy_image_filename = anatomy_image_filename
        self._mean_function_filename = mean_function_filename
        self._isNative = isNative
        self._spm_path = spm_path

    #-------------------------------------------- fsl register ---------------------------------------
    def fsl_register(self):
        '''FSL Registration'''
        # Reference link
        # http://nipy.org/nipype/interfaces/generated/nipype.interfaces.fsl.preprocess.html
        # Use FSL FLIRT for coregistration.


        #Only resample
        # > From 2 to 4 mm:
        # > flirt -in brain_2mm.nii.gz -ref brain_2mm.nii.gz -out brain_4mm.nii.gz
        # > -nosearch -applyisoxfm 4
        # >
        # > And back to 2 mm:
        # > flirt -in brain_4mm.nii.gz -ref brain_2mm.nii.gz -out brain_2mm_new.nii.gz
        # > -nosearch -applyisoxfm 2

        if self._anatomy_image_filename is not '' and self._mean_function_filename is not '':
            if self._isNative:
                self._native_fsl_register_mean_function_image()
            else:
                self._template_fsl_register_mean_function_image()
        elif self._anatomy_image_filename is not '':
            if self._isNative:
                return self._fsl_linear_register_two_images(self._template_image_filename, self._anatomy_image_filename)
            else:
                return self._fsl_linear_register_two_images(self._anatomy_image_filename, self._template_image_filename)
        elif self._mean_function_filename is not '':
            if self._isNative:
                return self._fsl_linear_register_two_images(self._template_image_filename, self._mean_function_filename)
            else:
                return self._fsl_linear_register_two_images(self._mean_function_filename, self._template_image_filename)
        else:
            return None

    def _fsl_linear_register_two_images(self, input_image_filename, template_image_filename, omat=None):
        from nipype.interfaces import fsl

        flirt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
        flirt.inputs.in_file = input_image_filename
        flirt.inputs.reference = template_image_filename
        flirt.inputs.output_type = "NIFTI"

        if omat is not None:
            print '_fsl_linear_register_two_images = > omat: ', omat
            flirt.inputs.in_matrix_file = omat
            flirt.inputs.apply_xfm = True

        res = flirt.run()
        print 'flirt.cmdline => ', flirt.cmdline

        # Example output
        # res: ('/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/T1_brain_flirt.nii.gz',
        #       '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/T1_brain_flirt.mat')

        return res.outputs.out_file, res.outputs.out_matrix_file

    def _fsl_nonlinear_register_two_images(self, input_image_filename, template_image_filename, omat=None):
        from nipype.interfaces import fsl

        fnirt = fsl.FNIRT()
        fnirt.inputs.in_file = input_image_filename
        fnirt.inputs.ref_file = self._template_image_filename
        fnirt.inputs.output_type = "NIFTI"

        print '_fsl_nonlinear_register_two_images(flt.cmd): ', fnirt.cmd

        res = fnirt.run()

        # Example output
        # res: ('/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/T1_brain_fnirt.nii.gz',
        #       '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/T1_brain_fnirt.mat')

        print 'res: ', res
        # return res.outputs.out_file, res.outputs.out_matrix_file

    def _template_fsl_register_mean_function_image(self):
        #register mean function image to anatomy image
        r_mean_function_image_filename , f_to_a__matrix = self._fsl_linear_register_two_images(
                                                                   self._mean_function_filename,
                                                                   self._anatomy_image_filename)

        #register anamoty image to template image
        r_anamoty_image_filename , a_to_t_matrix = self._fsl_linear_register_two_images(
                                                                   self._anatomy_image_filename,
                                                                   self._template_image_filename)
        print 'f_to_a__matrix: ', f_to_a__matrix
        print 'a_to_t_matrix: ', a_to_t_matrix

        f_to_t_matrix = str(QDir.currentPath() + QDir.separator()) + 'f_to_t_matrix.mat'
        print 'f_to_t_matrix: ', f_to_t_matrix

        command = "convert_xfm " + " -omat " + f_to_t_matrix + " -concat " + f_to_a__matrix + \
          " " + a_to_t_matrix

        import os
        os.system(command)

        r_mean_function_image_filename, out_matrix = self._fsl_linear_register_two_images(
                                                                        self._mean_function_filename,
                                                                        self._template_image_filename,
                                                                        f_to_t_matrix)

        print '_fsl_register_mean_function_image', [r_anamoty_image_filename,
                                                    r_mean_function_image_filename]
        return r_anamoty_image_filename, r_mean_function_image_filename

    def _native_fsl_register_mean_function_image(self):
        import nibabel as nib

        #register anamoty image to template image
        r_anamoty_image_filename , out_matrix = self._fsl_register(self._template_image_filename,
                                                                   self._anatomy_image_filename)

        print '_native_fsl_register_mean_function_image', r_anamoty_image_filename
        return r_anamoty_image_filename

    def fsl_resampling(self):
        '''FSL Registration'''
        # Reference link
        # http://nipy.org/nipype/interfaces/generated/nipype.interfaces.fsl.preprocess.html
        # Use FSL FLIRT for coregistration.


        #Only resample
        # > From 2 to 4 mm:
        # > flirt -in brain_2mm.nii.gz -ref brain_2mm.nii.gz -out brain_4mm.nii.gz
        # > -nosearch -applyisoxfm 4
        # >
        # > And back to 2 mm:
        # > flirt -in brain_4mm.nii.gz -ref brain_2mm.nii.gz -out brain_2mm_new.nii.gz
        # > -nosearch -applyisoxfm 2

        return None

    #-------------------------------------------- spm register and normalize ---------------------------------------

    def _spm_coregister(self, target_image, source_image):
        if self._spm_path is None:
            return

        import nipype.interfaces.matlab as mlab      # how to run matlab
        # Set the way matlab should be called
        mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")
        # If SPM is not in your MATLAB path you should add it here
        mlab.MatlabCommand.set_default_paths(self._spm_path)

        import nipype.interfaces.spm as spm
        coreg = spm.Coregister()
        coreg.inputs.target = target_image
        coreg.inputs.source = source_image
        res = coreg.run()

        print 'coregistered_files: ', res.outputs.coregistered_source

        return res.outputs.coregistered_source #coregistered_files: (a list of items which are an existing file name)

    def spm_normalize(self):
        '''FSL Registration'''
        # Reference link
        # http://nipy.org/nipype/interfaces/generated/nipype.interfaces.fsl.preprocess.html
        # Use FSL FLIRT for coregistration.


        #Only resample
        # > From 2 to 4 mm:
        # > flirt -in brain_2mm.nii.gz -ref brain_2mm.nii.gz -out brain_4mm.nii.gz
        # > -nosearch -applyisoxfm 4
        # >
        # > And back to 2 mm:
        # > flirt -in brain_4mm.nii.gz -ref brain_2mm.nii.gz -out brain_2mm_new.nii.gz
        # > -nosearch -applyisoxfm 2

        if self._anatomy_image_filename is not '' and self._mean_function_filename is not '':
            if self._isNative:
                self._native_spm_register_mean_function_image()
            else:
                self._template_spm_normalize_mean_function_image()
        elif self._anatomy_image_filename is not '':
            if self._isNative:
                return self._spm_normalize_two_images(self._template_image_filename, self._anatomy_image_filename)
            else:
                return self._spm_normalize_two_images(self._anatomy_image_filename, self._template_image_filename)
        elif self._mean_function_filename is not '':
            if self._isNative:
                return self._spm_normalize_two_images(self._template_image_filename, self._mean_function_filename)
            else:
                return self._spm_normalize_two_images(self._mean_function_filename, self._template_image_filename)
        else:
            return None

    def _spm_normalize_two_images(self, input_image_filename, template_image_filename, omat=None):
        '''SPM Registration'''
        # Reference link
        # http://www.mit.edu/~satra/nipype-nightly/interfaces/generated/nipype.interfaces.spm.preprocess.html
        # http://nipy.org/nipype/users/examples/fmri_spm_dartel.html

        #Registeration and Normalize

        import nipype.interfaces.matlab as mlab      # how to run matlab

        """

        Preliminaries
        -------------

        Set any package specific configuration. The output file format
        for FSL routines is being set to uncompressed NIFTI and a specific
        version of matlab is being used. The uncompressed format is required
        because SPM does not handle compressed NIFTI.
        """

        # Set the way matlab should be called
        # mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")
        # If SPM is not in your MATLAB path you should add it here
        # mlab.MatlabCommand.set_default_paths('/nfs/j3/userhome/zhouguangfu/workingdir/spm')
        if self._spm_path is None:
            QMessageBox.warning('SPM path must be choosed!')
            return

        import nipype.interfaces.matlab as mlab      # how to run matlab
        # Set the way matlab should be called
        mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")
        # If SPM is not in your MATLAB path you should add it here
        mlab.MatlabCommand.set_default_paths(self._spm_path)

        import nipype.interfaces.spm as spm
        norm = spm.Normalize()
        # norm.inputs.apply_to_files = input_image_filename
        # norm.inputs.out_prefix = 'w_'

        if omat is not None:
            norm.inputs.parameter_file = omat
            print 'Normalize with parameters file: ', omat
        else:
            norm.inputs.template = template_image_filename
            norm.inputs.source = input_image_filename


        #Compute the bounding box....
        import nibabel as nib
        from nibabel.affines import apply_affine
        import numpy as np
        reference_origin = apply_affine(np.linalg.inv(nib.load(self._template_image_filename).affine), [0, 0, 0])

        print 'reference_origin: ', reference_origin

        #Should be auto calculated based on the given template image !!!!
        norm.inputs.write_bounding_box = [[-90, -126, -72], [90, 90, 108]]

        res = norm.run()

        print 'res.outputs.out_file, res.outputs.out_parameters_file: ', res.outputs.normalized_files, \
                                                                         res.outputs.normalization_parameters
        return res.outputs.normalized_files, res.outputs.normalization_parameters

    def _template_spm_normalize_mean_function_image(self):
        r_anamoty_image_filename = self._spm_coregister(self._mean_function_filename, self._anatomy_image_filename)

        #register anamoty image to template image
        wr_anamoty_image_filename , out_parameters_matrix = self._spm_normalize_two_images(r_anamoty_image_filename,
                                                                                          self._template_image_filename)

        wr_mean_function_image_filename, out_matrix = self._spm_normalize_two_images(self._mean_function_filename,
                                                                                    self._template_image_filename,
                                                                                    out_parameters_matrix)

        print '_template_spm_normalize_mean_function_image: ', [wr_anamoty_image_filename, wr_mean_function_image_filename]

        return wr_anamoty_image_filename, wr_mean_function_image_filename

    def _native_spm_normalize_mean_function_image(self):
        import nibabel as nib

        #register the affine matrix from anamoty to mean function image
        anamoty_image = nib.load(self._anatomy_image_filename)
        nib.save(nib.Nifti1Image(nib.load(self._mean_function_filename).get_affine(), anamoty_image.get_data()),
                 self._anatomy_image_filename)

        #register anamoty image to template image
        r_anamoty_image_filename , out_matrix = self._spm_normalize(self._template_image_filename,
                                                                   self._anatomy_image_filename)

        print '_native_fsl_register_mean_function_image', r_anamoty_image_filename
        return r_anamoty_image_filename






