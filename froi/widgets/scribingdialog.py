from PyQt4.QtCore import *
from PyQt4.QtGui import *

from my_tools import bfs, toggle_color


class ScribingDialog(QDialog):

    def __init__(self, surface_view, parent=None):
        super(ScribingDialog, self).__init__(parent)
        self._surface_view = surface_view

        # Initialize widgets
        hint_label = QLabel("scribing")
        mask_button = QPushButton("get mask")
        cancel_button = QPushButton("Cancel")

        # layout
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(mask_button)
        hbox_layout.addWidget(cancel_button)
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(hint_label)
        self.setLayout(vbox_layout)
        self.layout().addLayout(hbox_layout)

        # connect
        self.connect(mask_button, SIGNAL("clicked()"), self._get_mask)
        # self.connect(cancel_button, SIGNAL("clicked()"), self, SLOT("close()"))  # It may connect QDialog.close
        self.connect(cancel_button, SIGNAL("clicked()"), self.close)
        self._surface_view.scribing.connect(self._plot_line)

        # initialize fields
        self.plot_start = None
        self.path = []

        # do work
        self._surface_view.scribing_flag = True

    def _plot_line(self):
        if self.plot_start is None:
            self.plot_start = self._surface_view.point_id
            self.path.append(self.plot_start)
        else:
            new_path = bfs(self._surface_view.edge_list, self.plot_start, self._surface_view.point_id)
            new_path.pop(0)
            self.path.extend(new_path)
            self.plot_start = self._surface_view.point_id
            for v_id in self.path:
                toggle_color(self._surface_view.tmp_lut[v_id])

    def _get_mask(self):
        self.close()

    def close(self):
        # recover
        self.path = []
        self.plot_start = None
        self._surface_view.scribing_flag = False
        QDialog.close(self)
