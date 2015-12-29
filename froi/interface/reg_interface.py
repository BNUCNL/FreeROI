# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nibabel.tmpdirs import InTemporaryDirectory
from matlab import run_matlab, run_matlab_script

import subprocess
import os
import re
import sys
import nibabel as nib
import numpy as np

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
        omat_filename = os.path.join(os.path.dirname(source_image), output_filename + '_flirt.mat').replace("\\","/")
        output_filename = os.path.join(os.path.dirname(source_image), output_filename + '_flirt.nii.gz').replace("\\","/")

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
        try:
            subprocess.call(command, shell=True)
            if not os.path.exists(output_filename):
                raise  ValueError('FSL excute error!')
        except:
            self.set_error_info('FSL error occured! Make sure the fsl path is in the environment variable ' + \
                                'or the parameter is correct.')

        return output_filename, omat_filename

    def _fsl_register_auxiliary_image(self):
        #register anamoty image to template image
        r_auxiliary_image_filename, apply_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._auxiliary_image_filename)
        #register mean function image to anatomy image
        r_source_image_filename , result_matrix = self._fsl_register(self._target_image_filename,
                                                                    self._source_image_filename,
                                                                    omat=apply_matrix)

        return r_source_image_filename, r_auxiliary_image_filename


    #-------------------------------------------- spm normalize ---------------------------------------
    def spm_register(self):
        #detect whether the matlab is exsited.
        try:
            ret = run_matlab('clear all;')
            if ret != 0:
                raise
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

    def _make_normalise_estwrite_job_file(self,
                                         source_image,
                                         target_image,
                                         boundingbox,
                                         voxel_size,
                                         interp):
        return_flag = '\r\n'
        prefix = 'matlabbatch{1}.spm.spatial.normalise.estwrite'
        bb = '[' + str(boundingbox[0][0]) + ' ' + str(boundingbox[0][1]) + ' ' + str(boundingbox[0][2]) + return_flag + \
             str(boundingbox[1][0]) + ' ' + str(boundingbox[1][1]) + ' ' + str(boundingbox[1][2]) + ']'
        command = r"""%-----------------------------------------------------------------------""" + return_flag + \
                  """% Job configuration created by FreeROI.""" + return_flag + \
                  """%-----------------------------------------------------------------------""" + return_flag + \
                  prefix + """.subj.source = {'""" + source_image + """,1'};""" + return_flag + \
                  prefix + """.subj.wtsrc = '';""" + return_flag + \
                  prefix + """.subj.resample = {'""" + source_image + """,1'};""" + return_flag + \
                  prefix + """.eoptions.template = {'""" + target_image + """,1'};""" + return_flag + \
                  prefix + """.eoptions.weight = '';""" + return_flag + \
                  prefix + """.eoptions.smosrc = 8;""" + return_flag + \
                  prefix + """.eoptions.smoref = 0;""" + return_flag + \
                  prefix + """.eoptions.regtype = 'mni';""" + return_flag + \
                  prefix + """.eoptions.cutoff = 25;""" + return_flag + \
                  prefix + """.eoptions.nits = 16;""" + return_flag + \
                  prefix + """.eoptions.reg = 1;""" + return_flag + \
                  prefix + """.roptions.preserve = 0;""" + return_flag + \
                  prefix + """.roptions.bb = """ + bb + """;""" + return_flag + \
                  prefix + """.roptions.vox = """ + str(voxel_size).replace(',', ' ') + """;""" + return_flag + \
                  prefix + """.roptions.interp = """ + str(interp) + """;""" + return_flag + \
                  prefix + """.eoptions.wrap = [0 0 0];""" + return_flag + \
                  prefix + """.eoptions.prefix = 'w';""" + return_flag

        template_mat_filename = os.path.join(os.path.dirname(source_image), 'normalise1_job.m').replace("\\","/")
        if sys.platform == 'win32':
            command = command.replace('/', '\\')
            template_mat_filename = template_mat_filename.replace('/', '\\')

        file = open(template_mat_filename, "wb")
        file.write(command)
        file.close()

        return template_mat_filename

    def _make_normalise_write_job_file(self,
                                      source_image,
                                      omat_file,
                                      boundingbox,
                                      voxel_size,
                                      interp):
        return_flag = '\r\n'
        bb = '[' + str(boundingbox[0][0]) + ' ' + str(boundingbox[0][1]) + ' ' + str(boundingbox[0][2]) + return_flag + \
             str(boundingbox[1][0]) + ' ' + str(boundingbox[1][1]) + ' ' + str(boundingbox[1][2]) + ']'
        prefix = 'matlabbatch{1}.spm.spatial.normalise.write'
        command = """%-----------------------------------------------------------------------""" + return_flag + \
                  """% Job configuration created by FreeROI.""" + return_flag + \
                  """%-----------------------------------------------------------------------""" + return_flag + \
                  prefix + """.subj.matname = {'""" + omat_file + """'};""" + return_flag + \
                  prefix + """.subj.resample = {'""" + source_image + """,1'};""" + return_flag + \
                  prefix + """.roptions.preserve = 0;""" + return_flag + \
                  prefix + """.roptions.bb = """ + bb + """;""" + return_flag + \
                  prefix + """.roptions.vox = """ + str(voxel_size).replace(',', ' ') + """;""" + return_flag + \
                  prefix + """.roptions.interp = """ + str(interp) + """;""" + return_flag + \
                  prefix + """.eoptions.wrap = [0 0 0];""" + return_flag + \
                  prefix + """.eoptions.prefix = 'w';""" + return_flag

        template_mat_filename = os.path.join(os.path.dirname(source_image), 'normalise2_job.m').replace("\\", "/")
        if sys.platform == 'win32':
            command = command.replace('/', '\\')
            template_mat_filename = template_mat_filename.replace('/', '\\')

        file = open(template_mat_filename, "wb")
        file.write(command)
        file.close()

        return template_mat_filename

    def _spm_normalize(self, target_image, source_image, omat=None):
        """SPM Normalize"""
        spm_write = None
        mat_contents = None
        template_m_filename = None

        output_basename = os.path.basename(source_image.strip('/'))
        output_filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', output_basename)
        omat_filename = os.path.join(os.path.dirname(source_image), output_filename + '_sn.mat').replace("\\", "/")
        temp_filename = os.path.join(os.path.dirname(source_image), 'temp_w' + output_filename + '.nii').replace("\\", "/")
        output_filename = os.path.join(os.path.dirname(source_image), 'w' + output_filename + '.nii').replace("\\", "/")
        #SPM normalise
        interp = 1
        if self._interpolation_method:
            interp = 0
        zooms = nib.load(target_image).get_header().get_zooms()
        voxel_sizes = [float(zooms[0]), float(zooms[1]), float(zooms[2])]

        if not omat:
            template_m_filename = self._make_normalise_estwrite_job_file(source_image,
                                                                         target_image,
                                                                         self._compute_boundingbox(),
                                                                         voxel_sizes,
                                                                         interp)
        else:
            template_m_filename = self._make_normalise_write_job_file(source_image,
                                                                      omat,
                                                                      self._compute_boundingbox(),
                                                                      voxel_sizes,
                                                                      interp)

        #Another method to read the structure of the mat files.
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
        try:
            # with InTemporaryDirectory():
            #     run_matlab_script(r"""spm_path = spm('dir');
            #                             spm_ver = spm('ver');
            #                             fid = fopen('spm_stuff.txt', 'wt');
            #                             fprintf(fid, '%s\n', spm_path);
            #                             fprintf(fid, '%s\n', spm_ver);
            #                             fclose(fid);
            #                             """)
            #     with open('spm_stuff.txt', 'rt') as fobj:
            #         lines = fobj.readlines()
            #         spm_path = lines[0].strip()
            #         spm_ver = lines[1].strip()
            spm_ver = 'SPM8'
            # script = """load """ + template_mat_filename + """;spm_jobman('run', matlabbatch);"""
            script = """jobfile = {'""" + template_m_filename + """'};""" \
                     + """jobs = repmat(jobfile, 1, 1);""" \
                     + """inputs = cell(0, 1);""" \
                     + """spm('defaults', 'FMRI');""" \
                     + """spm_jobman('serial', jobs, '', inputs{:});"""
            # Need initcfg for SPM8
            if spm_ver != 'SPM5':
                script = "spm_jobman('initcfg');\n" + script

            with InTemporaryDirectory():
                run_matlab_script(script)
                if not os.path.exists(output_filename):
                    self.set_error_info('Spm error occured!')
        except Exception as e:
            self.set_error_info('Spm error occured! ' + str(e))
            if os.path.exists(template_m_filename):
                os.remove(template_m_filename)
            return None, None

        if os.path.exists(template_m_filename):
            os.remove(template_m_filename)

        output_filename = self._spm_nan_to_number(output_filename, temp_filename)
        return output_filename, omat_filename


    def _spm_normalize_auxiliary_image(self):
        #register anamoty image to template image
        w_source_image_filename , out_parameters_matrix = self._spm_normalize(self._target_image_filename,
                                                                              self._source_image_filename)

        w_auxiliary_image_filename, out_matrix = self._spm_normalize(self._target_image_filename,
                                                                      self._auxiliary_image_filename,
                                                                      out_parameters_matrix)
        return w_source_image_filename, w_auxiliary_image_filename

    def _spm_nan_to_number(self, filename, temp_filename):
        nan_img = nib.load(filename)
        nan_data = nan_img.get_data()
        nan_header = nan_img.get_header()
        nan_data = np.nan_to_num(nan_data)

        nan_image = nib.nifti1.Nifti1Image(nan_data, None, nan_header)
        nib.nifti1.save(nan_image, temp_filename)

        return temp_filename

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



