# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtGui import *

from froi.utils import get_data_dir
from froi.utils import get_file_names
from froi.interface.xml_api import get_info
from froi.interface.atlas_api import *


def get_atlas_names():
    """
    Get atlas name which is equal to xml names.
    """
    tar_path = os.path.join(get_data_dir(), 'atlas')
    xml_names = get_file_names(tar_path,'.xml')
    return xml_names

def get_atlas_data(xml_name):
    """
    Get atlas nii data.
    """
    tar_path = os.path.join(get_data_dir(), 'atlas')
    nii_name = get_info(os.path.join(tar_path, xml_name), 'imagefile')
    nii_data = get_nii_data(tar_path, nii_name[0])
    return nii_data

def get_label_info(xml_name):
    """
    Get atlas label information.
    """
    tar_path = os.path.join(get_data_dir(), 'atlas')
    label_list = get_info(os.path.join(tar_path, xml_name), 'label')
    return label_list


class AtlasDialog(QDialog):
    """
    A dialog for action of Atlas.
    """
    default_atlas = ['Harvard-Oxford_Cortical_Structural_Atlas.xml', \
                     'Harvard-Oxford_Subcortical_Structural_Atlas.xml']
    def __init__(self, model, parent=None):
        super(AtlasDialog, self).__init__(parent)
        self._model = model
        self.xml_names = get_atlas_names()
        self.nii_data, self.label_list=[],[]
        self._init_gui()
        self._create_actions()

    def atlas_display(self, data, label):
        """
        The layout of a single atlas prob information.
        """
        xyz = self._model.get_cross_pos()
        prob_list = get_atlasprob(data, xyz[0], xyz[1], xyz[2])
        display = sorting(label, prob_list)
        return display

    def _init_gui(self):
        """
        Initialize GUI.
        """
        # set dialog title
        self.setWindowTitle("Candidate Label")

        # initialize widgets
        # self.source_combo = QComboBox()
        vbox_layout = QVBoxLayout()
        self.scrollContents = QWidget()
        self.Layout_2 = QHBoxLayout(self.scrollContents)
        self.Layout_2.addLayout(vbox_layout)

        self.label,self.prob = list(),list()
        for i in range(len(self.xml_names)):
            self.label.append(QLabel())
            self.prob.append(QLabel())
            self.nii_data.append(0)
            self.label_list.append(0)

        for i in range(len(self.xml_names)):
            self.label[i].setText(self.xml_names[i].split('.')[0])
            self.label[i].setFont(QFont("Roman times", 10, QFont.Bold))
            vbox_layout.addWidget(self.label[i])
            vbox_layout.addWidget(self.prob[i])
            if (self.xml_names[i] in self.default_atlas):
                self.nii_data[i] = get_atlas_data(self.xml_names[i])
                self.label_list[i] = get_label_info(self.xml_names[i])
                atlas_prob = self.atlas_display(self.nii_data[i], self.label_list[i])
                self.prob[i].setText(atlas_prob)
            else:
                self.label[i].setVisible(False)
                self.prob[i].setVisible(False)

        self.Layout1=QVBoxLayout(self)
        self.scrollArea=QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollContents)
        self.Layout1.addWidget(self.scrollArea)
        self.setGeometry(300,260,300,260)

        self.space = QLabel(" ")
        self.set_button = QPushButton("Select Atlas")
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.space,0,0)
        grid_layout.addWidget(self.set_button,0,1)
        self.Layout1.addLayout(grid_layout)
        self.setLayout(self.Layout1)

    def _create_actions(self):
        """
        Create actions for button and cross_changed
        """
        self.set_button.clicked.connect(self._set_dialog)
        self._model.cross_pos_changed.connect(self._update_prob)

    def _update_prob(self):
        """
        Update atlas probability values
        """
        for i in range(len(self.xml_names)):
            if (self.label_list[i]!=0):
                atlas_prob = self.atlas_display(self.nii_data[i], self.label_list[i])
                self.prob[i].setText(atlas_prob)

    def _set_dialog(self):
        """
        Setting clicked
        """
        self.stat=list()
        for i in range(len(self.xml_names)):
            self.stat.append(self.prob[i].isVisible())
        new_dialog = SettingDialog(self.stat)
        new_dialog.exec_()
        self.status = new_dialog._get_checkbox_status()

        for i in range(len(self.xml_names)):
            if (self.status[i]):
                self.label[i].setVisible(True)
                self.prob[i].setVisible(True)
                if not self.label_list[i]:
                    self.nii_data[i] = get_atlas_data(self.xml_names[i])
                    self.label_list[i] = get_label_info(self.xml_names[i])
                    atlas_prob = self.atlas_display(self.nii_data[i], self.label_list[i])
                    self.prob[i].setText(atlas_prob)
            else:
                self.label[i].setVisible(False)
                self.prob[i].setVisible(False)

    def _get_setting_status(self):
        """
        Get setting status.
        """
        return self.status


class SettingDialog(QDialog):
    """
    A dialog for setting button.
    """
    def __init__(self, stat, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.stat= stat
        self.xml_names = get_atlas_names()
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.
        """
        self.label,self.check=list(),list()
        for i in range(len(self.xml_names)):
            self.label.append(QLabel())
            self.check.append(QCheckBox())

        self.setWindowTitle("Atlas Selection")

        self.scrollContents = QWidget()
        self.Layout_2 = QHBoxLayout(self.scrollContents)
        grid_layout = QGridLayout()
        self.Layout_2.addLayout(grid_layout)

        for i in range(len(self.xml_names)):
            self.label[i].setText(self.xml_names[i].split('.')[0])
            if self.stat[i]:
                self.check[i].setChecked(True)
            else:
                self.check[i].setChecked(False)
            grid_layout.addWidget(self.check[i], i,0)
            grid_layout.addWidget(self.label[i],i,1)

        self.Layout1=QVBoxLayout(self)
        self.scrollArea=QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollContents)
        self.Layout1.addWidget(self.scrollArea)
        self.setGeometry(300,260,250,280)

        self.save_button = QPushButton("OK")
        self.Layout1.addWidget(self.save_button)
        self.setLayout(self.Layout1)

    def _create_actions(self):
        """Create actions for the button."""
        self.save_button.clicked.connect(self._save)

    def _save(self):
        """Actions for save button."""
        self.stat=[]
        for i in range(len(self.xml_names)):
            self.stat.append(self.check[i].isChecked())
        self.close()

    #def _update_checkbox_status(self):
    #    """Update checkbox status."""
    #    for i in range(len(self.stat)):
    #        if self.stat[i]:
    #            self.check[i].setChecked(True)
    #        else:
    #            self.check[i].setChecked(False)

    def _get_checkbox_status(self):
        """Get checkbox status."""
        return self.stat
