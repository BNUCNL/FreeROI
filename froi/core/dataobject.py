# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Dataset definition class for FreeROI GUI system.
"""

import re
import os
import sys

import nibabel as nib
import numpy as np
from scipy import sparse
from scipy.spatial.distance import cdist
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..algorithm import array2qimage as aq
from labelconfig import LabelConfig


class DoStack(QObject):
    """
    For Undo and Redo
    """
    stack_changed = pyqtSignal()

    def __init__(self):
        super(QObject, self).__init__()
        self._stack = []

    def push(self, v):
        self._stack.append(v)
        self.stack_changed.emit()

    def pop(self):
        t = self._stack.pop()
        self.stack_changed.emit()
        return t

    def clear(self):
        self._stack = []

    def stack_not_empty(self):
        if self._stack:
            return True
        else:
            return False

class VolumeDataset(object):
    """Base dataset in FreeROI GUI system."""
    def __init__(self, source, label_config_center, name=None, header=None, 
                 view_min=None, view_max=None, alpha=255, colormap='gray',
                 cross_pos=None):
        """
        Create a dataset from an NiftiImage which has following 
        atributes:
        
        Parameters
        ----------
        source : Nifti file path or 3D/4D numpy array
            Nifti dataset, specified either as a filename (single file 3D/4D 
            image) or a 3D/4D numpy array. When source is a numpy array,
            parameter header is required.
        label_config : label configuration
        name : name of the volume
            volume name.
        header : nifti1 header structure
            Nifti header structure.
        view_min : scalar or None
            The lower limitation of data value which can be seen.
        view_max : scalar
            The upper limitation of data value which can be seen.
        alpha: int number (0 - 255)
            alpha channel value, 0 indicates transparency. Default is 255.
        colormap : string
            The string can represents the colormap used for corresponding
            values, it can be 'gray', 'red2yellow', 'blue2green', 'ranbow'...
        cross_pos : a list containing [x, y, z]
            Default is None

        Returns
        -------
        VolumeDataset

        """
        if isinstance(source, np.ndarray):
            self._data = np.rot90(source)
            if name == None:
                self._name = 'new_image'
            else:
                self._name = str(name)
            if not isinstance(header, nib.nifti1.Nifti1Header):
                raise ValueError("Parameter header must be specified!")
            elif header.get_data_shape() == source.shape:
                self._header = header
                self._img = None
            else:
                raise ValueError("Data dimension does not match.")
        else:
            self._img = nib.load(source)
            self._header = self._img.get_header()
            basename = os.path.basename(source.strip('/'))
            self._name = re.sub(r'(.*)\.nii(\.gz)?', r'\1', basename)
            self.save_mem_load()

        # For convenience, define a shift variable
        self._y_shift = self.get_data_shape()[1] - 1

        if view_min == None:
            self._view_min = self._data.min()
        else:
            self._view_min = view_min

        if view_max == None:
            self._view_max = self._data.max()
        else:
            self._view_max = view_max

        self._alpha = alpha
        self._colormap = colormap
        self._rgba_list = range(self.get_data_shape()[2])
 
        # bool status for the item
        self._visible = True
        if len(self.get_data_shape()) == 3:
            self._4d = False
        else:
            self._4d = True
        self._time_point = 0

        # temporal variant for OrthView
        self._cross_pos = cross_pos

        # define a dictionary 
        self.label_config_center = label_config_center
        self.label_config_center.single_roi_view_update.connect(self.update_single_roi)
        
        # undo redo stacks
        self.undo_stack = DoStack()
        self.redo_stack = DoStack()

        self.update_rgba()
        if self._cross_pos:
            self.update_orth_rgba()

    def save_mem_load(self):
        """Load data around current time-point."""
        if len(self.get_data_shape())==4 and self._img:
            data = np.zeros(self.get_data_shape())
            self._data = np.rot90(data)
            self._loaded_time_list = [0]
            self._data[..., 0] = np.rot90(self._img.dataobj[..., 0])
        else:
            self._loaded_time_list = [0]
            data = self._img.get_data(caching='unchanged')
            self._data = np.rot90(data)

    def get_data_shape(self):
        """Get shape of data."""
        return self._header.get_data_shape()

    def _rendering_factory(self):
        """Return a rendering factory according to the display setting."""
        def shadow(array):
            if not isinstance(self._colormap, LabelConfig):
                colormap = str(self._colormap)
            else:
                colormap = self._colormap.get_colormap()
            try:
                current_roi = self.label_config_center.get_drawing_value()
            except ValueError:
                current_roi = None
            return aq.array2qrgba(array, self._alpha, colormap,
                                  normalize=(self._view_min, self._view_max), 
                                  roi=current_roi)
        return shadow

    def update_single_roi(self):
        """Update the view with single ROI colormap."""
        if self._colormap == 'single ROI':
            self.update_rgba()
            if self._cross_pos:
                self.update_orth_rgba()
            self.label_config_center.single_roi_view_update_for_model.emit() 

    def update_rgba(self, index=None):
        """Create a range of qrgba array for display."""
        # return a rendering factory
        f = self._rendering_factory()

        if index == None:
            if self.is_4d():
                layer_list = [self._data[..., i, self._time_point] for i in 
                                    range(self.get_data_shape()[2])]
            else:
                layer_list = [self._data[..., i] for i in 
                                    range(self.get_data_shape()[2])]
            self._rgba_list = map(f, layer_list)
        else:
            if self.is_4d():
                self._rgba_list[index] = f(self._data[..., index,
                                                      self._time_point])
            else:
                self._rgba_list[index] = f(self._data[..., index])

    def set_cross_pos(self, cross_pos):
        """ Update RGBA data in sagital, axial and coronal directions."""
        if self._cross_pos:
            if not cross_pos[0] == self._cross_pos[0]:
                self._cross_pos[0] = cross_pos[0]
                self.update_sagital_rgba()
            if not cross_pos[1] == self._cross_pos[1]:
                self._cross_pos[1] = cross_pos[1]
                self.update_coronal_rgba()
            if not cross_pos[2] == self._cross_pos[2]:
                self._cross_pos[2] = cross_pos[2]
                self.update_axial_rgba()
        else:
            self._cross_pos = cross_pos
            self.update_sagital_rgba()
            self.update_coronal_rgba()
            self.update_axial_rgba()
    
    def update_orth_rgba(self):
        """Update the disply in orth view."""
        self.update_sagital_rgba()
        self.update_coronal_rgba()
        self.update_axial_rgba()

    def update_sagital_rgba(self):
        """Update the sagital disply in orth view."""
        f = self._rendering_factory()
        idx = self._cross_pos[0]
        if self.is_4d():
            self._sagital_rgba = f(np.rot90(self._data[:, idx, :,
                                                       self._time_point]))
        else:
            self._sagital_rgba = f(np.rot90(self._data[:, idx, :]))

    def update_axial_rgba(self):
        """Update the axial disply in orth view."""
        f = self._rendering_factory()
        idx = self._cross_pos[2]
        if self.is_4d():
            self._axial_rgba = f(self._data[:, :, idx, self._time_point])
        else:
            self._axial_rgba = f(self._data[:, :, idx])

    def update_coronal_rgba(self):
        """Update the coronal disply in orth view."""
        f = self._rendering_factory()
        idx = self._y_shift - self._cross_pos[1]
        if self.is_4d():
            self._coronal_rgba = f(np.rot90(self._data[idx, :, :,
                                                       self._time_point]))
        else:
            self._coronal_rgba = f(np.rot90(self._data[idx, :, :]))

    def set_alpha(self, alpha):
        """Set alpha value."""
        if isinstance(alpha, int):
            if alpha <= 255 and alpha >= 0:
                if self._alpha != alpha:
                    self._alpha = alpha
                    self.update_rgba()
                    if self._cross_pos:
                        self.update_orth_rgba()
        else:
            raise ValueError("Value must be an integer between 0 and 255.")

    def get_alpha(self):
        """Get alpha value."""
        return self._alpha

    def set_time_point(self, tpoint):
        """Set time point."""
        if self.is_4d():
            if isinstance(tpoint, int):
                if tpoint >= 0 and tpoint < self.get_data_shape()[3]:
                    if self._img:
                        if not tpoint in self._loaded_time_list:
                            self._data[..., tpoint] = \
                                    np.rot90(self._img.dataobj[..., tpoint])
                            self._loaded_time_list.append(tpoint)
                    self._time_point = tpoint
                    self.undo_stack.clear()
                    self.redo_stack.clear()
                    self.update_rgba()
                    if self._cross_pos:
                        self.update_orth_rgba()
            else:
                raise ValueError("Value must be an integer.")
    
    def get_time_point(self):
        """Get time point."""
        return self._time_point

    def set_view_min(self, view_min):
        """Set lower limition of display range."""
        try:
            view_min = float(view_min)
            self._view_min = view_min
            self.update_rgba()
            if self._cross_pos:
                self.update_orth_rgba()
        except ValueError:
            print "view_min must be a number."

    def get_view_min(self):
        """Get lower limition of display range."""
        return self._view_min

    def set_view_max(self, view_max):
        """Set upper limition of display range."""
        try:
            view_max = float(view_max)
            self._view_max = view_max
            self.update_rgba()
            if self._cross_pos:
                self.update_orth_rgba()
        except ValueError:
            print"view_max must be a number."

    def get_view_max(self):
        """Get upper limition of display range."""
        return self._view_max
    
    def set_name(self, name):
        """Set item's name."""
        self._name = str(name)

    def get_name(self):
        """Get item's name."""
        return self._name

    def set_colormap(self, map_name):
        """Set item's colormap."""
        self._colormap = map_name
        self.update_rgba()
        if self._cross_pos:
            self.update_orth_rgba()

    def get_colormap(self):
        """Get item's colormap."""
        return self._colormap

    def set_visible(self, status):
        """Set visibility of the volume."""
        if isinstance(status, bool):
            if status:
                self._visible = True
            else:
                self._visible = False
        else:
            raise ValueError("Input must a bool.")

    def is_4d(self):
        """If the data is including several time points, return True."""
        return self._4d

    def is_visible(self):
        """Query the status of visibility."""
        return self._visible

    def get_rgba(self, index):
        """Get rgba array based on the index of the layer."""
        return self._rgba_list[index]

    def get_sagital_rgba(self):
        """Return the sagital rgba value.."""
        if self._sagital_rgba.tolist():
            return self._sagital_rgba
        else:
            return False

    def get_axial_rgba(self):
        """Return the axial rgba value."""
        if self._axial_rgba.tolist():
            return self._axial_rgba
        else:
            return False

    def get_coronal_rgba(self):
        """Return the coronal rgba value.."""
        if self._coronal_rgba.tolist():
            return self._coronal_rgba
        else:
            return False

    def set_voxel(self, x, y, z, value, ignore=True):
        """Set value of the voxel whose coordinate is (x, y, z)."""
        try:
            if isinstance(y, list):
                y_trans = [self._y_shift - item for item in y]
            if self.is_4d():
                orig_data = self._data[y_trans, x, z, self._time_point]
            else:
                orig_data = self._data[y_trans, x, z]
            if np.any(orig_data != 0) and not ignore:
                force = QMessageBox.question(None, "Replace?",
                        "Would you like to replace the original values?",
                        QMessageBox.Yes,
                        QMessageBox.No)
                if force == QMessageBox.No:
                    return
            if self.is_4d():
                self.undo_stack.push((x, y, z, self._data[y_trans, x, z,
                                                          self._time_point]))
                self._data[y_trans, x, z, self._time_point] = value
            else:
                self.undo_stack.push((x, y, z, self._data[y_trans, x, z]))
                self._data[y_trans, x, z] = value
            try:
                for z_ in range(min(z), max(z)+1):
                    self.update_rgba(z_)
            except TypeError:
                self.update_rgba(z)
            if self._cross_pos:
                self.update_orth_rgba()
        except:
            raise
            print "Input coordinates are invalid."

    def save2nifti(self, file_path):
        """Save to a nifti file."""
        #Define nifti1 datatype codes
        NIFTI_TYPE_UINT8 = 2  # unsigned char
        NIFTI_TYPE_INT16 = 4  # signed short
        NIFTI_TYPE_INT32 = 8  # signed int.
        NIFTI_TYPE_FLOAT32 = 16  # 32 bit float.
        NIFTI_TYPE_COMPLEX64 = 32  # 64 bit complex = 2 32 bit floats
        NIFTI_TYPE_FLOAT64 = 64  # 64 bit float = double.
        NIFTI_TYPE_RGB24 = 128  # 3 8 bit bytes.
        NIFTI_TYPE_INT8 = 256  # signed char.
        NIFTI_TYPE_UINT16 = 512  # unsigned short.
        NIFTI_TYPE_UINT32 = 768  # unsigned int.
        NIFTI_TYPE_INT64 = 1024  #signed long long.
        NIFTI_TYPE_UINT64 = 1280  # unsigned long long.
        NIFTI_TYPE_FLOAT128 = 1536  # 128 bit float = long double.
        NIFTI_TYPE_COMPLEX128 = 1792  #128 bit complex = 2 64 bit floats.
        NIFTI_TYPE_COMPLEX256 = 2048  # 256 bit complex = 2 128 bit floats
        NIFTI_TYPE_RGBA32 = 2304  # 4 8 bit bytes.

         #Detect the data type of the input data.
        data_type = {
            np.uint8: NIFTI_TYPE_UINT8,
            np.uint16: NIFTI_TYPE_UINT16,
            np.uint32: NIFTI_TYPE_UINT32,
            np.float32: NIFTI_TYPE_FLOAT32,
            np.int16: NIFTI_TYPE_INT16,
            np.int32: NIFTI_TYPE_INT32,
            np.int8: NIFTI_TYPE_INT8
            }
        if sys.maxint > 2 ** 32: # The platform is 64 bit
            data_type[np.float128] = NIFTI_TYPE_FLOAT128
            data_type[np.float64] = NIFTI_TYPE_FLOAT64
            data_type[np.int64] = NIFTI_TYPE_INT64
            data_type[np.uint64] = NIFTI_TYPE_UINT64
            data_type[np.complex64] = NIFTI_TYPE_COMPLEX64
            data_type[np.complex128] = NIFTI_TYPE_COMPLEX128
            data_type[np.complex256] = NIFTI_TYPE_COMPLEX256

        data = np.rot90(self._data, 3)
        if data_type.has_key(data.dtype.type):
            self._header['datatype'] = data_type[data.dtype.type]
        self._header['cal_max'] = data.max()
        self._header['cal_min'] = 0
        image = nib.nifti1.Nifti1Image(data, None, self._header)
        nib.nifti1.save(image, file_path)

    def get_label_config(self):
        """Return the label config object."""
        return self.label_config_center

    def undo_stack_not_empty(self):
        """Return status of the undo stack."""
        return self.undo_stack.stack_not_empty()

    def redo_stack_not_empty(self):
        return self.redo_stack.stack_not_empty()

    def undo(self):
        """Resume to the last step."""
        if self.undo_stack:
            voxel_set = self.undo_stack.pop()
            self.set_voxel(*voxel_set, ignore=True)
            self.redo_stack.push(self.undo_stack.pop())
            return voxel_set[2]
        return None

    def redo(self):
        """Forward to the next step."""
        if self.redo_stack:
            voxel_set = self.redo_stack.pop()
            self.set_voxel(*voxel_set, ignore=True)
            return voxel_set[2]
        return None

    def connect_undo(self, slot):
        """Connect the event to the undo slot.
        """
        self.undo_stack.stack_changed.connect(slot)

    def connect_redo(self, slot):
        """Connect the event to the undo slot."""
        self.redo_stack.stack_changed.connect(slot)

    def get_header(self):
        """Get the header of the data.."""
        return self._header

    def get_value(self, xyz, time_course=False):
        """Get the valoue based on the given x,y,z cordinate."""
        if not time_course:
           if self.is_4d():
               return self._data[self._y_shift - xyz[1],
                                 xyz[0], xyz[2], self._time_point]
           else:
               return self._data[self._y_shift - xyz[1], xyz[0], xyz[2]]
        else:
            if self.is_4d() and self._img:
               data = self.get_raw_data()
               data = np.rot90(data)
               return data[self._y_shift - xyz[1], xyz[0], xyz[2], :]
            elif self.is_4d():
               return self._data[self._y_shift - xyz[1], xyz[0], xyz[2], :]
            else:
               return self._data[self._y_shift - xyz[1], xyz[0], xyz[2]]

    def get_lthr_data(self):
        """Return whole data which low-thresholded."""
        # FIXME one time point or whole data
        temp = self._data.copy()
        temp[temp <= self._view_min] = 0
        return temp

    def get_lthr_raw_data(self):
        """
        Return the low threshold of the raw data.
        """
        temp = self._data.copy()
        temp[temp <= self._view_min] = 0
        return np.rot90(temp, 3)

    def get_raw_data(self):
        """Return the raw data."""
        if self._img and self.is_4d():
            temp = self._img.get_data(caching='unchanged')
            temp = np.rot90(temp)
            for tp in self._loaded_time_list:
                temp[..., tp] = self._data[..., tp]
        else:
            temp = self._data.copy()

        return np.rot90(temp, 3)

    def get_value_label(self, value):
        """Return the label of the given value."""
        return self.label_config.get_index_label(value)

    def set_label(self, label_config):
        """Set the label using the given label_config parameter."""
        self.label_config = label_config

    def is_label_global(self):
        """Return the value whether the label is global."""
        return self.label_config.is_global

    def get_roi_coords(self, roi):
        """Return cordinates of the given roi."""
        if self.is_4d():
            data = self._data[..., self._time_point]
        else:
            data = self._data
        coord = (data==roi).nonzero()
        #return (data==roi).nonzero()
        return (coord[1], self._y_shift - coord[0], coord[2])

    def get_coord_val(self, x, y, z):
        """Return value based on the given x,y,z cordinate."""
        if self.is_4d():
            #return self._data[y, x, z, self._time_point]
            return self._data[self._y_shift - y, x, z, self._time_point]
        else:
            #return self._data[y, x, z]
            return self._data[self._y_shift - y, x, z]

    def duplicate(self):
        """Return a duplicated image."""
        dup_img = VolumeDataset(source=self.get_raw_data(),
                                label_config_center=self.get_label_config(),
                                name=self.get_name()+'_duplicate',
                                header=self.get_header(),
                                view_min=self.get_view_min(),
                                view_max=self.get_view_max(),
                                alpha=self.get_alpha(),
                                colormap=self.get_colormap())
        return dup_img

