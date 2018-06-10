# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from PyQt4.QtCore import *
from PyQt4.QtGui import *


def gen_label_color(color):
    icon_image = QImage(QSize(32, 32), QImage.Format_RGB888)
    icon_image.fill(color.rgb())
    icon_image = icon_image.rgbSwapped()
    icon_pixmap = QPixmap.fromImage(icon_image)

    return QIcon(icon_pixmap)
