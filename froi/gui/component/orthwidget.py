# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""A viewer (part of Qt model-view-delegate classes) for image display 
in orthographic style.

"""

import numpy as np
from PyQt4.QtGui import *

from imagelabel import (SagittalImageLabel, AxialImageLabel, CoronalImageLabel)

class OrthView(QWidget):
    """
    Implementation a widget for image display in a orthographic style.

    """
    def __init__(self, model=None, draw_settings=None, parent=None):
        """
        Initialize the widget.

        """
        super(OrthView, self).__init__(parent)

        self._model = model
        self._model.scale_changed.connect(self.resize_item)
        self._model.cross_pos_changed.connect(self.update_cross_pos)
        self.set_draw_settings(draw_settings)
        
        self._saglabel = SagittalImageLabel(model, draw_settings, self)
        self._axilabel = AxialImageLabel(model, draw_settings, self)
        self._corlabel = CoronalImageLabel(model, draw_settings, self)
        
        # get expanding factor
        self.set_expanding_factor()

        # set label layout
        layout = QGridLayout()
        layout.setSpacing(5)
        layout.addWidget(self._corlabel, 0, 0)
        layout.addWidget(self._saglabel, 0, 1)
        layout.addWidget(self._axilabel, 1, 0)

        # add display widget
        self.setLayout(layout)
        self.setBackgroundRole(QPalette.Dark)

        self._type = 'orth'

        # -- temporary
        self.layout = layout
        # --

        # variable for drawing
        self.voxels = set()

        self.set_label_mouse_tracking(True)

    def set_expanding_factor(self):
        self._expanding_factor = np.min([self._corlabel.get_expanding_size(),
                                         self._saglabel.get_expanding_size(),
                                         self._axilabel.get_expanding_size()])
        self._expanding_factor -= 0.1

    def get_expanding_factor(self):
        return self._expanding_factor

    def display_type(self):
        return self._type

    def set_display_type(self, type):
        self._type = type

    def set_label_mouse_tracking(self, t=False):
        self._saglabel.setMouseTracking(t)
        self._axilabel.setMouseTracking(t)
        self._corlabel.setMouseTracking(t)

    def set_cursor(self, cursor_shape):
        self._saglabel.setCursor(cursor_shape)
        self._axilabel.setCursor(cursor_shape)
        self._corlabel.setCursor(cursor_shape)

    def resize_item(self):
        """
        Resize label -- remove label from layout first, and re-fill it

        """
        self.repaint()

    def set_draw_settings(self, draw_settings):
        """
        Set scale factor.

        """
        self._draw_settings = draw_settings

    def update_cross_pos(self):
        """
        Set current coordinate as a new value.

        """
        self.repaint()

    def repaint(self):
        """
        repaint.

        """
        self._saglabel.update_image()
        self._axilabel.update_image()
        self._corlabel.update_image()

    def reset_view(self):
        """
        Reset view.

        """
        self._saglabel.pic_src_point = None
        self._axilabel.pic_src_point = None
        self._corlabel.pic_src_point = None
        self.repaint()

    def resizeEvent(self, e):
        """
        Reimplement the resize event.

        """
        self.set_expanding_factor()
        self.repaint()