class SurfaceDataset(object):
    """Container for surface object in FreeROI GUI system.

    Attributes
    ----------
    subject_id: string
        Name of subject
    hemi: {'lh', 'rh'}
        Which hemisphere to load
    surf: string
        Name of the surface to load (eg. inflated, orig ...)
    data_path: string
        Path where to look for data
    x: 1d array
        x coordinates of vertices
    y: 1d array
        y coordinates of vertices
    z: 1d array
        z coordinates of vertices
    coords: 2d array of shape [n_vertices, 3]
        The vertices coordinates
    faces: 2d array
        The faces ie. the triangles
    nn: 2d array
        Normalized surface normals for vertices
    subjects_dir: str | None
        If not None, this directory will be used as the subjects directory
        instead of the value set using the SUBJECTS_DIR enviroment variable.

    """

    def __init__(self, subject_id, hemi, surf, subjects_dir=None,
                 offset=None):
        """Surface
        
        Parameters
        ----------
        subject_id: string
            Name of subject
        hemi: {'lh', 'rh'}
            Which hemisphere to load
        surf: string
            Name of the surface to load (eg. inflated, orig ...)
        offset: float | None
            If 0.0, the surface will be offset such that medial wall
            is aligned with the origin. If None, no offset will be
            applied. If != 0.0, an additional offset will be used.

        """
        if hemi not in ['lh', 'rh']:
            raise ValueError('hemi must be "lh" or "rh"')
        self.subject_id = subejct_id
        self.hemi = hemi
        self.surf = surf
        self.offset = offset

        subjects_dir = _get_subjects_dir(subjects_dir)
        self.data_path = os.path.join(subjects_dir, subejct_id)

    def load_geometry(self):
        """Load surface geometry."""
        surf_path = os.path.join(self.data_path, 'surf',
                                 '%s.%s'%(self.hemi, self.surf))
        self.coords, self.faces = nib.freesurfer.read_geometry(surf_path)
        if self.offset is not None:
            if self.hemi == 'lh':
                self.coords[:, 0] -= (np.max(self.coords[:, 0]) + self.offset)
            else:
                self.coords[:, 0] -= (np.min(self.coords[:, 0]) + self.offset)
        self.nn = _compute_normals(self.coords, self.faces)

    def save_geometry(self):
        """Save geometry information."""
        surf_path = os.path.join(self.data_path, 'surf',
                                 '%s.%s'%(self.hemi, self.surf))
        nib.freesurfer.write_geometry(surf_path, self.coords, self.faces)

    @property
    def x(self):
        return self.coords[:, 0]

    @property
    def y(self):
        return self.coords[:, 1]

    @property
    def z(self):
        return self.coords[:, 2]

    def load_curvature(self):
        """Load in curvature values from the ?h.curv file."""
        curv_path = os.path.join(self.data_path, 'surf', '%s.curv' % self.hemi)
        self.curv = nib.freesurfer.read_morph_data(curv_path)
        self.bin_curv = np.array(self.curv > 0, np.int)

    def load_label(self, name):
        """Load in a FreeSurfer .label file.

        Label files are just text files indicating the vertices included in
        the label. Each Surface instance has a dictionary of labels, keyed
        by the name (which is taken from the file name if not given as an
        argument).
        
        """
        label = nib.freesurfer.read_label(os.path.join(self.data_path, 'label',
                                          '%s.%s.label' % (self.hemi, name)))
        label_array = np.zeros(len(self.x), np.int)
        label_array[label] = 1
        try:
            self.labels[name] = label_array
        except AttributeError:
            self.labels = {name: label_array}

    def apply_xfm(self, mtx):
        """Apply an affine transformation matrix to the x, y, z vectors."""
        self.coords = np.dot(np.c_[self.coords, np.ones(len(self.coords))],
                             mtx.T)[:, 3]

