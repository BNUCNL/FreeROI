# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from froi.algorithm import imtool


def inverse_image(model):
    """Inverse current selected image by multiplying with -1."""
    # get data and name from current selected image
    current_row = model.currentIndex().row()
    source_vol = model.data(model.index(current_row), Qt.UserRole + 6)
    source_name = model.data(model.index(current_row), Qt.DisplayRole)
    # inverse process
    inversed_vol =  imtool.inverse_transformation(source_vol)
    inversed_vol_name = 'inverse_' + source_name
    # save result as a new image
    model.addItem(inversed_vol, None, inversed_vol_name, 
                  model._data[0].get_header())
    return


def edge_detection(model):
    """Image edge detection."""
    # get data and name from current selected image
    current_row = model.currentIndex().row()
    source_vol = model.data(model.index(current_row), Qt.UserRole + 6)
    source_name = model.data(model.index(current_row), Qt.DisplayRole)
    # detect the edge
    new_vol =  imtool.multi_label_edge_detection(source_vol)
    new_vol_name = 'edge_' + source_name
    # save result as a new image
    model.addItem(new_vol, None, new_vol_name,
                  model._data[0].get_header(),
                  None, None, 255, 'green')
    return


def gen_label_color(color):
    icon_image = QImage(QSize(32, 32), QImage.Format_RGB888)
    icon_image.fill(color.rgb())
    icon_image = icon_image.rgbSwapped()
    icon_pixmap = QPixmap.fromImage(icon_image)

    return QIcon(icon_pixmap)
