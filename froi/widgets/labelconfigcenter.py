# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from drawsettings import DrawSettings


# class ConfigLabelModel(QAbstractListModel):
#     """
#     Model for label config list view.
#
#     """
#
#     def __init__(self, label_config, parent=None):
#         super(ConfigLabelModel, self).__init__()
#         self._label_config = label_config
#         self._label_index = label_config.get_label_index_pair()
#
#     def rowCount(self, parent=QModelIndex()):
#         """
#         Return the item numbers in the list.
#
#         """
#         return len(self._label_index)
#
#     def data(self, index, role):
#         if not index.isValid() or not 0 <= index.row() < self.rowCount():
#             return QString()
#         row = index.row()
#         if role == Qt.DisplayRole or role == Qt.EditRole:
#             return str(self._label_index[row][1]) + ' ' + self._label_index[row][0]
#         if role == Qt.UserRole:
#             return self._label_index[row][0]
#
#     def insertRow(self, index_row, index, label):
#         self._label_index.append((label, index))
#         self.dataChanged.emit(index_row, index_row)
#
#     def removeRow(self, index):
#         del self._label_index[index.row()]
#         self.dataChanged.emit(index, index)
#
#     def editRow(self, index, label):
#         current_index = self._label_index[index.row()][1]
#         del self._label_index[index.row()]
#         self._label_index.insert(index.row(), (label, current_index))
#         self.dataChanged.emit(index, index)


class LabelConfigCenter(QGroupBox, DrawSettings):
    """A Qwidget for label config chooser."""
    single_roi_view_update = pyqtSignal()
    single_roi_view_update_for_model = pyqtSignal()

    def __init__(self, label_configs, list_view_model, label_models, is_roi_edit=False, parent=None):
        super(LabelConfigCenter, self).__init__()
        # self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        self.label_configs = label_configs
        self._label_models = label_models
        self._list_view_model = list_view_model

        # self.models = map(ConfigLabelModel, label_configs)
        # self.config_names = [x.get_name() for x in self.label_configs]
        # self.config_names.insert(0, 'None')
        self._is_roi_edit = is_roi_edit

        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Tool)
        self._init_gui()
        self._create_actions()

    def get_default_label_config(self):
        return self.label_configs[0]

    def _init_gui(self):
        """Initialize GUI."""
        self.config_combobox = QComboBox()
        self.config_combobox.setModel(self._list_view_model)
        # self.config_combobox.addItems(self.config_names)
        self.null_model = QStringListModel()

        self.label_list_view = QListView()
        self._update_labels()

        self.size_label = QLabel('Brush Size:')
        self.size_edit = QSpinBox()
       
        hboxlayout = QHBoxLayout()
        hboxlayout.addWidget(self.size_label)
        hboxlayout.addWidget(self.size_edit)

        labcon_layout = QGridLayout()
        labcon_layout.addWidget(self.config_combobox)
        labcon_layout.addWidget(self.label_list_view)
        labcon_layout.addLayout(hboxlayout, 2, 0)
        self.setLayout(labcon_layout)

    def _update_labels(self):
        idx = self.config_combobox.currentIndex()
        if idx >= 0:
            self.label_list_view.setModel(self._label_models[idx])
        else:
            self.label_list_view.setModel(self.null_model)
        # else:
        #     self.label_list_view.setModel(self.models[idx-1])
        #     self.label_list_view.setCurrentIndex(
        #                     self.models[idx-1].createIndex(0,0))
        #     self.label_list_view.selectionModel().currentChanged.connect(
        #                     self.single_roi_view_update)

    def _create_actions(self):
        self.config_combobox.currentIndexChanged.connect(self._update_labels)
        self.config_combobox.currentIndexChanged.connect(
                                    self.single_roi_view_update)
        self.label_list_view.selectionModel().currentChanged.connect(
                                    self.single_roi_view_update)

    def label_config_changed_signal(self):
        return self.config_combobox.currentIndexChanged

    def is_brush(self):
        return True

    def set_is_roi_edit(self, is_roi_edit=False):
        self._is_roi_edit = is_roi_edit
    
    # For DrawSettings
    def is_roi_tool(self):
        return self._is_roi_edit

    def is_drawing_valid(self):
        return self.config_combobox.currentIndex() >= 0

    def get_current_list_view_index(self):
        idx = self.config_combobox.currentIndex()
        if idx < 0:
            return None
        return self.label_list_view.currentIndex()

    def get_drawing_value(self):
        idx = self.config_combobox.currentIndex()
        if idx < 0:
            raise ValueError, 'Label Config Invalid'
        current_label_config = self.label_configs[idx]
        index = self.label_list_view.currentIndex()
        # label = self.label_list_view.model().data(index, Qt.UserRole)
        return current_label_config.get_index_list()[index.row()]

    def get_drawing_size(self):
        if not self.is_drawing_valid():
            raise ValueError, 'Label Config Invalid'
        return self.size_edit.value()

    def get_drawing_color(self):
        idx = self.config_combobox.currentIndex()
        if idx < 0:
            raise ValueError, 'Label Config Invalid'
        current_label_config = self.label_configs[idx]
        index = self.label_list_view.currentIndex()
        # label = self.label_list_view.model().data(index, Qt.UserRole)
        index = current_label_config.get_index_list()[index.row()]

        return current_label_config.get_label_color(current_label_config.get_index_label(index))

    def get_all_labelconfig_names(self):
        self.config_names = [x.get_name() for x in self.label_configs]
        # self.config_names.insert(0, 'None')

        return self.config_names[:]

    def get_first_label_config(self):
        if len(self.label_configs) < 1:
            return None
        return self.label_configs[0]

    def get_label_config(self, offset):
        if offset >= len(self.label_configs):
            raise ValueError, "Not Enough Label Config Files"
        return self.label_configs[offset]

    def get_label_config_by_name(self, name):
        if len(self.label_configs) < 1:
            raise ValueError, "Not Enough Label Config files"
        for label_config in self.label_configs:
            if label_config.get_name() == name:
                return label_config

    def get_current_label_config(self):
        if self.is_drawing_valid():
            if self.config_combobox.currentIndex() < 0:
                return None
            else:
                return self.label_configs[self.config_combobox.currentIndex()]

    def get_current_index_label(self, value):
        if not self.is_drawing_valid():
            # return QString()
            return str()
        return self.get_current_label_config().get_index_label(value)

    def get_current_label_index(self, label):
        if not self.is_drawing_valid():
            # return QString()
            return str()
        return self.get_current_label_config().get_label_index(label)

    def has_current_label(self, label):
        return label in self.get_all_labelconfig_names()

    def has_current_index(self, index):
        return index in self.get_current_label_config().label_index.values()

    def get_current_label_list(self):
        return self.get_all_labelconfig_names()

    def add_current_label(self, label, index=None, color=None):
        if index is None:
            index = self.new_index()
        if color is None:
            color = self.default_color()
        if self.has_current_index(index):
            raise ValueError, 'Index already exists, choose another one'
        if self.has_current_label(label):
            raise ValueError, 'Label Name already exists, choose another one'
        self.get_current_label_config().label_index[label] = index
        self.get_current_label_config().label_color[label] = color

    def get_current_label_color(self, label):
        if label:
            if self.has_current_label(label):
                return self.get_current_label_config().label_color[label]

    def current_save(self):
        self.get_current_label_config().save()

    def remove_current_label(self, label):
        if self.has_current_label(label):
            del self.get_current_label_config().label_index[label]
            del self.get_current_label_config().label_color[label]