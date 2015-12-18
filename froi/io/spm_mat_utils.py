# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from froi.gui.base import utils as froi_utils
import scipy.io as sio
import os

class SPMMat:

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


    def _get_mat_contents(self):
        self._spm_template_mat_eswrite_file = os.path.join(self._data_dir, 'spm-mat_template').join('normalise1.mat')
        mat_contents = sio.loadmat(self._spm_template_mat_eswrite_file, struct_as_record=False, squeeze_me=True)


    def _init_spm_instances(self):
        mat_contents = self._get_mat_contents()
        self._spm = mat_contents['matlabbatch'].spm

    def normalise1(self):
        if not self._spm:
            return


        self._spm_template_mat_eswrite_file = os.path.join(self._data_dir, 'spm-mat_template').join('normalise1.mat')
        mat_contents = sio.loadmat(self._spm_template_mat_eswrite_file, struct_as_record=False, squeeze_me=True)

        spm_write = None
        spm_write = self._spm.spatial.normalise.estwrite
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

    def normalise2(self):
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