# TODO move to algorithm module
def _fast_cross_3d(x, y):
    """Compute cross product between list of 3D vectors

    Much faster than np.cross() when the number of cross products
    becomes large (>500). This is because np.cross() methods become
    less memory efficient at this stage.

    Parameters
    ----------
    x : array
        Input array 1.
    y : array
        Input array 2.

    Returns
    -------
    z : array
        Cross product of x and y.

    Notes
    -----
    x and y must both be 2D row vectors. One must have length 1, or both
    lengths must match.
    """
    assert x.ndim == 2
    assert y.ndim == 2
    assert x.shape[1] == 3
    assert y.shape[1] == 3
    assert (x.shape[0] == 1 or y.shape[0] == 1) or x.shape[0] == y.shape[0]
    if max([x.shape[0], y.shape[0]]) >= 500:
        return np.c_[x[:, 1] * y[:, 2] - x[:, 2] * y[:, 1],
                     x[:, 2] * y[:, 0] - x[:, 0] * y[:, 2],
                     x[:, 0] * y[:, 1] - x[:, 1] * y[:, 0]]
    else:
        return np.cross(x, y)

def _compute_normals(rr, tris):
    """Efficiently compute vertex normals for triangulated surface"""
    # first, compute triangle normals
    r1 = rr[tris[:, 0], :]
    r2 = rr[tris[:, 1], :]
    r3 = rr[tris[:, 2], :]
    tri_nn = _fast_cross_3d((r2 - r1), (r3 - r1))

    #   Triangle normals and areas
    size = np.sqrt(np.sum(tri_nn * tri_nn, axis=1))
    zidx = np.where(size == 0)[0]
    size[zidx] = 1.0  # prevent ugly divide-by-zero
    tri_nn /= size[:, np.newaxis]

    npts = len(rr)

    # the following code replaces this, but is faster (vectorized):
    #
    # for p, verts in enumerate(tris):
    #     nn[verts, :] += tri_nn[p, :]
    #
    nn = np.zeros((npts, 3))
    for verts in tris.T:  # note this only loops 3x (number of verts per tri)
        for idx in range(3):  # x, y, z
            nn[:, idx] += np.bincount(verts, tri_nn[:, idx], minlength=npts)
    size = np.sqrt(np.sum(nn * nn, axis=1))
    size[size == 0] = 1.0  # prevent ugly divide-by-zero
    nn /= size[:, np.newaxis]
    return nn

