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
        self.spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self.fsl_radio)
        radio_group.addButton(self.spm_radio)
        self.fsl_radio.setChecked(True)

        radio_group_hlayout = QHBoxLayout()
        radio_group_hlayout.addWidget(self.fsl_radio)
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
        self.register_button.clicked.connect(self._register)

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
        self.input_dir.setText(file_path)
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
        self.reference_dir.setText(file_path)
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


if __name__ == '__main__':
    pass


    output_volume_filename = '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/brain/test_output.nii'
    input_volume_filename = '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/brain/T1_brain.nii'
    reference_volume_filename = '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/brain/std.nii'

    normalize_volume_filename = '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/brain/spm_r_T1_brain.nii'
    normalizeresult__volume_filename = '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/brain/wspm_r_T1_brain.nii'

    import nibabel as nib
    # input_volume_filename = '/nfs/j3/userhome/zhouguangfu/Desktop/PycharmProjects/FreeROI/bin/brain/T1_brain.nii'
    print nib.load(input_volume_filename).get_data().shape
    print nib.load(reference_volume_filename).get_data().shape
    print nib.load(normalize_volume_filename).get_data().shape
    print nib.load(normalizeresult__volume_filename).get_data().shape

    import nipype.interfaces.matlab as mlab      # how to run matlab

    # Set the way matlab should be called
    mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")
    # If SPM is not in your MATLAB path you should add it here
    mlab.MatlabCommand.set_default_paths('/nfs/j3/userhome/zhouguangfu/spm8')

    # res = mlab.MatlabCommand(script='which(spm)',
    #             paths=['/nfs/j3/userhome/zhouguangfu/spm8'],
    #             mfile=False).run()
    # print res.runtime.stdout

    import nipype.interfaces.spm as spm
    coreg = spm.Coregister()

     #reference file
    coreg.inputs.target = reference_volume_filename
    #a list of items which are an existing file name file to register to target
    coreg.inputs.source = input_volume_filename

    coreg.inputs.cost_function = 'nmi'
    coreg.inputs.separation = [4, 2]
    coreg.inputs.tolerance = [0.02, 0.02, 0.02, 0.001, 0.001, 0.001,
                          0.01, 0.01, 0.01, 0.001, 0.001, 0.001]
    coreg.inputs.fwhm = [7, 7]
    coreg.inputs.write_mask = False
    coreg.inputs.out_prefix = 'spm_r_'
    coreg.inputs.write_wrap = [0, 0, 0]
    coreg.inputs.write_interp = 1
    ret = coreg.run()
    print 'Registeration end!'

    import nipype.interfaces.spm as spm
    norm = spm.Normalize()
    norm.inputs.template = reference_volume_filename
    norm.inputs.source = normalize_volume_filename
    norm.run()


    print 'Program end!'





