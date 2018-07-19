# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..algorithm.array2qimage import composition, qrgba2qimage


"""ImageLabel class. It is used to show a slice of the 3D image"""

class ImageLabel(QLabel):
    """Class ImageLabel provides basic methods for image displaying."""

    # resized signal
    #resized_signal = pyqtSignal(float, float, int)

    def __init__(self, model, painter_status, n_slice, parent=None):
        """Initialize an instance."""
        super(ImageLabel, self).__init__(parent)
        # set background color
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)
        # model setting
        self.set_model(model)
        self.painter_status = painter_status
        self.n_slice = n_slice
        self.background = np.zeros((model.getX(), model.getY(), 3), 
                                   dtype=np.uint8)
        self.image = None
        self.pm = None

        self.voxel_scaler_base = min([self.model.get_voxel_size_x(),
                                      self.model.get_voxel_size_y(),
                                      self.model.get_voxel_size_z()])
        self.voxel_scaler = [item*1.0/self.voxel_scaler_base for item in
                             [self.model.get_voxel_size_x(),
                              self.model.get_voxel_size_y(),
                              self.model.get_voxel_size_z()]]

        # for drawing
        self.drawing = False
        self.voxels = set() 

    def sizeHint(self):
        """ Size hint configuration."""
        default_size = QSize(self.background.shape[1]*self.voxel_scaler[1],
                             self.background.shape[0]*self.voxel_scaler[0])
        scale_factor = self.model.get_scale_factor('grid')
        return default_size * scale_factor

    def set_model(self, model):
        """Set data model."""
        self.model = model
        self.model.repaint_slices.connect(self.update_image)

    def update_image(self, m_slice):
        """Repaint image."""
        # -1 for all
        if m_slice == -1 or m_slice == self.n_slice:
            self.repaint()
        self.updateGeometry()

    def is_current_slice(self):
        """Return True if cursor select current slice."""
        return self.n_slice == self.model.get_cross_pos()[2]

    def paintEvent(self, e):
        """Reimplement repaintEvent."""
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(self)
        if not self.image or not self.drawing:
            background = self.background.copy()
            blend = reduce(composition, 
                           self.model.rgba_list(self.n_slice), 
                           background)
            image = qrgba2qimage(blend)
            self.image = image
        pm = QPixmap.fromImage(self.image)
        pm = pm.scaled(pm.size().width() * self.voxel_scaler[1] \
                         * self.model.get_scale_factor('grid'),
                       pm.size().height() * self.voxel_scaler[0] \
                         * self.model.get_scale_factor('grid'),
                       Qt.IgnoreAspectRatio,
                       Qt.FastTransformation)
        self.pm = pm
        self.voxels_painter.drawPixmap(0, 0, pm, 0, 0, 
                                       pm.size().width(), pm.size().height())
        
        # draw voxels if necessary
        if self.drawing and self.voxels:
            self.draw_voxels(self.voxels)

        # draw crosshair on picture
        if self.model.display_cross() and self.is_current_slice():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('grid')
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[1]
            horizon_src = ((current_pos[0] + 0.5) * horizon_vscale * scale, 0)
            horizon_targ = ((current_pos[0] + 0.5) * horizon_vscale * scale,
                            self.pm.size().height())
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[0]
            vertical_src = (0,
                            (self.model.getX() - current_pos[1] - 0.5) \
                                * vertical_vscale * scale)
            vertical_targ = (self.pm.size().width(),
                             (self.model.getX() - current_pos[1] - 0.5) \
                                * vertical_vscale * scale)
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])

        self.voxels_painter.end()
        self.resize(self.pm.size().width(), self.pm.size().height())

    def mousePressEvent(self, e):
        if not self._mouse_in(e.x(), e.y()):
            return 
        if self.painter_status.is_drawing_valid():
            if not self.painter_status.is_roi_tool():
                size = self.painter_status.get_drawing_size()
                X = e.x()
                Y = e.y()
                new_voxels = [(x, y, self.n_slice) 
                              for x in xrange(X - size/2, X + size/2 + 1)
                              for y in xrange(Y -size/2, Y + size/2 + 1)
                              if self._mouse_in(x, y)]
                self.voxels |= set(new_voxels)
                self.drawing = True
                self.repaint()
                self.drawing = False
            else:
                scale = self.model.get_scale_factor('grid')
                height_vscale = self.voxel_scaler[0]
                width_vscale = self.voxel_scaler[1]
                y = self.model.getX()-1-int(np.floor(e.y()/height_vscale/scale))
                x = int(np.floor(e.x()/width_vscale/scale))
                roi_val = self.model.get_current_roi_val(x, y, self.n_slice)
                if roi_val != 0:
                    t_value = self.painter_status.get_drawing_value()
                    self.model.modify_voxels(value=t_value, roi=roi_val)
        else:
            if self.painter_status.is_roi_selection():
                scale = self.model.get_scale_factor('grid')
                height_vscale = self.voxel_scaler[0]
                width_vscale = self.voxel_scaler[1]
                y = self.model.getX()-1-int(np.floor(e.y()/height_vscale/scale))
                x = int(np.floor(e.x()/width_vscale/scale))
                roi_val = self.model.get_current_roi_val(x, y, self.n_slice)
                if roi_val != 0:
                    self.painter_status.get_draw_settings()._update_roi(roi_val)
            scale = self.model.get_scale_factor('grid')
            height_vscale = self.voxel_scaler[0]
            width_vscale = self.voxel_scaler[1]
            y = self.model.getX()-1-int(np.floor(e.y()/height_vscale/scale))
            x = int(np.floor(e.x()/width_vscale/scale))
            self.model.set_cross_pos([x, y, self.n_slice])
       
    def mouseMoveEvent(self, e):
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            #self.setCursor(Qt.CrossCursor)
            if not self.painter_status.is_roi_tool():
                size = self.painter_status.get_drawing_size()
                X = e.x()
                Y = e.y()
                new_voxels = [(x, y, self.n_slice) 
                              for x in xrange(X - size/2, X + size/2 + 1)
                              for y in xrange(Y - size/2, Y + size/2 + 1)
                              if self._mouse_in(x, y)]
                self.voxels |= set(new_voxels)
                self.drawing = True
                self.repaint()
                self.drawing = False
        else:
            pass
            #self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, e):
        if self.painter_status.is_drawing_valid() and (not
           self.painter_status.is_roi_tool()):
            scale = self.model.get_scale_factor('grid')
            height_vscale = self.voxel_scaler[0]
            width_vscale = self.voxel_scaler[1]
            pix_to_vox = lambda (x,y,z): (int(np.floor(x/width_vscale/scale)), 
                                          self.model.getX() - 1 - \
                                          int(np.floor(y/height_vscale/scale)), 
                                          z)
            voxels = map(pix_to_vox, list(self.voxels))
            if voxels:
                self.model.modify_voxels(voxels, 
                    self.painter_status.get_drawing_value())
            self.voxels = set()

    def _mouse_in(self, x, y):
        return (0 <= x < self.size().width() and
                0 <= y < self.size().height())
        
    def draw_voxels(self, voxels):
        self.voxels_painter.setPen(self.painter_status.get_drawing_color())
        points = [QPoint(v[0], v[1]) for v in voxels]
        self.voxels_painter.drawPoints(*points)

    def inrange(self, x=None, y=None):
        if x is None:
            return y >= 0 and y < self.model.getX()
        if y is None:
            return x >= 0 and x < self.model.getY()
        return ((x >= 0 and x < self.model.getY()) and 
                (y >= 0 and y < self.model.getX()))