def find_closest_vertices(surface_coords, point_coords):
    """Return the vertices on a surface mesh closest to some given coordinates.

    The distance metric used is Euclidian distance.

    Parameters
    ----------
    surface_coords : numpy array
        Array of coordinates on a surface mesh
    point_coords : numpy array
        Array of coordinates to map to vertices

    Returns
    -------
    closest_vertices : numpy array
        Array of mesh vertex ids

    """
    point_coords = np.atleast_2d(point_coords)
    return np.argmin(cdist(surface_coords, point_coords), axis=0)

def tal_to_mni(coords):
    """Convert Talairach coords to MNI using the Lancaster transform.

    Parameters
    ----------
    coords : n x 3 numpy array
        Array of Talairach coordinates

    Returns
    -------
    mni_coords : n x 3 numpy array
        Array of coordinates converted to MNI space

    """
    coords = np.atleast_2d(coords)
    xfm = np.array([[1.06860, -0.00396, 0.00826,  1.07816],
                    [0.00640,  1.05741, 0.08566,  1.16824],
                    [-0.01281, -0.08863, 1.10792, -4.17805],
                    [0.00000,  0.00000, 0.00000,  1.00000]])
    mni_coords = np.dot(np.c_[coords, np.ones(coords.shape[0])], xfm.T)[:, :3]
    return mni_coords

