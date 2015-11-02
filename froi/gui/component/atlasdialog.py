# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtGui import *
from froi.io.xml_api import *
from froi.io.atlas_api import *

parent_path = os.path.dirname(os.getcwd())
tar_path = parent_path+'/froi/data/atlas/'
xml_names = get_file_name(tar_path,'.xml')                 #get the xml file name automatically
nii_names = get_info(tar_path,xml_names,'imagefile')       #get nii file names
nii_data = get_nii_data(tar_path, nii_names)               #get nii data
label_list = get_info(tar_path, xml_names, 'label')        #get label list


class AtlasDialog(QDialog):
    """
    A dialog for action of Atlas.

    """
    def __init__(self, model, parent=None):
        super(AtlasDialog, self).__init__(parent)
        self._model = model
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
        self.setWindowTitle("Probability Information")

        # initialize widgets
        self.source_combo = QComboBox()
        vbox_layout = QVBoxLayout()
        self.label,self.prob = list(),list()
        for i in range(len(xml_names)):
            self.label.append(QLabel())
            self.prob.append(QLabel())

        for i in range(len(xml_names)):
            self.label[i].setText(xml_names[i].split('.')[0])
            self.label[i].setFont(QFont("Roman times", 10, QFont.Bold))
            layout = self.atlas_display(nii_data[i], label_list[i])
            self.prob[i].setText(layout)
            vbox_layout.addWidget(self.label[i])
            vbox_layout.addWidget(self.prob[i])

        self.space = QLabel(" ")
        self.set_button = QPushButton("Setting")
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.space,0,0)
        grid_layout.addWidget(self.set_button,0,1)
        vbox_layout.addLayout(grid_layout)
        self.setLayout(vbox_layout)

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
        for i in range(len(xml_names)):
            layout = self.atlas_display(nii_data[i], label_list[i])
            self.prob[i].setText(layout)

    def _set_dialog(self):
        """
        Setting clicked
        """
        self.stat=list()
        for i in range(len(xml_names)):
            self.stat.append(self.prob[i].isVisible())
        if self.set_button.isEnabled():
            new_dialog = SettingDialog(self.stat)
            new_dialog.exec_()
            self.status = new_dialog._get_checkbox_status()
            if self.status != []:
                for i in range(len(xml_names)):
                    if self.status[i]:
                        self.label[i].setVisible(True)
                        self.prob[i].setVisible(True)
                    else:
                        self.label[i].setVisible(False)
                        self.prob[i].setVisible(False)

    def _get_setting_status(self):
        """
        Get setting status.

        """
        return self.status


class signal():
    """
    A base class for setting dialog.

    """
    def __init__(self, signal):
        self.signal = signal


class SettingDialog(QDialog, signal):
    """
    A dialog for setting button.

    """
    def __init__(self, stat, parent=None):
        super(SettingDialog, self).__init__(parent)
        self.stat= stat
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.label,self.check=list(),list()
        for i in range(len(xml_names)):
            self.label.append(QLabel())
            self.check.append(QCheckBox())

        self.setWindowTitle("Atlas Selection")
        grid_layout = QGridLayout()

        for i in range(len(xml_names)):
            self.label[i].setText(xml_names[i].split('.')[0])
            if self.stat[i]:
                self.check[i].setChecked(True)
            else:
                self.check[i].setChecked(False)
            grid_layout.addWidget(self.check[i], i,0)
            grid_layout.addWidget(self.label[i],i,1)

        ver_layout = QVBoxLayout()
        ver_layout.addLayout(grid_layout)
        self.save_button = QPushButton("OK")
        ver_layout.addWidget(self.save_button)
        self.setLayout(ver_layout)

    def _create_actions(self):
        """
        Create actions for the button

        """
        self.save_button.clicked.connect(self._save)

    def _save(self):
        """
        Actions for save button.

        """
        self.stat=[]
        for i in range(len(xml_names)):
            self.stat.append(self.check[i].isChecked())
        self.close()

    def _update_checkbox_status(self):
        """
        Update checkbox status.

        """
        for i in range(len(self.stat)):
            if self.stat[i]:
                self.check[i].setChecked(True)
            else:
                self.check[i].setChecked(False)

    def _get_checkbox_status(self):
        """
        Get checkbox status.

        """
        return self.stat
