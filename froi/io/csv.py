# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

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

