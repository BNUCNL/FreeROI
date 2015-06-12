# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import sys
from PyQt4.QtGui import *
from froi.io.xml_api import *


def atlas_display(self, atlas_name, niftil_path, xml_path):
    """
    The layout display for a single atlas information.

    Parameters
    ----------
    atlas_name:
        The atlas name for display with bold font.
    niftil_path:
        The path of niftil file which including the niftil file name.
    xml_path:
        The path of xml file which including the xml file name.

    """
    xyz = self._model.get_cross_pos()

    atlas_label = QLabel(atlas_name)
    atlas_label.setFont(QFont("Roman times", 10, QFont.Bold))

    prob_label = QLabel()
    prob_list = extract_atlasprob(niftil_path, xyz[0], xyz[1], xyz[2])
    label_list = get_info(xml_path, 'label')
    display = sorting(label_list, prob_list)
    prob_label.setText(display)

    vbox_layout = QVBoxLayout()
    vbox_layout.addWidget(atlas_label)
    vbox_layout.addWidget(prob_label)
    return vbox_layout

class SettingDialog(QDialog):
    """
    A dialog for setting button.

    """
    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.setWindowTitle("Atlas Selection")
        self.subcor_label = QLabel('Harvard-Oxford SubCortical Atlas')
        self.cor_label = QLabel('Harvard-Oxford Cortical Atlas')
        self.subcor_checkbox = QCheckBox()
        self.subcor_checkbox.setChecked(True)
        self.cor_checkbox = QCheckBox()
        self.cor_checkbox.setChecked(False)
        dialog_layout = QGridLayout()
        dialog_layout.addWidget(self.subcor_checkbox, 0,0)
        dialog_layout.addWidget(self.subcor_label,0,1)
        dialog_layout.addWidget(self.cor_checkbox,1,0)
        dialog_layout.addWidget(self.cor_label,1,1)
        self.setLayout(dialog_layout)

    def _create_actions(self):
        pass




class HOsubcorticalDialog(QDialog):
    """
    A dialog for action of Harvard-Oxford SubCortical Atlas.

    """
    def __init__(self, model, main_win, parent=None):
        super(HOsubcorticalDialog, self).__init__(parent)
        self._model = model
        self._main_win = main_win
        self._init_gui()
        self._create_actions()


    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Atlas Information")
        parent_path = os.path.dirname(os.getcwd())
        tar_path = parent_path+'/froi/data/atlas/'

        # initialize widgets
        self.source_combo = QComboBox()
        layout1 = atlas_display(self, 'Harvard-Oxford SubCortical Structural Atlas',\
                                tar_path+'HarvardOxford-sub-prob-2mm.nii.gz', tar_path+'HarvardOxford-Subcortical.xml')
        layout2 = atlas_display(self, 'Harvard-Oxford Cortical Structural Atlas', \
                                tar_path+'HarvardOxford-cort-prob-2mm.nii.gz', tar_path+'HarvardOxford-Cortical.xml')

        self.help_button = QPushButton("Help")
        self.set_button = QPushButton("Setting")
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.help_button,0,0)
        grid_layout.addWidget(self.set_button,0,1)

        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(layout1)
        vbox_layout.addLayout(layout2)
        vbox_layout.addLayout(grid_layout)

        self.setLayout(vbox_layout)


    def _create_actions(self):
        """
        Create actions about the button
        """
        self.help_button.clicked.connect(self._help_dialog)
        self.set_button.clicked.connect(self._set_dialog)


    def _set_dialog(self):
        '''
        Setting clicked
        '''
        if self.set_button.isEnabled():
            new_dialog = SettingDialog()
            new_dialog.exec_()


    def _help_dialog(self):
        """
        Help dialog.

        """
        QMessageBox.about(self, self.tr("Helps"),
                      self.tr("<p>There exist two atlas: <br/>"
                              "Harvard-Oxford SubCortical Atlas, <br/>"
                              "Harvard-Oxford Cortical Atlas</p>"
                              "<p>You can click the Setting button "
                              "to choose which atlas to show.</p>"))