class ImageLabel3d(QLabel):
    """Class ImageLabel3d provides basic methods for image displaying in three different orientation.

    Attention:
    Methods, e.g. painEvent, must be reimplemented.
    """

    # draw voxels signal
    draw_voxels_sig = pyqtSignal()
    
    def __init__(self, model, painter_status, holder, parent=None):
        """Initialize an instance."""
        super(ImageLabel3d, self).__init__(parent)

        # set background color as black
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)
       
        # set margin of imagelabel
        self.margin_size = 30
        self.axcodes = None
        self.str_font_size = 10

        # private attributes
        self.set_model(model)
        self.painter_status = painter_status
        self.background = self.make_background()
        self.image = None
        self.pm = None
        self.pic_src_point = None

        # store parent widget
        self.holder = holder

        # for drawing
        self.drawing = False

        # for moving
        self.old_pos = None
        self.new_pos = None

        # label status
        self.is_moving = False
        self.is_painting = True

    def set_model(self, model):
        """Set date model."""
        self.model = model
        self.model.repaint_slices.connect(self.update_image)
        self.get_axcodes()
        self.voxel_scaler_base = min([self.model.get_voxel_size_x(),
                                      self.model.get_voxel_size_y(),
                                      self.model.get_voxel_size_z()])
        self.voxel_scaler = [item*1.0/self.voxel_scaler_base for item in
                             [self.model.get_voxel_size_x(),
                              self.model.get_voxel_size_y(),
                              self.model.get_voxel_size_z()]]

    def get_axcodes(self):
        """Get axis codes from model."""
        tmp = self.model.get_axcodes()
        self.axcodes = []
        for item in tmp:
            if item == 'R':
                self.axcodes.append(('R', 'L'))
            elif item == 'L':
                self.axcodes.append(('L', 'R'))
            elif item == 'A':
                self.axcodes.append(('A', 'P'))
            elif item == 'P':
                self.axcodes.append(('P', 'A'))
            elif item == 'S':
                self.axcodes.append(('S', 'I'))
            elif item == 'I':
                self.axcodes.append(('I', 'S'))
        return self.axcodes

    def sizeHint(self):
        """Size hint configuration."""
        return QSize(self.size().width(), self.size().height())

    def update_image(self, coord=None):
        """Update image."""
        self.repaint()

    def make_background(self):
        """Create a whole black background."""
        background = np.zeros((self.size().height(), self.size().width(), 3),
                              dtype=np.uint8)
        return qrgba2qimage(background)

    def get_ver_margin(self):
        """Get black vertical margin for the image."""
        margin = np.zeros((self.size().height(), self.margin_size, 3),
                          dtype=np.uint8)
        return qrgba2qimage(margin)

    def get_hor_margin(self):
        """Get horizontal margin for the image."""
        margin = np.zeros((self.margin_size, self.size().width(), 3),
                          dtype=np.uint8)
        return qrgba2qimage(margin)

    def center_src_point(self):
        """Return the coordinate of left-up corner."""
        x = (self.size().width() - self.pm.size().width()) / 2
        y = (self.size().height() - self.pm.size().height()) / 2
        return (x, y)

    def horizontal_valid_range(self):
        """Return the valid range of horizontal axis."""
        if not self.is_painting:
            min_val = self.pic_src_point[0]
            if min_val < 0:
                min_val = 0
            max_val = self.pic_src_point[0] + self.pm.size().width()
            if max_val > self.size().width():
                max_val = self.size().width()
            return (min_val, max_val)
        else:
            return (0, -1)

    def vertical_valid_range(self):
        """Return the valid range of vertical axis."""
        if not self.is_painting:
            min_val = self.pic_src_point[1]
            if min_val < 0:
                min_val = 0
            max_val = self.pic_src_point[1] + self.pm.size().height()
            if max_val > self.size().height():
                max_val = self.size().height()
            return (min_val, max_val)
        else:
            return (0, -1)

    def _mouse_in(self, x, y):
        """Check whether current cursor position is in the valid area of the picture."""
        return (self.horizontal_valid_range()[0] <= x < \
                self.horizontal_valid_range()[1] and \
                self.vertical_valid_range()[0] <= y < \
                self.vertical_valid_range()[1])

    def mouseReleaseEvent(self, e):
        """Reimplement mouseReleaseEvent."""
        scale = self.model.get_scale_factor('orth') * self._expanding_factor
        if self.painter_status.is_drawing_valid() and (not 
           self.painter_status.is_roi_tool()):
            pix_to_vox = lambda (x, y, z): (int(np.rint(x \
                                            / self.voxel_scaler[1] / scale)), 
                                            int(np.rint(y \
                                            / self.voxel_scaler[0] / scale)), 
                                            int(np.rint(z \
                                            / self.voxel_scaler[2] / scale)))
            voxels = map(pix_to_vox, list(self.holder.voxels))
            if voxels:
                self.model.modify_voxels(voxels,
                        self.painter_status.get_drawing_value())
            self.holder.voxels = set()
        elif self._mouse_in(e.x(), e.y()) and self.painter_status.is_view():
            self.is_moving = False
        elif self._mouse_in(e.x(), e.y()) and self.painter_status.is_hand():
            self.setCursor(Qt.OpenHandCursor)

