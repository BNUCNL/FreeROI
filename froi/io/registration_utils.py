# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from froi.gui.base import utils as froi_utils
from nibabel.tmpdirs import InTemporaryDirectory
from scipy.io import savemat
import scipy.io as sio

import subprocess
import os
import re
import sys
import nibabel as nib
import numpy as np


class Registration:
    def __init__(self,
                 source_image_filename,
                 template_image_filename,
                 auxiliary_image_filename,
                 voxel_image_size,
                 boudingbox,
                 interp=1):

        self._source_image_filename = source_image_filename
        self._resample_image_filename = auxiliary_image_filename
        self._template_image_filename = template_image_filename
        self._voxel_image_size = voxel_image_size
        self._boudingbox = boudingbox
        self._interp = interp

        self._spm = None

        self._data_dir = froi_utils.get_data_dir()

    def _init_spm_instances(self):
        mat_contents = self._get_mat_contents()
        self._spm = mat_contents['matlabbatch'].spm

    def _spm_normalise1(self):
        if not self._spm:
            return

        self._spm_template_mat_eswrite_file = os.path.join(self._data_dir, 'spm_mat_template').join('normalise1.mat')
        mat_contents = sio.loadmat(self._spm_template_mat_eswrite_file, struct_as_record=False, squeeze_me=True)
        spm = mat_contents['matlabbatch'].spm

        spm_write = None

        spm_write = spm.spatial.normalise.estwrite
        print 'spm_write.subj.source: ', spm_write.subj.source
        print 'spm_write.subj.resample: ', spm_write.subj.resample
        spm_write.subj.source = ''
        spm_write.subj.resample = ''

        spm_write.eoptions.template = ''
        spm_write.eoptions.regtype = 'mni'

        spm_write.roptions.bb = [-72, -108, -90, 90, 90, 108]
        spm_write.roptions.prefix = 'w'
        spm_write.roptions.vox = [2, 2, 2]
        spm_write.roptions.interp = 1

        #run matlab script
        #reference :
        #https://github.com/nipy/nipy/blob/master/nipy/interfaces/spm.py

    def _spm_normalise2(self):
        if not self._spm:
            return

        self._spm_template_mat_eswrite_file = os.path.join(self._data_dir, 'spm-mat_template').join('normalise2.mat')
        mat_contents = sio.loadmat(self._spm_template_mat_eswrite_file, struct_as_record=False, squeeze_me=True)

        spm_write = self._spm.spatial.normalise.write
        spm_write.subj.matname = ''
        spm_write.subj.resample = ''

        spm_write.eoptions.template = ''
        spm_write.eoptions.regtype = 'mni'

        spm_write.roptions.bb = [-72, -108, -90, 90, 90, 108]
        spm_write.roptions.prefix = 'w'
        spm_write.roptions.vox = [2, 2, 2]
        spm_write.roptions.interp = 1

        sio.savemat(self._spm_template_mat_eswrite_file, self._get_mat_contents())

        #run matlab script



    #---------------------------------------------------------------------------------------------------------------
    def _fsl_register1(self):
        #fsl registration:
        # flirt -in inputvol -ref refvol -init <matrix-filename> -omat <matrix-filename> -out <outputvol> \
        #  -applyxfm <scale> -interp trilinear
        #args: interp: nearestneighbour

        omat_filename = None
        output_filename = None

        if sys.platform == 'win32':
            output_filename_path = unicode(output_filename).encode('gb2312')
            out_matrix_filename_path = unicode(omat_filename).encode('gb2312')
        else:
            output_filename_path = str(output_filename)
            out_matrix_filename_path = str(omat_filename)

        interp = 'trilinear'
        if self._interp == 1:
            interp = 'nearestneighbour'

        command = ' flirt ' + \
                  ' -in ' + self._source_image_filename + \
                  ' -ref ' + self._template_image_filename + \
                  ' -omat ' + omat_filename + \
                  ' -interp ' + interp + \
                  ' -out ' + output_filename
        print '_fsl_register1: ', command
        try:
            subprocess.call(command, shell=True)
        except:
            pass

        return output_filename, omat_filename


    def _fsl_register2(self, omat_filename):
        #fsl registration:
        # flirt -in inputvol -ref refvol -init <matrix-filename> -omat <matrix-filename> -out <outputvol> \
        #  -applyxfm <scale> -interp trilinear
        #args: interp: nearestneighbour

        omat_filename = None
        output_filename = None

        interp = 'trilinear'
        if self._interp == 1:
            interp = 'nearestneighbour'

        command = ' flirt ' + \
                  ' -in ' + self._source_image_filename + \
                  ' -ref ' + self._template_image_filename + \
                  ' -interp ' + interp + \
                  ' -out ' + output_filename + \
                  ' -init ' + omat_filename + \
                  ' -applyxfm'
        print '_fsl_register2: ', command
        try:
            subprocess.call(command, shell=True)
        except:
            pass

        return output_filename, omat_filename




    #-----------------------------------------------------------------------------------------------------
    def register(self, is_fsl=True):
        if is_fsl:
            self._fsl_register()
        else:
            self._spm_normalise1()





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
        if self._target_image_filename is not '' and self._auxiliary_image_filename is not '':
            return self._fsl_register_auxiliary_image()
        elif self._source_image_filename is not '' and self._auxiliary_image_filename is '':
            return [self._fsl_register(self._target_image_filename, self._source_image_filename)[0]]
        else:
            self.set_error_info('FSL register error as for the wrong input!')
            return None

    def _fsl_register(self, target_image, source_image, omat=None):
        #fsl registration:
        # flirt -in inputvol -ref refvol -init <matrix-filename> -omat <matrix-filename> -out <outputvol> \
        #  -applyxfm <scale> -interp trilinear
        #args: interp: nearestneighbour

        output_basename = os.path.basename(source_image.strip('/'))
        output_filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', output_basename)
        omat_filename = os.path.join(os.path.dirname(source_image), output_filename + '_flirt.mat')
        output_filename = os.path.join(os.path.dirname(source_image), output_filename + '_flirt.nii')

        if sys.platform == 'win32':
            output_filename_path = unicode(output_filename).encode('gb2312')
            out_matrix_filename_path = unicode(omat_filename).encode('gb2312')
        else:
            output_filename_path = str(output_filename)
            out_matrix_filename_path = str(omat_filename)

        interp = 'trilinear'
        if self._interpolation_method:
            interp = 'nearestneighbour'

        if omat:
            command = ' flirt ' + \
                      ' -in ' + source_image + \
                      ' -ref ' + target_image + \
                      ' -interp ' + interp + \
                      ' -out ' + output_filename + \
                      ' -init ' + omat_filename + \
                      ' -applyxfm'
        else:
            command = ' flirt ' + \
                      ' -in ' + source_image + \
                      ' -ref ' + target_image + \
                      ' -omat ' + omat_filename + \
                      ' -interp ' + interp + \
                      ' -out ' + output_filename
        print '_fsl_register1: ', command
        try:
            subprocess.call(command, shell=True)
        except:
            self.set_error_info('FSL error occured! Make sure the fsl path is in the environment variable ' + \
                                'or the parameter is correct.')

        return output_filename, omat_filename

    def _fsl_register_auxiliary_image(self):
        #register anamoty image to template image
        r_auxiliary_image_filename, apply_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._auxiliary_image_filename)
        print 'apply_matrix: ', apply_matrix
        #register mean function image to anatomy image
        r_source_image_filename , result_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._source_image_filename,
                                                                    omat=apply_matrix)

        return r_source_image_filename, r_auxiliary_image_filename


    #-------------------------------------------- spm normalize ---------------------------------------
    def spm_register(self):
        #detect whether the matlab is exsited.
        # try:
        #     self._run_matlab()
        # except:
        #     self.set_error_info('Cannot find the matlab! Make sure the matlab path has been added to the system ' + \
        #                         'environment path.')
        #     return

        if self._target_image_filename is not '' and self._auxiliary_image_filename is not '':
            return self._spm_normalize_auxiliary_image()
        elif self._source_image_filename is not '' and self._auxiliary_image_filename is '':
            return [self._spm_normalize(self._target_image_filename, self._source_image_filename)[0]]
        else:
            self.set_error_info('SPM normalize error as for the wrong input!')
            return None

    def _spm_normalize(self, target_image, source_image, omat=None):
        """SPM Normalize"""
        spm_write = None
        mat_contents = None
        template_mat_filename = None

        output_basename = os.path.basename(source_image.strip('/'))
        output_filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', output_basename)
        omat_filename = os.path.join(os.path.dirname(source_image), output_filename + '_sn.mat')
        output_filename = os.path.join(os.path.dirname(source_image), 'w' + output_filename + '.nii')
        print 'omat_filename: ', omat_filename
        print 'output_filename: ', output_filename


        if not omat:
            template_mat_filename = os.path.join(froi_utils.get_data_dir(), 'spm_mat_template', 'normalise1.mat')
            print 'template_mat_filename: ', template_mat_filename
            mat_contents = sio.loadmat(template_mat_filename)
            spm = mat_contents['matlabbatch'][0, 0]['spm']
            spm_write = spm[0, 0]['spatial'][0, 0]['normalise'][0, 0]['estwrite']
            # spm_write[0, 0]['subj'][0, 0]['source'][0, 0][0, 0][0] = source_image
            # spm_write[0, 0]['eoptions'][0, 0]['template'][0, 0][0,0][0] = target_image
        else:
            template_mat_filename = os.path.join(self._data_dir, 'spm_mat_template').join('normalise2.mat')
            mat_contents = sio.loadmat(template_mat_filename, struct_as_record=False, squeeze_me=True)
            spm = mat_contents['matlabbatch'][0, 0]['spm']
            spm_write = spm[0, 0]['spatial'][0, 0]['normalise'][0, 0]['write']
            spm_write[0, 0]['subj'][0, 0]['matname'][0, 0][0, 0][0] = omat
        # spm_write[0, 0]['subj'][0, 0]['resample'][0, 0][0, 0][0] = source_image
        # spm_write[0, 0]['eoptions'][0, 0]['regtype'][0, 0][0] = 'mni'
        # spm_write[0, 0]['roptions'][0, 0]['bb'][0, 0] = np.array(self._compute_boundingbox())
        # spm_write[0, 0]['roptions][0, 0]['prefix'][0, 0][0, 0][0] = 'w'
        zooms = nib.load(target_image).get_header().get_zooms()
        voxel_sizes = [float(zooms[0]), float(zooms[1]), float(zooms[2])]
        # spm_write[0, 0]['roptions'][0, 0]['vox'][0, 0] = np.array(voxel_sizes)
        # print 'voxel_size: ', spm_write[0, 0]['roptions'][0, 0]['vox'][0, 0]

        # if self._interpolation_method:
        #     spm_write[0, 0]['roptions'][0, 0]['interp'][0, 0][0, 0][0] = 0
        # sio.savemat(file_name=template_mat_filename, mdict=mat_contents)

        # if not omat:
        #     template_mat_filename = os.path.join(froi_utils.get_data_dir(), 'spm_mat_template','normalise1.mat')
        #     print 'template_mat_filename: ', template_mat_filename
        #     mat_contents = sio.loadmat(template_mat_filename, struct_as_record=False, squeeze_me=True)
        #     spm = mat_contents['matlabbatch'].spm
        #     spm_write = spm.spatial.normalise.estwrite
        #     spm_write.subj.source = source_image
        #     spm_write.eoptions.template = target_image
        # else:
        #     template_mat_filename = os.path.join(self._data_dir, 'spm_mat_template').join('normalise2.mat')
        #     mat_contents = sio.loadmat(template_mat_filename, struct_as_record=False, squeeze_me=True)
        #     spm = mat_contents['matlabbatch'].spm
        #     spm_write = spm.spatial.normalise.write
        #     spm_write.subj.matname = omat
        # spm_write.subj.resample = source_image
        # spm_write.eoptions.regtype = 'mni'
        # spm_write.roptions.bb = self._compute_boundingbox()
        # # spm_write.roptions.prefix = 'w'
        # zooms = nib.load(target_image).get_header().get_zooms()
        # voxel_sizes = [float(zooms[0]), float(zooms[1]), float(zooms[2])]
        # spm_write.roptions.vox = voxel_sizes
        #
        # if self._interpolation_method:
        #     spm_write.roptions.interp = 0
        # sio.savemat(file_name=template_mat_filename, mdict=mat_contents)

        #run matlab script
        print 'run matlab script'
        try:
            with InTemporaryDirectory():
                ret = self._run_matlab_script(r"""spm_path = spm('dir');
                                        spm_ver = spm('ver');
                                        fid = fopen('spm_stuff.txt', 'wt');
                                        fprintf(fid, '%s\n', spm_path);
                                        fprintf(fid, '%s\n', spm_ver);
                                        fclose(fid);
                                        """)
                print 'ret: ', ret #0 for success

                with open('spm_stuff.txt', 'rt') as fobj:
                    lines = fobj.readlines()
                    spm_path = lines[0].strip()
                    spm_ver = lines[1].strip()

                    print 'spm_ver: ', spm_ver
                    print 'spm_path: ', spm_path

            script = """load """ + template_mat_filename + """;spm_jobman('run', matlabbatch);"""
            # Need initcfg for SPM8
            if spm_ver != 'SPM5':
                script = "spm_jobman('initcfg');\n" + script
            with InTemporaryDirectory():
                print 'script: ', script
                self._run_matlab_script(script)
        except:
            self.set_error_info('Spm error occured! Make sure the spm path has been added to the matlab path ' + \
                                'or the parameter is correct.')
            return None, None

        print 'output_filename: ', output_filename
        print 'template_mat_filename: ', template_mat_filename

        if not os.path.exists(output_filename):
            self.set_error_info('Spm error occured!')
            return None, None

        if omat is None:
            self._spm_nan_to_number(output_filename)
            return output_filename, template_mat_filename
        else:
            self._spm_nan_to_number(output_filename)
            return output_filename, template_mat_filename




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


    def _run_matlab(self, cmd):
        matlab_cmd = 'matlab -nojvm -nosplash'
        return subprocess.call('%s -r \"%s;exit\" ' % (matlab_cmd, cmd), shell=True)


    def _run_matlab_script(self, script_lines, script_name='pyscript'):
        """Put multiline matlab script into script file and run."""
        mfile = open(script_name + '.m', 'wt')
        mfile.write(script_lines)
        mfile.close()
        return self._run_matlab(script_name)


