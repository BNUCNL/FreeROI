import numpy as np
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


class CiftiReader(object):

    def __init__(self, file_path):
        self.full_data = nib.load(file_path)

    @property
    def header(self):
        return self.full_data.header

    @property
    def brain_structures(self):
        return [_.brain_structure for _ in self.header.get_index_map(1).brain_models]

    @property
    def volume(self):
        return self.header.get_index_map(1).volume

    def brain_models(self, structures=None):
        """
        get brain model from cifti file

        Parameter:
        ---------
        structures: list of str
            Each structure corresponds to a brain model.
            If None, get all brain models.

        Return:
        ------
            brain_models: list of Cifti2BrainModel
        """
        brain_models = list(self.header.get_index_map(1).brain_models)
        if structures is not None:
            if not isinstance(structures, list):
                raise TypeError("The parameter 'structures' must be a list")
            brain_models = [brain_models[self.brain_structures.index(s)] for s in structures]
        return brain_models

    def map_names(self, rows=None):
        """
        get map names

        Parameters:
        ----------
        rows: sequence of integer
            Specify which map names should be got.
            If None, get all map names

        Return:
        ------
        map_names: list of str
        """
        named_maps = list(self.header.get_index_map(0).named_maps)
        if named_maps:
            if rows is None:
                map_names = [named_map.map_name for named_map in named_maps]
            else:
                map_names = [named_maps[i].map_name for i in rows]
        else:
            map_names = []
        return map_names

    def label_tables(self, rows=None):
        """
        get label tables

        Parameters:
        ----------
        rows: sequence of integer
            Specify which label tables should be got.
            If None, get all label tables.

        Return:
        ------
        label_tables: list of Cifti2LableTable
        """
        named_maps = list(self.header.get_index_map(0).named_maps)
        if named_maps:
            if rows is None:
                label_tables = [named_map.label_table for named_map in named_maps]
            else:
                label_tables = [named_maps[i].label_table for i in rows]
        else:
            label_tables = []
        return label_tables

    def get_data(self, structure=None, zeroize=False):
        """
        get data from cifti file

        Parameters:
        ----------
        structure: str
            One structure corresponds to one brain model.
            specify which brain structure's data should be extracted
            If None, get all structures, meanwhile ignore parameter 'zeroize'.
        zeroize: bool
            If true, get data after filling zeros for the missing vertices.

        Return:
        ------
        data: numpy array
            If zeroize is False, the data is (maps, values).
            If zeroize is True and brain model type is SURFACE, the data is (maps, values) with filled zeros.
            If zeroize is True and brain model type is VOXELS, the data is (maps, volumes) with filled zeros.
        """

        _data = np.array(self.full_data.get_data())
        if structure is not None:
            brain_model = self.brain_models([structure])[0]
            offset = brain_model.index_offset
            count = brain_model.index_count

            if zeroize:
                if brain_model.model_type == 'CIFTI_MODEL_TYPE_SURFACE':
                    n_vtx = brain_model.surface_number_of_vertices
                    data = np.zeros((_data.shape[0], n_vtx), _data.dtype)
                    data[:, list(brain_model.vertex_indices)] = _data[:, offset:offset+count]
                elif brain_model.model_type == 'CIFTI_MODEL_TYPE_VOXELS':
                    # This function have not been verified visually.
                    vol_shape = self.header.get_index_map(1).volume.volume_dimensions
                    data_shape = (_data.shape[0],) + vol_shape
                    data_ijk = np.array(list(brain_model.voxel_indices_ijk))
                    data = np.zeros(data_shape, _data.dtype)
                    data[:, data_ijk[:, 0], data_ijk[:, 1], data_ijk[:, 2]] = _data[:, offset:offset+count]
                else:
                    raise RuntimeError("The function can't support the brain model: {}".format(brain_model.model_type))
            else:
                data = _data[:, offset:offset+count]
        else:
            data = _data

        return data