class SagittalImageLabel(ImageLabel3d):
    """ImageLabel in sagittal view."""
    def get_expanding_size(self):
        """Compute a proper expanding size used to display."""
        w_times = float(self.size().width()) / self.model.getX() \
                    / self.voxel_scaler[0]
        h_times = float(self.size().height()) / self.model.getZ() \
                    / self.voxel_scaler[2]
        return np.min([w_times, h_times])

    def paintEvent(self, e):
        """Reimplement paintEvent."""
        self.is_painting = True
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(self)
        
        self._expanding_factor = self.holder.get_expanding_factor()

        # composite volume picture
        if not self.image or not self.drawing:
            back_temp = np.zeros((self.model.getZ(), self.model.getX(), 3), 
                                 dtype=np.uint8)
            blend = reduce(composition, 
                           self.model.get_sagital_rgba_list(),
                           back_temp)
            image = qrgba2qimage(blend)
            self.image = image
        
        # draw black background
        self.background = self.make_background()
        pm = QPixmap.fromImage(self.background)
        self.voxels_painter.drawPixmap(0, 0, pm)
        
        # draw volume picture
        pm = QPixmap.fromImage(self.image)
        self.pm = pm.scaled(pm.size().width() * self.voxel_scaler[0] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            pm.size().height() * self.voxel_scaler[2] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            Qt.IgnoreAspectRatio,
                            Qt.FastTransformation)
        if not self.pic_src_point:
            self.pic_src_point = self.center_src_point()
        self.voxels_painter.drawPixmap(self.pic_src_point[0],
                                       self.pic_src_point[1], 
                                       self.pm)

        # draw voxels if necessary
        if self.drawing and self.holder.voxels:
            self.draw_voxels(self.holder.voxels)

        # draw cross line on picture
        if self.model.display_cross():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[2]
            horizon_src = (0,
                           (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            horizon_targ = (self.size().width(),
                            (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[0]
            vertical_src = ((self.model.getX() - current_pos[1] - 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                            0)
            vertical_targ = ((self.model.getX() - current_pos[1] - 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                             self.size().height())
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])
            
        # draw margin
        l_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(0, 0, l_margin)
        r_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(self.size().width()-self.margin_size,
                                       0, r_margin)
        t_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0, 0, t_margin)
        b_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0,
                                       self.size().height()-self.margin_size,
                                       b_margin)
        # draw orientation label
        # l_str = QString(self.axcodes[1][0])
        # #l_str.resize(self.str_font_size)
        # r_str = QString(self.axcodes[1][1])
        # t_str = QString(self.axcodes[2][0])
        # b_str = QString(self.axcodes[2][1])

        l_str = self.axcodes[1][0]
        #l_str.resize(self.str_font_size)
        r_str = self.axcodes[1][1]
        t_str = self.axcodes[2][0]
        b_str = self.axcodes[2][1]

        self.voxels_painter.setPen(QColor(255, 255, 255, 255))
        self.voxels_painter.drawText(7, self.size().height()/2+5, l_str)
        self.voxels_painter.drawText(self.size().width()-12,
                                     self.size().height()/2+5, r_str)
        self.voxels_painter.drawText(self.size().width()/2-5,
                                     15, t_str)
        self.voxels_painter.drawText(self.size().width()/2-1,
                                     self.size().height()-12, b_str)
        
        self.voxels_painter.end()
        self.is_painting = False

    def save_image(self):
        """Save image as file."""
        file_name = self.__class__.__name__ + '.png'
        pic = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(pic)
        
        self._expanding_factor = self.holder.get_expanding_factor()

        # composite volume picture
        if not self.image or not self.drawing:
            back_temp = np.zeros((self.model.getZ(), self.model.getX(), 3), 
                                 dtype=np.uint8)
            blend = reduce(composition, 
                           self.model.get_sagital_rgba_list(),
                           back_temp)
            image = qrgba2qimage(blend)
            self.image = image
        
        # draw black background
        self.background = self.make_background()
        pm = QPixmap.fromImage(self.background)
        self.voxels_painter.drawPixmap(0, 0, pm)
        
        # draw volume picture
        pm = QPixmap.fromImage(self.image)
        self.pm = pm.scaled(pm.size().width() * self.voxel_scaler[0] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            pm.size().height() * self.voxel_scaler[2] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            Qt.IgnoreAspectRatio,
                            Qt.FastTransformation)
        if not self.pic_src_point:
            self.pic_src_point = self.center_src_point()
        self.voxels_painter.drawPixmap(self.pic_src_point[0],
                                       self.pic_src_point[1], 
                                       self.pm)

        # draw cross line on picture
        if self.model.display_cross():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[2]
            horizon_src = (0,
                           (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            horizon_targ = (self.size().width(),
                            (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[0]
            vertical_src = ((self.model.getX() - current_pos[1] - 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                            0)
            vertical_targ = ((self.model.getX() - current_pos[1] - 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                             self.size().height())
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])
            
        # draw margin
        l_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(0, 0, l_margin)
        r_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(self.size().width()-self.margin_size,
                                       0, r_margin)
        t_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0, 0, t_margin)
        b_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0,
                                       self.size().height()-self.margin_size,
                                       b_margin)
        # draw orientation label
        # l_str = QString(self.axcodes[1][0])
        # r_str = QString(self.axcodes[1][1])
        # t_str = QString(self.axcodes[2][0])
        # b_str = QString(self.axcodes[2][1])

        l_str = self.axcodes[1][0]
        r_str = self.axcodes[1][1]
        t_str = self.axcodes[2][0]
        b_str = self.axcodes[2][1]

        self.voxels_painter.setPen(QColor(255, 255, 255, 255))
        self.voxels_painter.drawText(7, self.size().height()/2+5, l_str)
        self.voxels_painter.drawText(self.size().width()-12,
                                     self.size().height()/2+5, r_str)
        self.voxels_painter.drawText(self.size().width()/2-5,
                                     15, t_str)
        self.voxels_painter.drawText(self.size().width()/2-1,
                                     self.size().height()-12, b_str)
        
        self.voxels_painter.end()
        self.is_painting = False
        pic.save(file_name)

    def draw_voxels(self, voxels):
        """Draw selected voxels."""
        self.voxels_painter.setPen(self.painter_status.get_drawing_color())
        scale = self.model.get_scale_factor('orth') * self._expanding_factor
        points = [QPoint(self.pic_src_point[0] \
                            + self.model.getX() * self.voxel_scaler[0] * scale \
                            - v[1],
                         self.pic_src_point[1] \
                            + self.model.getZ() * self.voxel_scaler[2] * scale \
                            - v[2]) 
                  for v in voxels
                  if v[0] == (self.model.get_cross_pos()[0] \
                                * self.voxel_scaler[1] * scale)]
        if points:        
            self.voxels_painter.drawPoints(*points)

    def mousePressEvent(self, e):
        """Reimplement mousePressEvent."""
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            if not self.painter_status.is_roi_tool():
                size = self.painter_status.get_drawing_size()
                X = e.x()
                Y = e.y()
                x_margin = self.pic_src_point[0]
                y_margin = self.pic_src_point[1]
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                new_voxels = [(self.model.get_cross_pos()[0] \
                                * self.voxel_scaler[1] * scale, 
                               self.model.getX() \
                                * self.voxel_scaler[0] * scale - x + x_margin, 
                               self.model.getZ() \
                                * self.voxel_scaler[2] * scale - y + y_margin)
                              for x in xrange(X - size/2, X + size/2 + 1) 
                              for y in xrange(Y - size/2, Y + size/2 + 1)
                              if self._mouse_in(x, y)]
                self.holder.voxels |= set(new_voxels)
                # draw voxels
                self.drawing = True
                self.repaint()
                self.drawing = False
            else:
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = self.model.getX() - 1 - \
                        int(np.floor(x/self.voxel_scaler[0]/scale))
                y = self.model.getZ() - 1 - \
                        int(np.floor(y/self.voxel_scaler[2]/scale))
                roi_val = self.model.get_current_roi_val(
                            self.model.get_cross_pos()[0], x, y)
                if roi_val != 0:
                    t_value = self.painter_status.get_drawing_value()
                    self.model.modify_voxels(value=t_value, roi=roi_val)
        elif self.painter_status.is_hand():
            self.setCursor(Qt.ClosedHandCursor)
            self.old_pos = (e.x(), e.y())
        else:
            self.setCursor(Qt.ArrowCursor)
            if self.painter_status.is_roi_selection():
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = self.model.getX() - \
                        int(np.floor(x/self.voxel_scaler[0]/scale))
                y = self.model.getZ() - \
                        int(np.floor(y/self.voxel_scaler[2]/scale))
                roi_val = self.model.get_current_roi_val(
                            self.model.get_cross_pos()[0], x, y)
                if roi_val != 0:
                    self.painter_status.get_draw_settings()._update_roi(roi_val)
            else:
                self.is_moving = True
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            x = e.x() - self.pic_src_point[0]
            y = e.y() - self.pic_src_point[1]
            x = self.model.getX() - 1 - \
                    int(np.floor(x/self.voxel_scaler[0]/scale))
            y = self.model.getZ() - 1 - \
                    int(np.floor(y/self.voxel_scaler[2]/scale))
            current_pos = [self.model.get_cross_pos()[0], x, y]
            self.model.set_cross_pos(current_pos)

    def mouseMoveEvent(self, e):
        """Reimplement mouseMoveEvent."""
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            self.setCursor(Qt.CrossCursor)
            size = self.painter_status.get_drawing_size()
            X = e.x()
            Y = e.y()
            x_margin = self.pic_src_point[0]
            y_margin = self.pic_src_point[1]
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            new_voxels = [(self.model.get_cross_pos()[0] \
                            * self.voxel_scaler[1] * scale,
                           self.model.getX() \
                            * self.voxel_scaler[0] * scale - x + x_margin, 
                           self.model.getZ() \
                            * self.voxel_scaler[2] * scale - y + y_margin)
                          for x in xrange(X - size/2, X + size/2 + 1) 
                          for y in xrange(Y - size/2, Y + size/2 + 1)
                          if self._mouse_in(x, y)]
            self.holder.voxels |= set(new_voxels)
            # draw voxels
            self.drawing = True
            self.repaint()
            self.drawing = False
        elif self.painter_status.is_view():
            self.setCursor(Qt.ArrowCursor)
            if self.is_moving:
                scale=self.model.get_scale_factor('orth')*self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = self.model.getX() - 1 - \
                        int(np.floor(x/self.voxel_scaler[0]/scale))
                y = self.model.getZ() - 1 - \
                        int(np.floor(y/self.voxel_scaler[2]/scale))
                current_pos = [self.model.get_cross_pos()[0], x, y]
                self.model.set_cross_pos(current_pos)
        elif self.painter_status.is_hand():
            if self.cursor().shape() == Qt.ArrowCursor:
                self.setCursor(Qt.OpenHandCursor)
            if self.cursor().shape() == Qt.ClosedHandCursor:
                self.new_pos = (e.x(), e.y())
                dist = (self.new_pos[0] - self.old_pos[0], 
                        self.new_pos[1] - self.old_pos[1])
                self.old_pos = self.new_pos
                self.pic_src_point = (self.pic_src_point[0] + dist[0],
                                      self.pic_src_point[1] + dist[1])
                self.repaint()
        else:
            self.setCursor(Qt.ArrowCursor)
            
class AxialImageLabel(ImageLabel3d):
    """ImageLabel in axial view."""
    def get_expanding_size(self):
        """Compute a proper expanding size used to display."""
        w_times = float(self.size().width()) / self.model.getY() \
                    / self.voxel_scaler[1]
        h_times = float(self.size().height()) / self.model.getX() \
                    / self.voxel_scaler[0]
        return np.min([w_times, h_times])

    def paintEvent(self, e):
        """Reimplement paintEvent."""
        self.is_painting = True
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(self)

        self._expanding_factor = self.holder.get_expanding_factor()

        # composite volume picture
        if not self.image or not self.drawing:
            back_temp = np.zeros((self.model.getX(), self.model.getY(), 3), 
                                 dtype=np.uint8)
            blend = reduce(composition, 
                           self.model.get_axial_rgba_list(),
                           back_temp)
            image = qrgba2qimage(blend)
            self.image = image

        # draw black backgroud
        self.background = self.make_background()
        pm = QPixmap.fromImage(self.background)
        self.voxels_painter.drawPixmap(0, 0, pm)

        # draw volume picture
        pm = QPixmap.fromImage(self.image)
        self.pm = pm.scaled(pm.size().width() * self.voxel_scaler[1] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            pm.size().height() * self.voxel_scaler[0] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            Qt.IgnoreAspectRatio,
                            Qt.FastTransformation)
        if not self.pic_src_point:
            self.pic_src_point = self.center_src_point()
        self.voxels_painter.drawPixmap(self.pic_src_point[0],
                                       self.pic_src_point[1],
                                       self.pm)

        # draw voxels if necessary
        if self.drawing and self.holder.voxels:
            self.draw_voxels(self.holder.voxels)

        # draw cross line on picture
        if self.model.display_cross():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[0]
            horizon_src = (0,
                           (self.model.getX() - current_pos[1] - 0.5) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            horizon_targ = (self.size().width(), 
                            (self.model.getX() - current_pos[1] - 0.5) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[1]
            vertical_src = ((current_pos[0] + 0.5) * vertical_vscale * scale \
                                + self.pic_src_point[0],
                            0)
            vertical_targ = ((current_pos[0] + 0.5) * vertical_vscale * scale \
                                + self.pic_src_point[0],
                             self.size().height())
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])
        
        # draw margin
        l_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(0, 0, l_margin)
        r_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(self.size().width()-self.margin_size,
                                       0, r_margin)
        t_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0, 0, t_margin)
        b_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0,
                                       self.size().height()-self.margin_size,
                                       b_margin)
        # draw orientation label
        # l_str = QString(self.axcodes[0][1])
        # r_str = QString(self.axcodes[0][0])
        # t_str = QString(self.axcodes[1][0])
        # b_str = QString(self.axcodes[1][1])

        l_str = self.axcodes[0][1]
        r_str = self.axcodes[0][0]
        t_str = self.axcodes[1][0]
        b_str = self.axcodes[1][1]

        self.voxels_painter.setPen(QColor(255, 255, 255, 255))
        self.voxels_painter.drawText(7, self.size().height()/2+5, l_str)
        self.voxels_painter.drawText(self.size().width()-12,
                                     self.size().height()/2+5, r_str)
        self.voxels_painter.drawText(self.size().width()/2-5,
                                     15, t_str)
        self.voxels_painter.drawText(self.size().width()/2-1,
                                     self.size().height()-12, b_str)
        
        self.voxels_painter.end()
        self.is_painting = False
    
    def save_image(self):
        """Save image as file."""
        file_name = self.__class__.__name__ + '.png'
        pic = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.is_painting = True
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(pic)

        self._expanding_factor = self.holder.get_expanding_factor()

        # composite volume picture
        if not self.image or not self.drawing:
            back_temp = np.zeros((self.model.getX(), self.model.getY(), 3), 
                                 dtype=np.uint8)
            blend = reduce(composition, 
                           self.model.get_axial_rgba_list(),
                           back_temp)
            image = qrgba2qimage(blend)
            self.image = image

        # draw black backgroud
        self.background = self.make_background()
        pm = QPixmap.fromImage(self.background)
        self.voxels_painter.drawPixmap(0, 0, pm)

        # draw volume picture
        pm = QPixmap.fromImage(self.image)
        self.pm = pm.scaled(pm.size().width() * self.voxel_scaler[1] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            pm.size().height() * self.voxel_scaler[0] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            Qt.IgnoreAspectRatio,
                            Qt.FastTransformation)
        if not self.pic_src_point:
            self.pic_src_point = self.center_src_point()
        self.voxels_painter.drawPixmap(self.pic_src_point[0],
                                       self.pic_src_point[1],
                                       self.pm)

        # draw cross line on picture
        if self.model.display_cross():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[0]
            horizon_src = (0,
                           (self.model.getX() - current_pos[1] - 0.5) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            horizon_targ = (self.size().width(), 
                            (self.model.getX() - current_pos[1] - 0.5) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[1]
            vertical_src = ((current_pos[0] + 0.5) * vertical_vscale * scale \
                                + self.pic_src_point[0],
                            0)
            vertical_targ = ((current_pos[0] + 0.5) * vertical_vscale * scale \
                                + self.pic_src_point[0],
                             self.size().height())
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])
        
        # draw margin
        l_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(0, 0, l_margin)
        r_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(self.size().width()-self.margin_size,
                                       0, r_margin)
        t_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0, 0, t_margin)
        b_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0,
                                       self.size().height()-self.margin_size,
                                       b_margin)
        # draw orientation label
        # l_str = QString(self.axcodes[0][1])
        # r_str = QString(self.axcodes[0][0])
        # t_str = QString(self.axcodes[1][0])
        # b_str = QString(self.axcodes[1][1])

        l_str = self.axcodes[0][1]
        r_str = self.axcodes[0][0]
        t_str = self.axcodes[1][0]
        b_str = self.axcodes[1][1]

        self.voxels_painter.setPen(QColor(255, 255, 255, 255))
        self.voxels_painter.drawText(7, self.size().height()/2+5, l_str)
        self.voxels_painter.drawText(self.size().width()-12,
                                     self.size().height()/2+5, r_str)
        self.voxels_painter.drawText(self.size().width()/2-5,
                                     15, t_str)
        self.voxels_painter.drawText(self.size().width()/2-1,
                                     self.size().height()-12, b_str)
        
        self.voxels_painter.end()
        self.is_painting = False
        pic.save(file_name)
    
    def draw_voxels(self, voxels):
        """Draw selected voxels."""
        self.voxels_painter.setPen(self.painter_status.get_drawing_color())
        scale = self.model.get_scale_factor('orth') * self._expanding_factor
        points = [QPoint(self.pic_src_point[0] + v[0], 
                         self.pic_src_point[1] + \
                            self.model.getX() * self.voxel_scaler[0] * scale \
                            - v[1])
                  for v in voxels
                  if v[2] == (self.model.get_cross_pos()[2] \
                                * self.voxel_scaler[2] * scale)]
        if points:
            self.voxels_painter.drawPoints(*points)

    def mousePressEvent(self, e):
        """Reimplement mousePressEvent."""
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            if not self.painter_status.is_roi_tool():
                size = self.painter_status.get_drawing_size()
                X = e.x()
                Y = e.y()
                x_margin = self.pic_src_point[0]
                y_margin = self.pic_src_point[1]
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                new_voxels = [(x - x_margin,
                               self.model.getX() \
                                * self.voxel_scaler[0] * scale - y + y_margin, 
                               self.model.get_cross_pos()[2] \
                                * self.voxel_scaler[2] * scale)
                              for x in xrange(X - size/2, X + size/2 + 1)
                              for y in xrange(Y - size/2, Y + size/2 + 1)
                              if self._mouse_in(x, y)]
                self.holder.voxels |= set(new_voxels)
                # draw voxels
                self.drawing = True
                self.repaint()
                self.drawing = False
            else:
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = int(np.floor(x/self.voxel_scaler[1]/scale))
                y = self.model.getX() - 1 - \
                        int(np.floor(y/self.voxel_scaler[0]/scale))
                roi_val = self.model.get_current_roi_val(
                            x, y, self.model.get_cross_pos()[2])
                if roi_val != 0:
                    t_value = self.painter_status.get_drawing_value()
                    self.model.modify_voxels(value=t_value, roi=roi_val)
        elif self.painter_status.is_hand():
            self.setCursor(Qt.ClosedHandCursor)
            self.old_pos = (e.x(), e.y())
        else:
            self.setCursor(Qt.ArrowCursor)
            if self.painter_status.is_roi_selection():
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = int(np.floor(x/self.voxel_scaler[1]/scale))
                y = self.model.getX() - 1 - \
                        int(np.floor(y/self.voxel_scaler[0]/scale))
                roi_val = self.model.get_current_roi_val(
                            x, y, self.model.get_cross_pos()[2])
                if roi_val != 0:
                    self.painter_status.get_draw_settings()._update_roi(roi_val)
            else:
                self.is_moving = True
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            x = e.x() - self.pic_src_point[0]
            y = e.y() - self.pic_src_point[1]
            x = int(np.floor(x/self.voxel_scaler[1]/scale))
            y = self.model.getX() - 1 - \
                    int(np.floor(y/self.voxel_scaler[0]/scale))
            current_pos = [x, y, self.model.get_cross_pos()[2]]
            self.model.set_cross_pos(current_pos)

    def mouseMoveEvent(self, e):
        """Reimplement mouseMoveEvent."""
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            self.setCursor(Qt.CrossCursor)
            size = self.painter_status.get_drawing_size()
            X = e.x()
            Y = e.y()
            x_margin = self.pic_src_point[0]
            y_margin = self.pic_src_point[1]
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            new_voxels = [(x - x_margin, 
                           self.model.getX() \
                            * self.voxel_scaler[0] * scale - y + y_margin, 
                           self.model.get_cross_pos()[2] \
                            * self.voxel_scaler[2] * scale)
                          for x in xrange(X - size/2, X + size/2 + 1)
                          for y in xrange(Y - size/2, Y + size/2 + 1)
                          if self._mouse_in(x, y)]
            self.holder.voxels |= set(new_voxels)
            # draw voxels
            self.drawing = True
            self.repaint()
            self.drawing = False
        elif self.painter_status.is_view():
            self.setCursor(Qt.ArrowCursor)
            if self.is_moving:
                scale=self.model.get_scale_factor('orth')*self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = int(np.floor(x/self.voxel_scaler[1]/scale))
                y = self.model.getX() - 1 - \
                        int(np.floor(y/self.voxel_scaler[0]/scale))
                current_pos = [x, y, self.model.get_cross_pos()[2]]
                self.model.set_cross_pos(current_pos)
        elif self.painter_status.is_hand():
            if self.cursor().shape() == Qt.ArrowCursor:
                self.setCursor(Qt.OpenHandCursor)
            if self.cursor().shape() == Qt.ClosedHandCursor:
                self.new_pos = (e.x(), e.y())
                dist = (self.new_pos[0] - self.old_pos[0],
                        self.new_pos[1] - self.old_pos[1])
                self.old_pos = self.new_pos
                self.pic_src_point = (self.pic_src_point[0] + dist[0],
                                      self.pic_src_point[1] + dist[1])
                self.repaint()
        else:
            self.setCursor(Qt.ArrowCursor)

