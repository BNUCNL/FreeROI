# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nibabel.affines import apply_affine
from math import floor
import numpy as np

def save2csv(data, csv_file):
    """
    Save a 1/2D list data into a csv file.

    """
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
    """
    Save a np array into a csv file.

    """
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
        raise valueError, "Input must be a numpy array."

def get_cord_from_file(data, cord_filepath, image_affine):
        """
        Return all cordinate from txt the txt file.

        """
        cord_file = open(cord_filepath, 'r')
        all_cords = []
        value_list = []
        shape = data.shape
        import numpy as np
        new_data = np.zeros_like(data)

        line = cord_file.readline()
        while line:
            try:
                cord = "".join(line.split()).split(',')
                if len(cord) != 3:
                    raise ValueError('The cordinate ' + line.rstrip('\t\n') + ' can only be three dimension!')
                new_cord = list(float(i) for i in cord)
                new_cord = apply_affine(np.linalg.inv(image_affine), new_cord)
                new_cord = list(int(i) for i in new_cord)

                all_cords.append(new_cord)
                if (new_cord[0] < 0 or new_cord[0] >= shape[0]) or \
                   (new_cord[1] < 0 or new_cord[1] >= shape[1]) or \
                   (new_cord[2] < 0 or new_cord[2] >= shape[2]):
                    raise ValueError('The cordinate ' + line.rstrip('\t\n') + ' out of bounds.')
                else:
                    value = data[new_cord[0], new_cord[1], new_cord[2]]
                    value_list.append(value)
                    new_data[new_cord[0], new_cord[1], new_cord[2]] = value
            except:
                raise ValueError('The cordinate ' + line.rstrip('\t\n') + ' error!')
            line = cord_file.readline()

        cord_file.close()

        return all_cords, value_list, new_data

