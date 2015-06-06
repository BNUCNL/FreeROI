# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from PyQt4.QtGui import *
from froi.io.xml_api import *


class HOCorticalDialog(QDialog):
    """
    A dialog for action of Harvard-Oxford Cortical Atlas.

    """
    def __init__(self, model, main_win, parent=None):
        super(HOCorticalDialog, self).__init__(parent)
        self._model = model
        self._main_win = main_win
        self._init_gui()


    def _init_gui(self):
        """
        Initialize GUI.

        """
        # set dialog title
        self.setWindowTitle("Atlas")

        # initialize widgets
        xyz = self._model.get_cross_pos()
        self.source_combo = QComboBox()
        cord_label = QLabel("Coordinate")
        cord_label.setFont(QFont("Roman times", 10, QFont.Bold))

        x_label = QLabel("x: "+ str(xyz[0]))
        y_label = QLabel("y: "+ str(xyz[1]))
        z_label = QLabel("z: "+ str(xyz[2]))

        atlas_label = QLabel("Harvard-Oxford Cortical Structural Atlas")
        atlas_label.setFont(QFont("Roman times", 10, QFont.Bold))

        prob_label = QLabel()
        parent_path = os.path.dirname(os.getcwd())
        tar_path = parent_path+'/froi/data/atlas/'
        prob_list = extract_atlasprob(tar_path+'HarvardOxford-cort-prob-2mm.nii.gz', xyz[0], xyz[1], xyz[2])
        label_list = get_info(tar_path+'HarvardOxford-Cortical.xml','label')
        display = sorting(label_list, prob_list)
        prob_label.setText(display)


        # layout config
        grid_layout = QGridLayout()
        grid_layout.addWidget(x_label, 0, 0)
        grid_layout.addWidget(y_label, 0, 1)
        grid_layout.addWidget(z_label, 0, 2)


        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(cord_label)
        vbox_layout.addLayout(grid_layout)
        vbox_layout.addWidget(atlas_label)
        vbox_layout.addWidget(prob_label)

        self.setLayout(vbox_layout)