if __name__ == '__main__':
    target_image_filename = '/nfs/j3/userhome/zhouguangfu/workingdir/flirt/brain/freeroi/register/std.nii'
    source_image_filename = '/nfs/j3/userhome/zhouguangfu/workingdir/flirt/brain/freeroi/register/T1_brain.nii'

    auxiliary_image_filename = '/nfs/j3/userhome/zhouguangfu/workingdir/flirt/brain/freeroi/register/mean_func.nii'
    auxiliary_image_filename = ''
    interpolation_method = False


    rm = RegisterMethod(target_image_filename,
                        source_image_filename,
                        auxiliary_image_filename,
                        interpolation_method)
    res = None
    _is_fsl = False

    if _is_fsl:
        #fsl register
        res = rm.fsl_register()
    else:
        #detect if the chose file is ended with '.nii', because spm cannot process the .nii.gz file.
        if not str(source_image_filename).endswith('.nii'):
            rm.set_error_info("The source image should be ended with .nii, not .nii.gz or anything else.")
        else:
            #spm register
            res = rm.spm_register()

    # try:
    #     if _is_fsl:
    #         #fsl register
    #         res = rm.fsl_register()
    #     else:
    #         #detect if the chose file is ended with '.nii', because spm cannot process the .nii.gz file.
    #         if not str(source_image_filename).endswith('.nii'):
    #             rm.set_error_info("The source image should be ended with .nii, not .nii.gz or anything else.")
    #         else:
    #             #spm register
    #             res = rm.spm_register()
    # except:
    #     # 'Register error occur!'
    #     rm.set_error_info("Unknown error!")

    print 'rm.get_error_info(): ', rm.get_error_info()


