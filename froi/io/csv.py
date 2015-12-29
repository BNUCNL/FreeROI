# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nibabel.affines import apply_affine
import numpy as np
import re

def save2csv(data, csv_file):
    """Save a 1/2D list data into a csv file."""
    if isinstance(data, list):
        try:
            f = open(csv_file, 'w')
        except IOError:
            print "Can not save file " + csv_file
        else:
            for line in data:
                if isinstance(line, list):
                    line_str = [str(item) for item in line]
                    line_str = ','.join(line_str)
                else:
                    line_str = str(line)
                f.write(line_str + '\n')
            f.close()
    else:
        raise ValueError, "Input must be a list."

def nparray2csv(data, labels=None, csv_file=None):
    """Save a np array into a csv file."""
    if isinstance(data, np.ndarray):
        try:
            f = open(csv_file, 'w')
        except IOError:
            print "Can not save file " + csv_file
        else:
            if isinstance(labels, list):
                labels = [str(item) for item in labels]
                labels = ','.join(labels)
                f.write(labels + '\n')
            for line in data:
                line_str = [str(item) for item in line]
                line_str = ','.join(line_str)
                f.write(line_str + '\n')
            f.close()
    else:
        raise ValueError, "Input must be a numpy array."

def get_cord_from_file(header, cord_filepath, image_affine):
        """Return all cordinate from the txt or csv file."""
        shape = header.get_data_shape()
        voxel_size = header.get_zooms()


        cord_file = open(cord_filepath, 'r')
        all_cords = []
        all_roi_id = []
        all_roi_radius = []

        line = cord_file.readline()
        while line:
            try:
                cord = line.replace('\r\n', '').split('\t')
                if len(cord) != 5:
                    raise ValueError('The cordinate ' + line.rstrip('\t\n') + ' can only be three dimension!')
                roi_id = int(cord[0])
                new_cord = list(float(i) for i in cord[1:4])
                new_cord = apply_affine(np.linalg.inv(image_affine), new_cord)
                new_cord = list(int(i) for i in new_cord)
                radius = int(cord[4])
                all_roi_radius.append([int(radius * 1. / voxel_size[0]),
                                      int(radius * 1. / voxel_size[1]),
                                      int(radius * 1. / voxel_size[2])])

                all_cords.append(new_cord)
                if (new_cord[0] < 0 or new_cord[0] >= shape[0]) or \
                   (new_cord[1] < 0 or new_cord[1] >= shape[1]) or \
                   (new_cord[2] < 0 or new_cord[2] >= shape[2]):
                    raise ValueError('The cordinate ' + line.rstrip('\t\n') + ' out of bounds.')
                else:
                    all_roi_id.append(roi_id)
            except:
                raise ValueError('The cordinate ' + line.rstrip('\t\n') + ' error!')
            line = cord_file.readline()

        cord_file.close()

        return all_cords, all_roi_radius, all_roi_id

