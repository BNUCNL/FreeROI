from PyQt4.QtCore import *
from PyQt4.QtGui import *
from my_tools import toggle_color

import time


class ScribingDialog(QDialog):

    def __init__(self, surface_view, parent=None):
        super(ScribingDialog, self).__init__(parent)
        self._surface_view = surface_view

        # Initialize widgets
        hint_label = QLabel("start scribing")
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        # layout
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(ok_button)
        hbox_layout.addWidget(cancel_button)
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(hint_label)
        self.setLayout(vbox_layout)
        self.layout().addLayout(hbox_layout)

        # connect
        self.connect(ok_button, SIGNAL("clicked()"), self._start_scribing)
        self.connect(cancel_button, SIGNAL("clicked()"), self, SLOT("close()"))

        # do work
        start1 = time.time()
        self.create_graph()
        end1 = time.time()
        print "time of create graph:", end1 - start1, "seconds."

    def _start_scribing(self):
        self.close()

        line_lut = self._surface_view.rgba_lut.copy()
        for v_id in self._surface_view.path:
            toggle_color(line_lut[v_id])
        self._surface_view.surf.module_manager.scalar_lut_manager.lut.table = line_lut

        # recover
        self._surface_view.path = []
        self._surface_view.plot_start = None

    def create_graph(self):

        n_vtx = self._surface_view.get_coords().shape[0]
        one_ring_neighbor = [set() for i in range(n_vtx)]

        for face in self._surface_view.get_faces():
            for v_id in face:
                one_ring_neighbor[v_id].update(set(face))

        for v_id in range(n_vtx):
            one_ring_neighbor[v_id].remove(v_id)

        graph = dict()
        for k, v in enumerate(one_ring_neighbor):
            graph[k] = list(v)
        self._surface_view.set_graph(graph)

    def close(self):
        self._surface_view.set_graph(None)
        QDialog.close(self)
