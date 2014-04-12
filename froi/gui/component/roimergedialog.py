# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm.imtool import merge

class ROIMergeDialog(QDialog):
    """
    A dialog for ROI selection and merging.

    """
    def __init__(self, model, parent=None):
        super(ROIMergeDialog, self).__init__(parent)
        self._model = model
        
        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        """
        Initialize GUI.

        """
        self.setWindowTitle('Selecet Volumes')
        imgs = []
        vol_list = self._model.getItemList()
        for item in vol_list:
            imgs.append(QCheckBox(item))

        self.imgs = imgs

        vboxlayout = QVBoxLayout()
        hboxlayout = QHBoxLayout()

        for item in imgs:
            vboxlayout.addWidget(item)

        self.run_button = QPushButton("Run")
        self.cancel_button = QPushButton("Cancel")
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.run_button)
        hbox_layout.addWidget(self.cancel_button)
        vbox_layout = QVBoxLayout()
        vbox_layout.addLayout(vboxlayout)
        vbox_layout.addLayout(hbox_layout)
        self.setLayout(vbox_layout)

    def _create_actions(self):
        self.run_button.clicked.connect(self._merge)
        self.cancel_button.clicked.connect(self.done)

    def _merge(self):
        img_iter = enumerate(self.imgs)
        first_data, tmp_idx, vol_name = (None, None, [])
        for idx, first in img_iter:
             if first.isChecked():
                first_data = self._model.data(self._model.index(idx),
                                              Qt.UserRole + 6)
                tmp_idx = idx
                vol_name.append(self.imgs[idx].text())
                break

        if first_data is not None:
            for idx, item in img_iter:
                if item.isChecked():
                    data = self._model.data(self._model.index(idx),
                                            Qt.UserRole + 6)
                    try:
                        first_data = merge(first_data, data)
                        vol_name.append(self.imgs[idx].text())
                    except ValueError:
                        QMessageBox.critical(self, "Conflicts dectected %s" % 
                                             self.imgs[idx].text(),
                                             "Please modify ROI by hands")
                        return
            self._model.addItem(first_data,
                                None,
                                '_'.join(map(str, vol_name)),
                                self._model._data[0].get_header(),
                                None, None, 255, 'rainbow')
            self.done(0)
