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
