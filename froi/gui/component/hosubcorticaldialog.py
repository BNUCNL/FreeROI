# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtGui import *
from froi.io.xml_api import *


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


    def get_prob_info(self, niftil_path, xml_path):
        """
        The layout display for a single atlas information.

        """
        xyz = self._model.get_cross_pos()
        parent_path = os.path.dirname(os.getcwd())
        tar_path = parent_path+'/froi/data/atlas/'

        prob_list = extract_atlasprob(tar_path+ niftil_path, xyz[0], xyz[1], xyz[2])
        label_list = get_info(tar_path+ xml_path, 'label')
        info = sorting(label_list, prob_list)
        return info


    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Atlas Information")

        # initialize widgets
        self.source_combo = QComboBox()
        self.subcor_label = QLabel('Harvard-Oxford SubCortical Atlas')
        self.subcor_label.setFont(QFont("Roman times", 10, QFont.Bold))
        self.subcor_checkbox = QCheckBox()
        self.subcor_checkbox.setChecked(True)
        grid_layout1 = QGridLayout()
        grid_layout1.addWidget(self.subcor_checkbox,0,0)
        grid_layout1.addWidget(self.subcor_label,0,1)

        self.cor_label = QLabel('Harvard-Oxford Cortical Atlas')
        self.cor_label.setFont(QFont("Roman times", 10, QFont.Bold))
        self.cor_checkbox = QCheckBox()
        self.cor_checkbox.setChecked(True)
        grid_layout2 = QGridLayout()
        grid_layout2.addWidget(self.cor_checkbox,0,0)
        grid_layout2.addWidget(self.cor_label,0,1)

        self.prob_label1 = QLabel()
        self.layout1 = self.get_prob_info('HarvardOxford-sub-prob-2mm.nii.gz', 'HarvardOxford-Subcortical.xml')
        self.prob_label1.setText(self.layout1)
        #self.layout1.setEnabled(False)
        self.prob_label2 = QLabel()
        self.layout2 = self.get_prob_info('HarvardOxford-cort-prob-2mm.nii.gz', 'HarvardOxford-Cortical.xml')
        self.prob_label2.setText(self.layout2)
        #self.layout2.setEnabled(False)

        self.help_button = QPushButton("Help")
        self.set_button = QPushButton("Setting")
        #grid_layout3.addWidget(self.set_button,0,1)

        self.vbox_layout = QVBoxLayout()
        self.vbox_layout.addLayout(grid_layout1)
        self.vbox_layout.addWidget(self.prob_label1)
        self.vbox_layout.addLayout(grid_layout2)
        self.vbox_layout.addWidget(self.prob_label2)
        self.vbox_layout.addWidget(self.help_button)

        self.setLayout(self.vbox_layout)


    def _create_actions(self):
        """
        Create actions about the button
        """
        self.help_button.clicked.connect(self._help_dialog)
        self.subcor_checkbox.clicked.connect(self._disabled_subcor)
        self.cor_checkbox.clicked.connect(self._disabled_cor)



    def _help_dialog(self):
        """
        Help dialog.

        """
        QMessageBox.about(self, self.tr("Helps"),
                      self.tr("<p><b>There exist two atlas: </b><br/>"
                              "Harvard-Oxford SubCortical Atlas, <br/>"
                              "Harvard-Oxford Cortical Atlas</p>"
                              "<p>You can click the Checkbox "
                              "to choose which atlas to show.</p>"))


    def _disabled_subcor(self):
        if self.subcor_checkbox.isChecked():
            #self.layout1.invalidate()
            self.prob_label1.setVisible(True)
        else:
            self.prob_label1.setVisible(False)



    def _disabled_cor(self):
        if self.cor_checkbox.isChecked():
            #self.layout1.invalidate()
            self.prob_label2.setVisible(True)
        else:
            self.prob_label2.setVisible(False)