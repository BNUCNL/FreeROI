# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import json
import collections

from PyQt4.QtGui import *

class LabelConfig(object):
    defalut_color = QColor(255, 0, 0)

    def __init__(self, filepath, is_global=True):
        self.filepath = filepath
        self.name = os.path.basename(filepath).split('.')[0]
        self.label_index = collections.OrderedDict()
        self.label_color = {}
        self.label_list = []
        self.load(filepath)
        #with open(filepath, 'r') as f:
        #    try:
        #        tmp_dict = json.load(f, object_pairs_hook=collections.OrderedDict)
        #    except ValueError:
        #        tmp_dict = collections.OrderedDict()
        #    for key, val in tmp_dict.iteritems():
        #        self.label_list.append(key)
        #        if not val:
        #            self.label_index[key] = 0
        #        else:
        #            self.label_index[key] = int(val[0])
        #        if len(val) < 2:
        #            self.label_color[key] = default_color
        #        else:
        #            self.label_color[key] = QColor(val[1])
        self._is_global = is_global

    def load(self, filepath):
        tmp_dict = collections.OrderedDict()
        with open(filepath, 'r') as f:
            for line in f:
                line = line.split()
                self.label_index[line[1]] = int(line[0])
                self.label_color[line[1]] = QColor(int(line[2]), int(line[3]), int(line[4]))
        return tmp_dict

    def dump(self):
        if hasattr(self, 'filepath'):
            with open(self.filepath, 'w') as f:
                for label in self.label_index:
                    color = self.label_color[label]
                    f.write('%3d\t%-25s\t%3d %3d %3d\n' % (self.label_index[label], label, color.red(), color.green(), color.blue()))

    def new_index(self):
        if self.label_index:
            return max(self.label_index.values()) + 1
        else:
            return 1

    def add_label(self, label, index=None, color=None):
        if index is None:
            index = self.new_index()
        if color is None:
            color = default_color
        if self.has_index(index):
            raise ValueError, 'Index already exists, choose another one'
        self.label_index[label] = index
        self.label_color[label] = color

    def remove_label(self, label):
        if self.has_label(label):
            del self.label_index[label]
            del self.label_color[label]

    def has_label(self, label):
        return label in self.label_index.keys()

    def has_index(self, index):
        return index in self.label_index.values()

    def get_label_list(self):
        return self.label_index.keys()

    def get_label_index(self, label):
        if label:
            if self.has_label(label):
                return self.label_index[label]

    def get_index_label(self, index):
        for label, ind in self.label_index.iteritems():
            if ind == index:
                return label
        return ''

    def get_label_color(self, label):
        if label:
            if self.has_label(label):
                return self.label_color[label]

    def update_label_color(self, label, color):
        if self.has_label(label):
            self.label_color[label] = color

    def save(self):
        self.dump()
        #colors = map(QColor.rgb, self.label_color.values())
        #tmp_dict = dict(zip(self.label_index.keys(), 
        #                    zip(self.label_index.values(), colors)))
        #with open(self.filepath, 'w') as f:
        #    json.dump(tmp_dict, f, indent=4)

    def get_colormap(self):
        rgb = lambda color: [color.red(), color.green(), color.blue()]
        return dict([(self.label_index[label], rgb(self.label_color[label])) for
                     label in self.label_index.keys()])

    def __str__(self):
        return str(self.label_index.keys())

    def get_name(self):
        return self.name
    
    @property
    def is_global(self):
        return self._is_global

    def get_label_index_pair(self):
        return list(self.label_index.iteritems())