def mesh_edges(faces):
    """Returns sparse matrix with edges as an adjacency matrix

    Parameters
    ----------
    faces : array of shape [n_triangles x 3]
        The mesh faces

    Returns
    -------
    edges : sparse matrix
        The adjacency matrix
    """
    npoints = np.max(faces) + 1
    nfaces = len(faces)
    a, b, c = faces.T
    edges = sparse.coo_matrix((np.ones(nfaces), (a, b)),
                              shape=(npoints, npoints))
    edges = edges + sparse.coo_matrix((np.ones(nfaces), (b, c)),
                                      shape=(npoints, npoints))
    edges = edges + sparse.coo_matrix((np.ones(nfaces), (c, a)),
                                      shape=(npoints, npoints))
    edges = edges + edges.T
    edges = edges.tocoo()
    return edges

#def create_color_lut(cmap, n_colors=256):
#    """Return a colormap suitable for setting as a Mayavi LUT.
#
#    Parameters
#    ----------
#    cmap : string, list of colors, n x 3 or n x 4 array
#        Input colormap definition. This can be the name of a matplotlib
#        colormap, a list of valid matplotlib colors, or a suitable
#        mayavi LUT (possibly missing the alpha channel).
#    n_colors : int, optional
#        Number of colors in the resulting LUT. This is ignored if cmap
#        is a 2d array.
#    Returns
#    -------
#    lut : n_colors x 4 integer array
#        Color LUT suitable for passing to mayavi
#    """
#    if isinstance(cmap, np.ndarray):
#        if np.ndim(cmap) == 2:
#            if cmap.shape[1] == 4:
#                # This looks likes a LUT that's ready to go
#                lut = cmap.astype(np.int)
#            elif cmap.shape[1] == 3:
#                # This looks like a LUT, but it's missing the alpha channel
#                alpha = np.ones(len(cmap), np.int) * 255
#                lut = np.c_[cmap, alpha]
#
#            return lut
#
#    # Otherwise, we're going to try and use matplotlib to create it
#
#    if cmap in dir(cm):
#        # This is probably a matplotlib colormap, so build from that
#        # The matplotlib colormaps are a superset of the mayavi colormaps
#        # except for one or two cases (i.e. blue-red, which is a crappy
#        # rainbow colormap and shouldn't be used for anything, although in
#        # its defense it's better than "Jet")
#        cmap = getattr(cm, cmap)
#
#    elif np.iterable(cmap):
#        # This looks like a list of colors? Let's try that.
#        colors = list(map(mpl.colors.colorConverter.to_rgb, cmap))
#        cmap = mpl.colors.LinearSegmentedColormap.from_list("_", colors)
#
#    else:
#        # If we get here, it's a bad input
#        raise ValueError("Input %s was not valid for making a lut" % cmap)
#
#    # Convert from a matplotlib colormap to a lut array
#    lut = (cmap(np.linspace(0, 1, n_colors)) * 255).astype(np.int)
#
#    return lut

