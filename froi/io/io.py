import nibabel as nib


def save2nifti(fpath, data, header=None):
        """
        Save to a nifti file.

        Parameters
        ----------
        fpath : string
            The file path to output
        data : numpy array
        header : Nifti2Header
        """
        img = nib.Nifti2Image(data, None, header=header)
        nib.nifti1.save(img, fpath)


class GiftiReader(object):

    def __init__(self, file_path):
        self._fpath = file_path
        self.full_data = nib.load(file_path)

    @property
    def coords(self):
        if self._fpath.endswith('surf.gii'):
            return self.full_data.darrays[0].data
        else:
            return None

    @property
    def faces(self):
        if self._fpath.endswith('surf.gii'):
            return self.full_data.darrays[1].data
        else:
            return None

    @property
    def scalar_data(self):
        if self._fpath.endswith('surf.gii'):
            return None
        else:
            return self.full_data.darrays[0].data
