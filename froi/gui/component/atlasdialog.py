# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from froi.io.xml_api import *


class AtlasDialog(QDialog):
    """
    A dialog for action of Harvard-Oxford Cortical Atlas.

    """
    def __init__(self, model, main_win, parent=None):
        super(AtlasDialog, self).__init__(parent)
        self._model = model
        self._main_win = main_win
        self._init_gui()
        self._create_actions()

    def atlas_display(self, niftil_path, xml_path):
        """
        The layout of a single atlas information.

        """
        xyz = self._model.get_cross_pos()

        prob_list = extract_atlasprob(niftil_path, xyz[0], xyz[1], xyz[2])
        label_list = get_info(xml_path, 'label')
        display = sorting(label_list, prob_list)
        return display


    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Probability Information")
        parent_path = os.path.dirname(os.getcwd())
        tar_path = parent_path+'/froi/data/atlas/'

        # initialize widgets
        self.source_combo = QComboBox()
        self.title_label1 = QLabel('Harvard-Oxford SubCortical Structural Atlas')
        self.title_label1.setFont(QFont("Roman times", 10, QFont.Bold))
        self.prob_label1 = QLabel()
        layout1 = self.atlas_display(tar_path+'HarvardOxford-sub-prob-2mm.nii.gz', tar_path+'HarvardOxford-Subcortical.xml')
        self.prob_label1.setText(layout1)

        self.title_label2 = QLabel('Harvard-Oxford Cortical Structural Atlas')
        self.title_label2.setFont(QFont("Roman times", 10, QFont.Bold))
        self.prob_label2 = QLabel()
        layout2 = self.atlas_display(tar_path+'HarvardOxford-cort-prob-2mm.nii.gz', tar_path+'HarvardOxford-Cortical.xml')
        self.prob_label2.setText(layout2)

        self.help_button = QPushButton("Help")
        self.set_button = QPushButton("Setting")
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.help_button,0,0)
        grid_layout.addWidget(self.set_button,0,1)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.title_label1)
        vbox_layout.addWidget(self.prob_label1)
        vbox_layout.addWidget(self.title_label2)
        vbox_layout.addWidget(self.prob_label2)
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
            new_dialog = SettingDialog(self)
            new_dialog.exec_()
            #print 'close dialog...'
            self.status = new_dialog._get_checkbox_status()
            if self.status != []:
                if self.status[0]:
                    self.title_label1.setVisible(True)
                    self.prob_label1.setVisible(True)
                else:
                    self.title_label1.setVisible(False)
                    self.prob_label1.setVisible(False)
                if self.status[1]:
                    self.title_label2.setVisible(True)
                    self.prob_label2.setVisible(True)
                else:
                    self.title_label2.setVisible(False)
                    self.prob_label2.setVisible(False)


    def _get_set_status(self):
        return self.status


    def _help_dialog(self):
        """
        Help dialog.

        """
        QMessageBox.about(self, self.tr("Helps"),
                          self.tr("<p><b>There exist two atlas: </b><br/>"
                                  "Harvard-Oxford SubCortical Atlas, <br/>"
                                  "Harvard-Oxford Cortical Atlas</p>"
                                  "<p>You can click the Setting button "
                                  "to choose which atlas to show.</p>"))



class SettingDialog(QDialog):
    """
    A dialog for setting button.

    """

    def __init__(self, parent=None):
        super(SettingDialog, self).__init__(parent)
        #self._model = model
        #self._main_win = main_win
        self._init_gui()
        self._create_actions()
        self.ret = []

    def _save(self):
        self.ret = [self.subcor_checkbox.isChecked(), self.cor_checkbox.isChecked()]
        if not self.subcor_checkbox.isChecked():
            self.subcor_checkbox.setEnabled(True)
        if not self.cor_checkbox.isChecked():
            self.cor_checkbox.setEnabled(True)
        self.close()

    def _get_checkbox_status(self):
        return self.ret

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
        self.cor_checkbox.setChecked(True)
        self.save_button = QPushButton("OK")
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.subcor_checkbox, 0,0)
        grid_layout.addWidget(self.subcor_label,0,1)
        grid_layout.addWidget(self.cor_checkbox,1,0)
        grid_layout.addWidget(self.cor_label,1,1)

        ver_layout = QVBoxLayout()
        ver_layout.addLayout(grid_layout)
        ver_layout.addWidget(self.save_button)
        self.setLayout(ver_layout)

    def _create_actions(self):
        self.save_button.clicked.connect(self._save)