#@verbose
#def smoothing_matrix(vertices, adj_mat, smoothing_steps=20, verbose=None):
#    """Create a smoothing matrix which can be used to interpolate data defined
#       for a subset of vertices onto mesh with an adjancency matrix given by
#       adj_mat.
#
#       If smoothing_steps is None, as many smoothing steps are applied until
#       the whole mesh is filled with with non-zeros. Only use this option if
#       the vertices correspond to a subsampled version of the mesh.
#
#    Parameters
#    ----------
#    vertices : 1d array
#        vertex indices
#    adj_mat : sparse matrix
#        N x N adjacency matrix of the full mesh
#    smoothing_steps : int or None
#        number of smoothing steps (Default: 20)
#    verbose : bool, str, int, or None
#        If not None, override default verbose level (see surfer.verbose).
#
#    Returns
#    -------
#    smooth_mat : sparse matrix
#        smoothing matrix with size N x len(vertices)
#    """
#    from scipy import sparse
#
#    logger.info("Updating smoothing matrix, be patient..")
#
#    e = adj_mat.copy()
#    e.data[e.data == 2] = 1
#    n_vertices = e.shape[0]
#    e = e + sparse.eye(n_vertices, n_vertices)
#    idx_use = vertices
#    smooth_mat = 1.0
#    n_iter = smoothing_steps if smoothing_steps is not None else 1000
#    for k in range(n_iter):
#        e_use = e[:, idx_use]
#
#        data1 = e_use * np.ones(len(idx_use))
#        idx_use = np.where(data1)[0]
#        scale_mat = sparse.dia_matrix((1 / data1[idx_use], 0),
#                                      shape=(len(idx_use), len(idx_use)))
#
#        smooth_mat = scale_mat * e_use[idx_use, :] * smooth_mat
#
#        logger.info("Smoothing matrix creation, step %d" % (k + 1))
#        if smoothing_steps is None and len(idx_use) >= n_vertices:
#            break
#
#    # Make sure the smoothing matrix has the right number of rows
#    # and is in COO format
#    smooth_mat = smooth_mat.tocoo()
#    smooth_mat = sparse.coo_matrix((smooth_mat.data,
#                                    (idx_use[smooth_mat.row],
#                                     smooth_mat.col)),
#                                   shape=(n_vertices,
#                                          len(vertices)))
#
#    return smooth_mat