class CoronalImageLabel(ImageLabel3d):
    """ImageLabel in coronal view."""
    def get_expanding_size(self):
        """Compute a proper expanding size used to display."""
        w_times = float(self.size().width()) / self.model.getY() \
                    / self.voxel_scaler[1]
        h_times = float(self.size().height()) / self.model.getZ() \
                    / self.voxel_scaler[2]
        return np.min([w_times, h_times])

    def paintEvent(self, e):
        """Reimplement paintEvent."""
        self.is_painting = True
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(self)

        self._expanding_factor = self.holder.get_expanding_factor()
        
        if not self.image or not self.drawing:
            back_temp = np.zeros((self.model.getZ(), self.model.getY(), 3), 
                                 dtype=np.uint8)
            blend = reduce(composition, 
                           self.model.get_coronal_rgba_list(),
                           back_temp)
            image = qrgba2qimage(blend)
            self.image = image

        # draw black background
        self.background = self.make_background()
        pm = QPixmap.fromImage(self.background)
        self.voxels_painter.drawPixmap(0, 0, pm)

        # draw volume picture
        pm = QPixmap.fromImage(self.image)
        self.pm = pm.scaled(pm.size().width() * self.voxel_scaler[1] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            pm.size().height() * self.voxel_scaler[2] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            Qt.IgnoreAspectRatio,
                            Qt.FastTransformation)
        if not self.pic_src_point:
            self.pic_src_point = self.center_src_point()
        self.voxels_painter.drawPixmap(self.pic_src_point[0],
                                       self.pic_src_point[1],
                                       self.pm)

        # draw voxels if necessary
        if self.drawing and self.holder.voxels:
            self.draw_voxels(self.holder.voxels)
            
        # draw cross line on picture
        if self.model.display_cross():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[2]
            horizon_src = (0,
                           (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            horizon_targ = (self.size().width(),
                            (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[1]
            vertical_src = ((current_pos[0] + 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                            0)
            vertical_targ = ((current_pos[0] + 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                             self.size().height())
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])
        
        # draw margin
        l_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(0, 0, l_margin)
        r_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(self.size().width()-self.margin_size,
                                       0, r_margin)
        t_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0, 0, t_margin)
        b_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0,
                                       self.size().height()-self.margin_size,
                                       b_margin)
        # draw orientation label
        # l_str = QString(self.axcodes[0][1])
        # r_str = QString(self.axcodes[0][0])
        # t_str = QString(self.axcodes[2][0])
        # b_str = QString(self.axcodes[2][1])

        l_str = self.axcodes[0][1]
        r_str = self.axcodes[0][0]
        t_str = self.axcodes[2][0]
        b_str = self.axcodes[2][1]

        self.voxels_painter.setPen(QColor(255, 255, 255, 255))
        self.voxels_painter.drawText(7, self.size().height()/2+5, l_str)
        self.voxels_painter.drawText(self.size().width()-12,
                                     self.size().height()/2+5, r_str)
        self.voxels_painter.drawText(self.size().width()/2-5,
                                     15, t_str)
        self.voxels_painter.drawText(self.size().width()/2-1,
                                     self.size().height()-12, b_str)
        
        self.voxels_painter.end()
        self.is_painting = False
    
    def save_image(self):
        """Save image as file."""
        file_name = self.__class__.__name__ + '.png'
        pic = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.voxels_painter = QPainter()
        self.voxels_painter.begin(pic)
        self._expanding_factor = self.holder.get_expanding_factor()
        if not self.image or not self.drawing:
            back_temp = np.zeros((self.model.getZ(), self.model.getY(), 3), 
                                 dtype=np.uint8)
            blend = reduce(composition, 
                           self.model.get_coronal_rgba_list(),
                           back_temp)
            image = qrgba2qimage(blend)
            self.image = image

        # draw black background
        self.background = self.make_background()
        pm = QPixmap.fromImage(self.background)
        self.voxels_painter.drawPixmap(0, 0, pm)

        # draw volume picture
        pm = QPixmap.fromImage(self.image)
        self.pm = pm.scaled(pm.size().width() * self.voxel_scaler[1] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            pm.size().height() * self.voxel_scaler[2] \
                                * self.model.get_scale_factor('orth') \
                                * self._expanding_factor,
                            Qt.IgnoreAspectRatio,
                            Qt.FastTransformation)
        if not self.pic_src_point:
            self.pic_src_point = self.center_src_point()
        self.voxels_painter.drawPixmap(self.pic_src_point[0],
                                       self.pic_src_point[1],
                                       self.pm)

        # draw cross line on picture
        if self.model.display_cross():
            self.voxels_painter.setPen(QColor(0, 255, 0, 255))
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            current_pos = self.model.get_cross_pos()
            horizon_vscale = self.voxel_scaler[2]
            horizon_src = (0,
                           (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            horizon_targ = (self.size().width(),
                            (self.model.getZ() - 0.5 - current_pos[2]) \
                                * horizon_vscale * scale \
                                + self.pic_src_point[1])
            self.voxels_painter.drawLine(horizon_src[0],
                                         horizon_src[1],
                                         horizon_targ[0],
                                         horizon_targ[1])
            vertical_vscale = self.voxel_scaler[1]
            vertical_src = ((current_pos[0] + 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                            0)
            vertical_targ = ((current_pos[0] + 0.5) \
                                * vertical_vscale * scale \
                                + self.pic_src_point[0],
                             self.size().height())
            self.voxels_painter.drawLine(vertical_src[0],
                                         vertical_src[1],
                                         vertical_targ[0],
                                         vertical_targ[1])
        
        # draw margin
        l_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(0, 0, l_margin)
        r_margin = QPixmap.fromImage(self.get_ver_margin())
        self.voxels_painter.drawPixmap(self.size().width()-self.margin_size,
                                       0, r_margin)
        t_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0, 0, t_margin)
        b_margin = QPixmap.fromImage(self.get_hor_margin())
        self.voxels_painter.drawPixmap(0,
                                       self.size().height()-self.margin_size,
                                       b_margin)
        # draw orientation label
        # l_str = QString(self.axcodes[0][1])
        # r_str = QString(self.axcodes[0][0])
        # t_str = QString(self.axcodes[2][0])
        # b_str = QString(self.axcodes[2][1])

        l_str = self.axcodes[0][1]
        r_str = self.axcodes[0][0]
        t_str = self.axcodes[2][0]
        b_str = self.axcodes[2][1]

        self.voxels_painter.setPen(QColor(255, 255, 255, 255))
        self.voxels_painter.drawText(7, self.size().height()/2+5, l_str)
        self.voxels_painter.drawText(self.size().width()-12,
                                     self.size().height()/2+5, r_str)
        self.voxels_painter.drawText(self.size().width()/2-5,
                                     15, t_str)
        self.voxels_painter.drawText(self.size().width()/2-1,
                                     self.size().height()-12, b_str)
        
        self.voxels_painter.end()
        self.is_painting = False
        pic.save(file_name)
    
    def draw_voxels(self, voxels):
        """Draw selected voxels."""
        self.voxels_painter.setPen(self.painter_status.get_drawing_color())
        scale = self.model.get_scale_factor('orth') * self._expanding_factor
        points = [QPoint(v[0] + self.pic_src_point[0], 
                         self.model.getZ() \
                            * self.voxel_scaler[2] * scale - v[2] \
                            + self.pic_src_point[1]) 
                  for v in voxels
                  if v[1] == (self.model.get_cross_pos()[1] \
                                * self.voxel_scaler[1] * scale)]
        if points:
            self.voxels_painter.drawPoints(*points)

    def mousePressEvent(self, e):
        """Reimplement mousePressEvent."""
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            if not self.painter_status.is_roi_tool():
                size = self.painter_status.get_drawing_size()
                X = e.x()
                Y = e.y()
                x_margin = self.pic_src_point[0]
                y_margin = self.pic_src_point[1]
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                new_voxels = [(x - x_margin, 
                               self.model.get_cross_pos()[1] \
                                * self.voxel_scaler[0] * scale, 
                               self.model.getZ() \
                                * self.voxel_scaler[2] * scale - y + y_margin)
                              for x in xrange(X - size/2, X + size/2 + 1)
                              for y in xrange(Y - size/2, Y + size/2 + 1)
                              if self._mouse_in(x, y)]
                self.holder.voxels |= set(new_voxels)
                # draw voxels
                self.drawing = True
                self.repaint()
                self.drawing = False
            else:
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = int(np.floor(x/self.voxel_scaler[1]/scale))
                y = self.model.getZ() - 1 - \
                        int(np.floor(y/self.voxel_scaler[2]/scale))
                roi_val = self.model.get_current_roi_val(
                            x, self.model.get_cross_pos()[1], y)
                if roi_val != 0:
                    t_value = self.painter_status.get_drawing_value()
                    self.model.modify_voxels(value=t_value, roi=roi_val)
        elif self.painter_status.is_hand():
            self.setCursor(Qt.ClosedHandCursor)
            self.old_pos = (e.x(), e.y())
        else:
            self.setCursor(Qt.ArrowCursor)
            if self.painter_status.is_roi_selection():
                scale = self.model.get_scale_factor('orth') * \
                        self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = int(np.floor(x/self.voxel_scaler[1]/scale))
                y = self.model.getZ() - 1 - \
                        int(np.floor(y/self.voxel_scaler[2]/scale))
                roi_val = self.model.get_current_roi_val(
                            x, self.model.get_cross_pos()[1], y)
                if roi_val != 0:
                    self.painter_status.get_draw_settings()._update_roi(roi_val)
            else:
                self.is_moving = True
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            x = e.x() - self.pic_src_point[0]
            y = e.y() - self.pic_src_point[1]
            x = int(np.floor(x/self.voxel_scaler[1]/scale))
            y = self.model.getZ() - 1 - \
                    int(np.floor(y/self.voxel_scaler[2]/scale))
            current_pos = [x, self.model.get_cross_pos()[1], y]
            self.model.set_cross_pos(current_pos)

    def mouseMoveEvent(self, e):
        """Reimplement mouseMoveEvent."""
        if not self._mouse_in(e.x(), e.y()):
            return
        if self.painter_status.is_drawing_valid():
            self.setCursor(Qt.CrossCursor)
            size = self.painter_status.get_drawing_size()
            X = e.x()
            Y = e.y()
            x_margin = self.pic_src_point[0]
            y_margin = self.pic_src_point[1]
            scale = self.model.get_scale_factor('orth') * self._expanding_factor
            new_voxels = [(x - x_margin, 
                           self.model.get_cross_pos()[1] \
                            * self.voxel_scaler[0] * scale,
                           self.model.getZ() \
                            * self.voxel_scaler[2] * scale - y + y_margin)
                          for x in xrange(X - size/2, X + size/2 + 1)
                          for y in xrange(Y - size/2, Y + size/2 + 1)
                          if self._mouse_in(x, y)]
            self.holder.voxels |= set(new_voxels)
            # draw voxels
            self.drawing = True
            self.repaint()
            self.drawing = False
        elif self.painter_status.is_view():
            self.setCursor(Qt.ArrowCursor)
            if self.is_moving:
                scale=self.model.get_scale_factor('orth')*self._expanding_factor
                x = e.x() - self.pic_src_point[0]
                y = e.y() - self.pic_src_point[1]
                x = int(np.floor(x/self.voxel_scaler[1]/scale))
                y = self.model.getZ() - 1 - \
                        int(np.floor(y/self.voxel_scaler[2]/scale))
                current_pos = [x, self.model.get_cross_pos()[1], y]
                self.model.set_cross_pos(current_pos)
        elif self.painter_status.is_hand():
            if self.cursor().shape() == Qt.ArrowCursor:
                self.setCursor(Qt.OpenHandCursor)
            if self.cursor().shape() == Qt.ClosedHandCursor:
                self.new_pos = (e.x(), e.y())
                dist = (self.new_pos[0] - self.old_pos[0],
                        self.new_pos[1] - self.old_pos[1])
                self.old_pos = self.new_pos
                self.pic_src_point = (self.pic_src_point[0] + dist[0],
                                      self.pic_src_point[1] + dist[1])
                self.repaint()
        else:
            self.setCursor(Qt.ArrowCursor)
