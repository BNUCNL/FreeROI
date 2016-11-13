# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import collections

from PyQt4.QtGui import *


class LabelConfig(object):
    """Mainly to config the labels."""
    defalut_color = QColor(255, 0, 0)

    def __init__(self, filepath, is_global=True):
        """Init the related label data."""
        self.filepath = filepath
        self.name = os.path.basename(filepath).split('.')[0]
        self.label_index = collections.OrderedDict()
        self.label_color = {}
        self.label_list = []
        self.load(filepath)
        self._is_global = is_global

    def load(self, filepath):
        """Load label data from the filepath."""
        try:
            f = open(filepath, 'r+')
        except IOError, e:
            if e.errno == 13:
                f = open(filepath, 'r')
            else:
                f = None
                print e
        if f:
            for line in f:
                line = line.split()
                if line:
                    self.label_index[line[1]] = int(line[0])
                    self.label_color[line[1]] = QColor(int(line[2]),
                                                       int(line[3]),
                                                       int(line[4]))
            f.close()

    def dump(self):
        """Dump the label config info to the disk."""
        if hasattr(self, 'filepath'):
            with open(self.filepath, 'w') as f:
                for label in self.label_index:
                    color = self.label_color[label]
                    f.write('%3d\t%-25s\t%3d %3d %3d\n' % (self.label_index[label], label, color.red(), color.green(), color.blue()))

    def get_filepath(self):
        """Return the label filepath."""
        return self.filepath

    def new_index(self):
        """ Create the new label index."""
        if self.label_index:
            return max(self.label_index.values()) + 1
        else:
            return 1

    def default_color(self):
        """Return the default label color."""
        return QColor(255, 0, 0)

    def add_label(self, label, index=None, color=None):
        """Add a new label."""
        if index is None:
            index = self.new_index()
        if color is None:
            color = self.default_color()
        if self.has_index(index):
            raise ValueError, 'Index already exists, choose another one'
        self.label_index[label] = index
        self.label_color[label] = color

    def remove_label(self, label):
        """Remove the given label."""
        if self.has_label(label):
            del self.label_index[label]
            del self.label_color[label]

    def edit_label(self, old_label, label, color):
        """Edit the given label."""
        if self.has_label(old_label):
            self.label_index[label] = self.get_label_index(old_label)
            self.label_color[label] = color
            if old_label != label:
                del self.label_index[old_label]

    def has_label(self, label):
        """Check if the current label config contains the given label."""
        return label in self.label_index.keys()

    def has_index(self, index):
        """Check if the current label config contains the given index."""
        return index in self.label_index.values()

    def get_label_list(self):
        """Return all labels in the current label config."""
        return self.label_index.keys()

    def get_index_list(self):
        """Return all indexes in the current label config."""
        return sorted(self.label_index.values())

    def get_label_index(self, label):
        """Return the index of the given label."""
        if label:
            if self.has_label(label):
                return self.label_index[label]

    def get_index_label(self, index):
        """Return the label of the given index."""
        for label, ind in self.label_index.iteritems():
            if ind == index:
                return label
        return ''

    def get_label_color(self, label):
        """Return the color of the given label."""
        if label:
            if self.has_label(label):
                return self.label_color[label]

    def update_label_color(self, label, color):
        """Update the color of the given label to the given color."""
        if self.has_label(label):
            self.label_color[label] = color

    def save(self):
        """Save the label config info to the disk."""
        self.dump()

    def get_colormap(self):
        """Return the colormap."""
        rgb = lambda color: [color.red(), color.green(), color.blue()]
        return dict([(self.label_index[label], rgb(self.label_color[label])) for
                     label in self.label_index.keys()])

    def __str__(self):
        """Override the __str__ method to get all labels."""
        return str(self.label_index.keys())

    def get_name(self):
        """Get the name which the current label belongs to."""
        return self.name
    
    @property
    def is_global(self):
        """Return whether the current label config is global."""
        return self._is_global

    def get_label_index_pair(self):
        """Return all labels and indexed in pairs."""
        return list(self.label_index.iteritems())