#@verbose
#def coord_to_label(subject_id, coord, label, hemi='lh', n_steps=30,
#                   map_surface='white', coord_as_vert=False, verbose=None):
#    """Create label from MNI coordinate
#
#    Parameters
#    ----------
#    subject_id : string
#        Use if file is in register with subject's orig.mgz
#    coord : numpy array of size 3 | int
#        One coordinate in MNI space or the vertex index.
#    label : str
#        Label name
#    hemi : [lh, rh]
#        Hemisphere target
#    n_steps : int
#        Number of dilation iterations
#    map_surface : str
#        The surface name used to find the closest point
#    coord_as_vert : bool
#        whether the coords parameter should be interpreted as vertex ids
#    verbose : bool, str, int, or None
#        If not None, override default verbose level (see surfer.verbose).
#    """
#    geo = Surface(subject_id, hemi, map_surface)
#    geo.load_geometry()
#
#    if coord_as_vert:
#        coord = geo.coords[coord]
#
#    n_vertices = len(geo.coords)
#    adj_mat = mesh_edges(geo.faces)
#    foci_vtxs = find_closest_vertices(geo.coords, [coord])
#    data = np.zeros(n_vertices)
#    data[foci_vtxs] = 1.
#    smooth_mat = smoothing_matrix(np.arange(n_vertices), adj_mat, 1)
#    for _ in range(n_steps):
#        data = smooth_mat * data
#    idx = np.where(data.ravel() > 0)[0]
#    # Write label
#    label_fname = label + '-' + hemi + '.label'
#    logger.info("Saving label : %s" % label_fname)
#    f = open(label_fname, 'w')
#    f.write('#label at %s from subject %s\n' % (coord, subject_id))
#    f.write('%d\n' % len(idx))
#    for i in idx:
#        x, y, z = geo.coords[i]
#        f.write('%d  %f  %f  %f 0.000000\n' % (i, x, y, z))

