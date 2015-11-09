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
        self.template_image_dir = QLineEdit('')
        self.template_image_dir.setReadOnly(True)
        self.template_image_button = QPushButton('Browse')

        anatomy_image = QLabel('Anatomy Image:')
        self.anatomy_image_dir = QLineEdit('')
        self.anatomy_image_dir.setReadOnly(True)
        self.anatomy_image_button = QPushButton('Browse')

        function_image = QLabel('Function Image:')
        self.function_image_dir = QLineEdit('')
        self.function_image_dir.setReadOnly(True)
        self.function_image_button = QPushButton('Browse')

        output_image = QLabel('Output Image:')
        self.output_image_dir = QLineEdit('')
        self.output_image_dir.setReadOnly(False)

        grid_layout = QGridLayout()
        grid_layout.addWidget(template_image, 0, 0, 1, 1)
        grid_layout.addWidget(self.template_image_dir, 0, 1, 1, 1)
        grid_layout.addWidget(self.template_image_button, 0, 2, 1, 1)
        grid_layout.addWidget(anatomy_image, 1, 0, 1, 1)
        grid_layout.addWidget(self.anatomy_image_dir, 1, 1, 1, 1)
        grid_layout.addWidget(self.anatomy_image_button, 1, 2, 1, 1)
        grid_layout.addWidget(function_image, 2, 0, 1, 1)
        grid_layout.addWidget(self.function_image_dir, 2, 1, 1, 1)
        grid_layout.addWidget(self.function_image_button, 2, 2, 1, 1)

        input_data_group = QGroupBox("Input Data: ")
        input_data_group.setLayout(grid_layout)

        self.native_space_radio = QRadioButton('Native Space',self)
        self.template_space_radio = QRadioButton('Template Space',self)
        space_group = QButtonGroup()
        space_group.addButton(self.native_space_radio)
        space_group.addButton(self.native_space_radio)
        self.template_space_radio.setChecked(True)

        space_group_vlayout = QVBoxLayout()
        space_group_vlayout.addWidget(self.template_space_radio)
        space_group_vlayout.addWidget(self.native_space_radio)

        space_group = QGroupBox("Space: ")
        space_group.setLayout(space_group_vlayout)

        self.fsl_radio = QRadioButton('FSL',self)
        self.spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self.fsl_radio)
        radio_group.addButton(self.spm_radio)
        self.fsl_radio.setChecked(True)

        radio_group_vlayout = QVBoxLayout()
        radio_group_vlayout.addWidget(self.fsl_radio)
        radio_group_vlayout.addWidget(self.spm_radio)

        tools_group = QGroupBox("Tools: ")
        tools_group.setLayout(radio_group_vlayout)

        self.register_button = QPushButton("Register")
        self.register_button.setFixedWidth(100)
        self.register_button.adjustSize()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.adjustSize()

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.register_button)
        hbox_layout.addWidget(self.cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(input_data_group)
        vbox_layout.addWidget(space_group)
        vbox_layout.addWidget(tools_group)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)
        self.setMinimumSize(600, 300)

    def _create_actions(self):
        self.template_image_button.clicked.connect(self._input_browse)
        self.anatomy_image_button.clicked.connect(self._reference_browse)
        self.function_image_button.clicked.connect(self._output_browse)
        self.register_button.clicked.connect(self._register)
        self.cancel_button.clicked.connect(self.done)

    def _input_browse(self):
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
        self.template_image_dir.setText(file_path)
        self._temp_dir = file_path

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

    def _output_browse(self):
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_types = "Compressed NIFTI file(*.nii.gz);;NIFTI file(*.nii)"
        path,filter = QFileDialog.getSaveFileNameAndFilter(
            self,
            'Save image as...',
            temp_dir,
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
        self._temp_dir = path
        print 'Save output file path: ', path

    def _output_browse(self):
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_types = "Compressed NIFTI file(*.nii.gz);;NIFTI file(*.nii)"
        path,filter = QFileDialog.getSaveFileNameAndFilter(
            self,
            'Save image as...',
            temp_dir,
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
        self._temp_dir = path
        print 'Save output file path: ', path

    def _register(self):
        if str(self.input_dir.text()) is '' or \
            str(self.reference_dir.text()) is '' or \
            str(self.output_dir.text()) is '':
            QMessageBox.warning('Complete the filepath information!')

        rm = RegisterMethod()
        rm.fsl_register(str(self.input_dir.text()),
                        str(self.reference_dir.text()),
                        str(self.output_dir.text()))

        print 'self.output_dir: ', str(self.output_dir.text())

        self.close()


class RegisterMethod(object):
    def __init__(self, parent=None):
        pass



    def fsl_register(self, input_volume_filename, reference_volume_filename, output_volume_filename):
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


        from nipype.interfaces import fsl
        from nipype.testing import example_data
        flt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
        flt.inputs.in_file = input_volume_filename
        flt.inputs.reference = reference_volume_filename
        flt.inputs.output_type = "NIFTI_GZ"
        flt.out_matrix_file = './result/fsl_matrix.mat'
        flt.out_file = output_volume_filename


        print flt.cmdline
        # flt.cmdline
        # 'flirt -in structural.nii -ref mni.nii -out structural_flirt.nii.gz -omat structural_flirt.mat -bins 640 -searchcost mutualinfo'

        res = flt.run()
        print res.outputs
        print 'Register end!'

        return res



    def spm_register(self, input_volume_filename, output_volume_filename):
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

        res = mlab.MatlabCommand(script='which(spm)',
                        paths=['/nfs/j3/userhome/zhouguangfu/workingdir/spm'],
                        mfile=False).run()
        print res.runtime.stdout

        import nipype.interfaces.spm as spm
        coreg = spm.Coregister()
        coreg.inputs.target = output_volume_filename
        coreg.inputs.source = input_volume_filename

        coreg.run()







