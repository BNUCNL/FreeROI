from PyQt4.QtCore import *
from PyQt4.QtGui import *


class ScribingDialog(QDialog):

    def __init__(self, surface_view, parent=None):
        super(ScribingDialog, self).__init__(parent)
        self._surface_view = surface_view

        # Initialize widgets
        hint_label = QLabel("scribing")
        cancel_button = QPushButton("Cancel")

        # layout
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(hint_label)
        vbox_layout.addWidget(cancel_button)
        self.setLayout(vbox_layout)

        # connect
        # self.connect(cancel_button, SIGNAL("clicked()"), self, SLOT("close()"))  # It may connect QDialog.close
        self.connect(cancel_button, SIGNAL("clicked()"), self.close)

        # do work
        self._surface_view.scribing_flag = True

    def close(self):
        # recover
        self._surface_view.path = []
        self._surface_view.plot_start = None
        self._surface_view.scribing_flag = False
        QDialog.close(self)