def _get_subjects_dir(subjects_dir=None, raise_error=True):
    """Get the subjects directory from parameter or environment variable

    Parameters
    ----------
    subjects_dir : str | None
        The subjects directory.
    raise_error : bool
        If True, raise a ValueError if no value for SUBJECTS_DIR can be found
        or the corresponding directory does not exist.

    Returns
    -------
    subjects_dir : str
        The subjects directory. If the subjects_dir input parameter is not
        None, its value will be returned, otherwise it will be obtained from
        the SUBJECTS_DIR environment variable.
    """
    if subjects_dir is None:
        subjects_dir = os.environ.get("SUBJECTS_DIR", "")
        if not subjects_dir and raise_error:
            raise ValueError('The subjects directory has to be specified '
                             'using the subjects_dir parameter or the '
                             'SUBJECTS_DIR environment variable.')

    if raise_error and not os.path.exists(subjects_dir):
        raise ValueError('The subjects directory %s does not exist.'
                         % subjects_dir)

    return subjects_dir

def has_fsaverage(subjects_dir=None):
    """Determine whether the user has a usable fsaverage"""
    fs_dir = op.join(_get_subjects_dir(subjects_dir, False), 'fsaverage')
    if not op.isdir(fs_dir):
        return False
    if not op.isdir(op.join(fs_dir, 'surf')):
        return False
    return True

requires_fsaverage = np.testing.dec.skipif(not has_fsaverage(),
                                           'Requires fsaverage subject data')

#def has_ffmpeg():
#    """Test whether the FFmpeg is available in a subprocess
#
#    Returns
#    -------
#    ffmpeg_exists : bool
#        True if FFmpeg can be successfully called, False otherwise.
#    """
#    try:
#        subprocess.call(["ffmpeg"], stdout=subprocess.PIPE,
#                        stderr=subprocess.PIPE)
#        return True
#    except OSError:
#        return False
#
#def assert_ffmpeg_is_available():
#    "Raise a RuntimeError if FFmpeg is not in the PATH"
#    if not has_ffmpeg():
#        err = ("FFmpeg is not in the path and is needed for saving "
#               "movies. Install FFmpeg and try again. It can be "
#               "downlaoded from http://ffmpeg.org/download.html.")
#        raise RuntimeError(err)
#
#requires_ffmpeg = np.testing.dec.skipif(not has_ffmpeg(), 'Requires FFmpeg')
#
#def ffmpeg(dst, frame_path, framerate=24, codec='mpeg4', bitrate='1M'):
#    """Run FFmpeg in a subprocess to convert an image sequence into a movie
#
#    Parameters
#    ----------
#    dst : str
#        Destination path. If the extension is not ".mov" or ".avi", ".mov" is
#        added. If the file already exists it is overwritten.
#    frame_path : str
#        Path to the source frames (with a frame number field like '%04d').
#    framerate : float
#        Framerate of the movie (frames per second, default 24).
#    codec : str | None
#        Codec to use (default 'mpeg4'). If None, the codec argument is not
#        forwarded to ffmpeg, which preserves compatibility with very old
#        versions of ffmpeg
#    bitrate : str | float
#        Bitrate to use to encode movie. Can be specified as number (e.g.
#        64000) or string (e.g. '64k'). Default value is 1M
#
#    Notes
#    -----
#    Requires FFmpeg to be in the path. FFmpeg can be downlaoded from `here
#    <http://ffmpeg.org/download.html>`_. Stdout and stderr are written to the
#    logger. If the movie file is not created, a RuntimeError is raised.
#    """
#    assert_ffmpeg_is_available()
#
#    # find target path
#    dst = os.path.expanduser(dst)
#    dst = os.path.abspath(dst)
#    root, ext = os.path.splitext(dst)
#    dirname = os.path.dirname(dst)
#    if ext not in ['.mov', '.avi']:
#        dst += '.mov'
#
#    if os.path.exists(dst):
#        os.remove(dst)
#    elif not os.path.exists(dirname):
#        os.mkdir(dirname)
#
#    frame_dir, frame_fmt = os.path.split(frame_path)
#
#    # make the movie
#    cmd = ['ffmpeg', '-i', frame_fmt, '-r', str(framerate),
#           '-b:v', str(bitrate)]
#    if codec is not None:
#        cmd += ['-c', codec]
#    cmd += [dst]
#    logger.info("Running FFmpeg with command: %s", ' '.join(cmd))
#    sp = subprocess.Popen(cmd, cwd=frame_dir, stdout=subprocess.PIPE,
#                          stderr=subprocess.PIPE)
#
#    # log stdout and stderr
#    stdout, stderr = sp.communicate()
#    std_info = os.linesep.join(("FFmpeg stdout", '=' * 25, stdout))
#    logger.info(std_info)
#    if stderr.strip():
#        err_info = os.linesep.join(("FFmpeg stderr", '=' * 27, stderr))
#        # FFmpeg prints to stderr in the absence of an error
#        logger.info(err_info)
#
#    # check that movie file is created
#    if not os.path.exists(dst):
#        err = ("FFmpeg failed, no file created; see log for more more "
#               "information.")
#        raise RuntimeError(err)

