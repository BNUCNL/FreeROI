# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Graphic User Interface.

"""

import sys
import os
import ConfigParser
import glob
import froi as src_pkg

from froi.version import __version__

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from base.labelconfig import LabelConfig
from base.utils import get_icon_dir
from component.listwidget import LayerView
from component.gridwidget import GridView
from component.orthwidget import OrthView
from component.datamodel import VolumeListModel
from component.imagelabel import ImageLabel
from component.drawsettings import PainterStatus, ViewSettings, MoveSettings
from component.binarizationdialog import BinarizationDialog
from component.intersectdialog import IntersectDialog
from component.localmaxdialog import LocalMaxDialog
from component.no_gui_tools import inverse_image
from component.smoothingdialog import SmoothingDialog
from component.growdialog import GrowDialog
from component.watersheddialog import WatershedDialog
from component.clusterdialog import ClusterDialog
from component.regularroidialog import RegularROIDialog
from component.roi2gwmidialog import Roi2gwmiDialog
from component.no_gui_tools import edge_detection
from component.roimergedialog import ROIMergeDialog
from component.opendialog import OpenDialog
from component.labelconfigcenter import LabelConfigCenter
from component.roidialog import ROIDialog
from component.binaryerosiondialog import BinaryerosionDialog
from component.binarydilationdialog import BinarydilationDialog
from component.greydilationdialog import GreydilationDialog
from component.greyerosiondialog import GreyerosionDialog
from component.meants import MeanTSDialog

class BpMainWindow(QMainWindow):
    """Class BpMainWindow provides UI interface of FreeROI.

    Example:
    --------

    >>> from PyQt4.QtGui import QApplication
    >>> import main
    >>> app = QApplication([])
    >>> win = main.BpMainWindow()
    ......
    >>> win.show()
    >>> app.exec_()

    """

    def __init__(self, parent=None):
        """
        Initialize an instance of BpMainWindow.
        
        """
        # Inherited from QMainWindow
        if sys.platform == 'darwin':
            # Workaround for Qt issue on OS X that causes QMainWindow to
            # hide when adding QToolBar, see
            # https://bugreports.qt-project.org/browse/QTBUG-4300
            super(BpMainWindow, self).__init__(parent,
                                               Qt.MacWindowToolBarButtonHint)
        else:
            super(BpMainWindow, self).__init__(parent)

        # temporary variable
        self._temp_dir = None
        self.is_save_configure = False

        # pre-define a model variable
        self.model = None

    def config_extra_settings(self, data_dir):
        """
        Set data directory and update some configurations.

        """
        # load data directory configuration
        self.label_path = data_dir
        self.label_config_dir = os.path.join(self.label_path, 'labelconfig')
        self.label_config_suffix = 'lbl'

        # set icon configuration
        self._icon_dir = get_icon_dir()

        # set window title
        self.setWindowTitle('FreeROI')
        #self.resize(1280, 1000)
        self.center()
        # set window icon
        self.setWindowIcon(QIcon(os.path.join(self._icon_dir,
                                              'logo.png')))

        self._init_configuration()

        # create actions
        self._create_actions()

        # create menus
        self._create_menus()

    def center(self):
        """
        Display main window in the center of screen

        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _init_configuration(self):
        """
        Load configuration for GUI.

        """
        config_file = os.path.expanduser('~/.pybp.conf')
        if os.path.exists(config_file):
            config = ConfigParser.RawConfigParser()
            config.read(config_file)
            self.window_width = config.getint('width', 'int')
            self.window_height = config.getint('height', 'int')
            self.orth_scale_factor = config.getint('orth_scale', 'int')
            self.grid_scale_factor = config.getint('grid_scale', 'int')
            self.window_xpos = config.getint('xpos', 'int')
            self.window_ypos = config.getint('ypos', 'int')

            self.resize(self.window_width, self.window_height)
            self.move(self.window_xpos, self.window_ypos)
            self.default_orth_scale_factor = float(self.orth_scale_factor) / 100
            self.default_grid_scale_factor = float(self.grid_scale_factor) / 100
        else:
            self.setWindowState(Qt.WindowMaximized)
            self.default_orth_scale_factor = 1.0
            self.default_grid_scale_factor = 2.0

    def _save_configuration(self):
        """
        Save GUI configuration to a file.

        """
        config_file = os.path.expanduser('~/.pybp.conf')

        config = ConfigParser.RawConfigParser()
        config.add_section('width')
        config.add_section('height')
        config.add_section('orth_scale')
        config.add_section('grid_scale')
        config.add_section('xpos')
        config.add_section('ypos')
        config.set('width', 'int', self.width())
        config.set('height', 'int', self.height())
        config.set('xpos', 'int', self.x())
        config.set('ypos', 'int', self.y())
        if hasattr(self, 'model') and isinstance(self.model, VolumeListModel):
            config.set('orth_scale', 'int',
                       int(self.model.get_scale_factor('orth')*100))
            config.set('grid_scale', 'int',
                       int(self.model.get_scale_factor('grid')*100))
        else:
            config.set('orth_scale', 'int',
                       int(self.default_orth_scale_factor * 100))
            config.set('grid_scale', 'int',
                       int(self.default_grid_scale_factor * 100))

        with open(config_file, 'wb') as conf:
            config.write(conf)

    def closeEvent(self, e):
        if self.is_save_configure:
           self._save_configuration()
        e.accept()

    def _create_actions(self):
        """
        Create actions.

        """
        # create a dictionary to store actions info
        self._actions = {}

        # Open template action
        self._actions['add_template'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'open.png')),
                                            self.tr("&Open standard volume"),
                                            self)
        self._actions['add_template'].setShortcut(self.tr("Ctrl+O"))
        self._actions['add_template'].triggered.connect(self._add_template)
        self._actions['add_template'].setEnabled(True)

        # Add a new image action
        self._actions['add_image'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'add.png')),
                                            self.tr("&Add volume"),
                                            self)
        self._actions['add_image'].setShortcut(self.tr("Ctrl+A"))
        self._actions['add_image'].triggered.connect(self._add_image)
        self._actions['add_image'].setEnabled(True)

        # Remove an image
        self._actions['remove_image'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'remove.png')),
                                            self.tr("&Remove volume"),
                                            self)
        self._actions['remove_image'].setShortcut(self.tr("Ctrl+R"))
        self._actions['remove_image'].triggered.connect(self._remove_image)
        self._actions['remove_image'].setEnabled(False)

        # New image
        self._actions['new_image'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'create.png')),
                                             self.tr("&New volume"),
                                             self)
        self._actions['new_image'].setShortcut(self.tr("Ctrl+N"))
        self._actions['new_image'].triggered.connect(self.__new_image)
        self._actions['new_image'].setEnabled(False)

        # Save image
        self._actions['save_image'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'save.png')),
                                              self.tr("&Save volume as..."),
                                              self)
        self._actions['save_image'].setShortcut(self.tr("Ctrl+S"))
        self._actions['save_image'].triggered.connect(self._save_image)
        self._actions['save_image'].setEnabled(False)

        ## Load Label Config
        #self._actions['ld_lbl'] = QAction('Load Label', self)
        #self._actions['ld_lbl'].triggered.connect(self._ld_lbl)
        #self._actions['ld_lbl'].setEnabled(False)

        ## Load Global Label Config
        #self._actions['ld_glbl'] = QAction('Load Global Label', self)
        #self._actions['ld_glbl'].triggered.connect(self._ld_glbl)
        #self._actions['ld_glbl'].setEnabled(False)

        # Close display
        self._actions['close'] = QAction(self.tr("Close"), self)
        self._actions['close'].setShortcut(self.tr("Ctrl+W"))
        self._actions['close'].triggered.connect(self._close_display)
        self._actions['close'].setEnabled(False)

        # Quit action
        self._actions['quit'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'quit.png')),
                                        self.tr("&Quit"),
                                        self)
        self._actions['quit'].setShortcut(self.tr("Ctrl+Q"))
        self._actions['quit'].triggered.connect(self.close)

        # Grid view action
        self._actions['grid_view'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'gridview.png')),
                                             self.tr("Lightbox"),
                                             self)
        self._actions['grid_view'].triggered.connect(self._grid_view)
        self._actions['grid_view'].setEnabled(False)

        # Orth view action
        self._actions['orth_view'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'orthview.png')),
                                             self.tr("Orthographic"),
                                             self)
        self._actions['orth_view'].triggered.connect(self._orth_view)
        self._actions['orth_view'].setEnabled(False)

        # return original size
        self._actions['original_view'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'original_size.png')),
                                                 self.tr("Reset view"),
                                                 self)
        self._actions['original_view'].triggered.connect(self._reset_view)
        self._actions['original_view'].setEnabled(False)

        # whether display the cross hover
        self._actions['cross_hover_view'] = QAction(QIcon(os.path.join(
                                    self._icon_dir, 'cross_hover_enable.png')),
                                                self.tr("Disable cross hover"),
                                                self)
        self._actions['cross_hover_view'].triggered.connect(
                                            self._display_cross_hover)
        self._actions['cross_hover_view'].setEnabled(False)

        # Binaryzation view action
        self._actions['binarization'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'binarization.png')),
                                                self.tr("Binarization"),
                                                self)
        self._actions['binarization'].triggered.connect(self._binarization)
        self._actions['binarization'].setEnabled(False)

        # Intersection action
        self._actions['intersect'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'intersect.png')),
                                             self.tr("Intersection"),
                                             self)
        self._actions['intersect'].triggered.connect(self._intersect)
        self._actions['intersect'].setEnabled(False)

        # Extract mean time course
        self._actions['meants'] = QAction(QIcon(os.path.join(self._icon_dir,
                                                            'voxel_curve.png')),
                                          self.tr("Extract Mean Time Course"),
                                          self)
        self._actions['meants'].triggered.connect(self._meants)
        self._actions['meants'].setEnabled(False)
        
        # Local Max action
        self._actions['localmax'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'localmax.png')),
                                             self.tr("Local Max"),
                                             self)
        self._actions['localmax'].triggered.connect(self._local_max)
        self._actions['localmax'].setEnabled(False)

        # Inversion action
        self._actions['inverse'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'inverse.icon')),
                                             self.tr("Inversion"),
                                             self)
        self._actions['inverse'].triggered.connect(self._inverse)
        self._actions['inverse'].setEnabled(False)

        # Smoothing action
        self._actions['smoothing'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'smoothing.png')),
                                             self.tr("Smoothing"),
                                             self)
        self._actions['smoothing'].triggered.connect(self._smooth)
        self._actions['smoothing'].setEnabled(False)

        # Region Growing action
        self._actions['region_grow'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'grow.png')),
                                             self.tr("Region Growing"),
                                             self)
        self._actions['region_grow'].triggered.connect(self._region_grow)
        self._actions['region_grow'].setEnabled(False)

        # Watershed action
        self._actions['watershed'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'watershed.png')),
                                             self.tr("Watershed"),
                                             self)
        self._actions['watershed'].triggered.connect(self._watershed)
        self._actions['watershed'].setEnabled(False)

        # Cluster action
        self._actions['cluster'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'cluster.png')),
                                             self.tr("Cluster"),
                                             self)
        self._actions['cluster'].triggered.connect(self._cluster)
        self._actions['cluster'].setEnabled(False)

        # Opening
        self._actions['opening'] = QAction(self.tr("Opening"), self)
        self._actions['opening'].triggered.connect(self._opening)
        self._actions['opening'].setEnabled(False)

        # Binary_erosion view action
        self._actions['binaryerosion'] = QAction(self.tr("Binary Erosion"),
                                                 self)
        self._actions['binaryerosion'].triggered.connect(self._binaryerosion)
        self._actions['binaryerosion'].setEnabled(False)

        # Binary_dilation view action
        self._actions['binarydilation'] = QAction(self.tr("Binary Dilation"),
                                                  self)
        self._actions['binarydilation'].triggered.connect(self._binarydilation)
        self._actions['binarydilation'].setEnabled(False)

        # grey_erosion view action
        self._actions['greyerosion'] = QAction(self.tr("Grey Erosion"),
                                               self)
        self._actions['greyerosion'].triggered.connect(self._greyerosion)
        self._actions['greyerosion'].setEnabled(False)

        # grey_dilation view action
        self._actions['greydilation'] = QAction(self.tr("Grey Dilation"),
                                                self)
        self._actions['greydilation'].triggered.connect(self._greydilation)
        self._actions['greydilation'].setEnabled(False)

        # About software
        self._actions['about_pybp'] = QAction(self.tr("About FreeROI"), self)
        self._actions['about_pybp'].triggered.connect(self._about_pybp)

        # About Qt
        self._actions['about_qt'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'qt.png')),
                                            self.tr("About Qt"),
                                            self)
        self._actions['about_qt'].triggered.connect(qApp.aboutQt)

        # Hand
        self._actions['hand'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'hand.png')),
                                        self.tr("Hand"),
                                        self)
        self._actions['hand'].triggered.connect(self._hand_enable)
        self._actions['hand'].setCheckable(True)
        self._actions['hand'].setChecked(False)
        self._actions['hand'].setEnabled(False)

        # Cursor
        self._actions['cursor'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'cursor.png')),
                                          self.tr("Cursor"),
                                          self)
        self._actions['cursor'].triggered.connect(self._cursor_enable)
        self._actions['cursor'].setCheckable(True)
        self._actions['cursor'].setChecked(True)
        self._actions['cursor'].setEnabled(True)

        # Edit
        self._actions['edit'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'edit.png')),
                                         self.tr("Edit"), self)
        self._actions['edit'].triggered.connect(self._roidialog_enable)
        self._actions['edit'].setCheckable(True)
        self._actions['edit'].setChecked(False)

        # Undo
        self._actions['undo'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'undo.png')),
                                        self.tr("Undo"),
                                        self)
        self._actions['undo'].triggered.connect(self._undo)

        # Redo
        self._actions['redo'] = QAction(QIcon(os.path.join(
                                            self._icon_dir, 'redo.png')),
                                        self.tr("Redo"),
                                        self)
        self._actions['redo'].triggered.connect(self._redo)

        # sphere and cube roi
        self._actions['regular_roi'] = QAction(QIcon(os.path.join(
                                                self._icon_dir,
                                                'sphere_and_cube.png')),
                                               self.tr("Regular ROI"), self)
        self._actions['regular_roi'].triggered.connect(self._regular_roi)
        self._actions['regular_roi'].setEnabled(False)

        # ROI to Interface
        self._actions['r2i'] = QAction(QIcon(os.path.join(
                                        self._icon_dir, 'r2i.png')),
                                       self.tr("ROI2Interface"), self)
        self._actions['r2i'].triggered.connect(self._r2i)
        self._actions['r2i'].setEnabled(False)

        # Edge detection for ROI
        self._actions['edge_dete'] = QAction(QIcon(os.path.join(
                                                self._icon_dir,
                                                'edge_detection.png')),
                                             self.tr("Edge Detection"), self)
        self._actions['edge_dete'].triggered.connect(self._edge_detection)
        self._actions['edge_dete'].setEnabled(False)

        # ROI Merging
        self._actions['roi_merge'] = QAction(QIcon(os.path.join(
                                                self._icon_dir, 'merging.png')),
                                             self.tr("ROI Merging"), self)
        self._actions['roi_merge'].triggered.connect(self._roi_merge)
        self._actions['roi_merge'].setEnabled(False)

    def _add_toolbar(self):
        """
        Add toolbar.

        """
        # Initialize a spinbox for zoom-scale selection
        self._spinbox = QSpinBox()
        self._spinbox.setMaximum(500)
        self._spinbox.setMinimum(50)
        self._spinbox.setSuffix('%')
        self._spinbox.setSingleStep(10)
        self._spinbox.setValue(self.default_grid_scale_factor * 100)
        self._spinbox.valueChanged.connect(self._set_scale_factor)

        # Add a toolbar
        self._toolbar = self.addToolBar("Tools")
        #self._toolbar.setIconSize(QSize(38,38))
        # Add file actions
        self._toolbar.addAction(self._actions['add_image'])
        self._toolbar.addAction(self._actions['remove_image'])
        self._toolbar.addAction(self._actions['new_image'])
        self._toolbar.addAction(self._actions['save_image'])
        # Add view actions
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._actions['grid_view'])
        self._toolbar.addAction(self._actions['orth_view'])
        self._toolbar.addAction(self._actions['original_view'])
        self._toolbar.addAction(self._actions['cross_hover_view'])
        # Add cursor status
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._actions['hand'])
        self._toolbar.addAction(self._actions['cursor'])
        self._toolbar.addAction(self._actions['edit'])
        # Add undo redo
        self._toolbar.addSeparator()
        self._toolbar.addAction(self._actions['undo'])
        self._toolbar.addAction(self._actions['redo'])

        self._toolbar.addSeparator()
        self._toolbar.addWidget(self._spinbox)

    def _set_scale_factor(self, value):
        """
        Set scale factor.

        """
        value = float(value) / 100
        self.model.set_scale_factor(value, self.image_view.display_type())

    def _add_template(self):
        """
        Open a dialog window and select a template file.

        """
        template_dir = os.path.join(self.label_path, 'standard',
                                    'MNI152_T1_2mm_brain.nii.gz')
        template_name = QFileDialog.getOpenFileName(
            self,
            'Open standard file',
            template_dir,
            'Nifti files (*.nii.gz *.nii)')
        if not template_name.isEmpty():
            if sys.platform == 'win32':
                template_path = unicode(template_name).encode('gb2312')
            else:
                template_path = str(template_name)
            self._add_img(template_path)

    def _add_image(self):
        """
        Add new item.

        """
        if self._temp_dir == None:
            temp_dir = QDir.currentPath()
        else:
            temp_dir = self._temp_dir
        file_name = QFileDialog.getOpenFileName(self,
                                                'Add new file',
                                                temp_dir,
                                                'Nifti files (*.nii.gz *.nii)')
        if not file_name.isEmpty():
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
            self._add_img(file_path)

    def _add_img(self, source, name=None, header=None, view_min=None,
                 view_max=None, alpha=255, colormap='gray'):
        """
        Add image.

        """
        # If model is NULL, then re-initialize it.
        if not self.model:
            self._init_label_config_center()
            self.model = VolumeListModel([], self._label_config_center)
            self.model.set_scale_factor(self.default_grid_scale_factor, 'grid')
            self.model.set_scale_factor(self.default_orth_scale_factor, 'orth')
            self.painter_status = PainterStatus(ViewSettings())

        # Save previous opened directory (except `standard` directory)
        file_path = source
        if sys.platform == 'win32':
            temp_dir = os.path.dirname(unicode(file_path, 'gb2312'))
            if not os.stat(temp_dir) == os.stat(os.path.join(self.label_path,
                                                             'standard')):
                self._temp_dir = temp_dir
        else:
            temp_dir = os.path.dirname(file_path)
            if not os.path.samefile(temp_dir, os.path.join(self.label_path,
                                                           'standard')):
                self._temp_dir = temp_dir

        if self.model.addItem(file_path, None, name, header, view_min,
                              view_max, alpha, colormap):
            # Take different acions in different case.
            # If only one data in VolumeList, then initialize views.
            if self.model.rowCount() == 1:
                # initialize views
                self.list_view = LayerView(self._label_config_center)
                self.list_view.setModel(self.model)
                self._init_roi_dialog()
                self.image_view = GridView(self.model, self.painter_status)
                # initialize display layout
                central_widget = QWidget()
                layout = QHBoxLayout()
                central_widget.setLayout(layout)
                central_widget.layout().addWidget(self.list_view)
                central_widget.layout().addWidget(self.image_view)
                self.setCentralWidget(central_widget)
                # add a toolbar
                self._add_toolbar()
                #self.setUnifiedTitleAndToolBarOnMac(True)
                # change button status
                self._actions['save_image'].setEnabled(True)
                #self._actions['ld_lbl'].setEnabled(True)
                #self._actions['ld_glbl'].setEnabled(True)
                self._actions['new_image'].setEnabled(True)
                self._actions['close'].setEnabled(True)
                self._actions['orth_view'].setEnabled(True)
                self._actions['cross_hover_view'].setEnabled(True)
                self._actions['original_view'].setEnabled(True)
                self._actions['undo'].setEnabled(False)
                self._actions['redo'].setEnabled(False)
                self._functional_module_set_enabled(True)
                # connect signals with slots
                self.list_view.current_changed.connect(self._update_undo)
                self.list_view.current_changed.connect(self._update_redo)
                self.model.rowsInserted.connect(self._update_remove_image)
                self.model.undo_stack_changed.connect(self._update_undo)
                self.model.redo_stack_changed.connect(self._update_redo)
                # set current volume index
                self.list_view.setCurrentIndex(self.model.index(0))
                # set crosshair as the center of the data
                self.model.set_cross_pos([self.model.getY()/2,
                                          self.model.getX()/2,
                                          self.model.getZ()/2])
                ## Enable cursor tracking
                # self.list_view._list_view.selectionModel().currentChanged.connect(
                #                self._switch_cursor_status)
            elif self.model.rowCount() > 1:
                self._actions['remove_image'].setEnabled(True)
                # set current volume index
                self.list_view.setCurrentIndex(self.model.index(0))
            self.is_save_configure = True
        else:
            QMessageBox.information(self,'FreeROI', 'Cannot load ' + "filename" + '.')

    def __new_image(self):
        self._new_image()

    def _update_remove_image(self):
        if self.model.rowCount() == 1:
            self._actions['remove_image'].setEnabled(False)
        else:
            self._actions['remove_image'].setEnabled(True)

    def _new_image(self, data=None, name=None, colormap=None):
        """
        Create a new volume for brain parcellation.

        """
        if colormap is None:
            colormap = self._label_config_center.get_first_label_config()
        self.model.new_image(data, name, None, colormap)
        self.list_view.setCurrentIndex(self.model.index(0))

        # change button status
        self._actions['remove_image'].setEnabled(True)

    def new_image_action(self):
        self._actions['remove_image'].setEnabled(True)

    def _remove_image(self):
        """
        Remove current image.

        """
        row = self.list_view.currentRow()
        self.model.delItem(row)
        if self.model.rowCount() == 1:
            self._actions['remove_image'].setEnabled(False)

    def _save_image(self):
        """
        Save image as a nifti file.

        """
        index = self.model.currentIndex()
        if self._temp_dir == None:
            temp_dir = str(QDir.currentPath())
        else:
            temp_dir = self._temp_dir
        file_path = os.path.join(temp_dir,
                                 str(self.model.data(index, Qt.DisplayRole))+'.nii.gz')
        path = QFileDialog.getSaveFileName(
            self,
            'Save image as...',
            file_path,
            'Nifti files (*.nii.gz *.nii)')
        if not path.isEmpty():
            if sys.platform == 'win32':
                path = unicode(path).encode('gb2312')
                self._temp_dir = os.path.dirname(unicode(path, 'gb2312'))
            else:
                path = str(path)
                self._temp_dir = os.path.dirname(path)
            self.model._data[index.row()].save2nifti(path)

    def _close_display(self):
        """
        Close current display.

        """
        self.setCentralWidget(QWidget())
        self._set_scale_factor(self.default_grid_scale_factor)
        self.removeToolBar(self._toolbar)
        self.model = None
        self._actions['add_template'].setEnabled(True)
        self._actions['add_image'].setEnabled(True)
        self._actions['remove_image'].setEnabled(False)
        self._actions['new_image'].setEnabled(False)
        self._actions['save_image'].setEnabled(False)
        #self._actions['ld_glbl'].setEnabled(False)
        #self._actions['ld_lbl'].setEnabled(False)
        self._actions['close'].setEnabled(False)
        self._actions['grid_view'].setEnabled(False)
        self._actions['orth_view'].setEnabled(False)
        self._actions['cross_hover_view'].setEnabled(False)
        self._actions['original_view'].setEnabled(False)
        self._functional_module_set_enabled(False)

    def _about_pybp(self):
        """
        About software.

        """
        QMessageBox.about(self, self.tr("About FreeROI"),
                          self.tr("<p><b>FreeROI</b> is a versatile image "
                                  "processing software developed for "
                                  "neuroimaging data.</p>"
                                  "<p>Its goal is to provide a user-friendly "
                                  "interface for neuroimaging researchers "
                                  "to visualize and analyze their data, "
                                  "especially in defining region of interest "
                                  "(ROI) for ROI analysis.</p>"
                                  "<p>Version: " + __version__ + "</p>"
                                  "<p>Written by: Lijie Huang, Zetian Yang, "
                                  "Guangfu Zhou, Zhaoguo Liu, Xiaobin Dang, "
                                  "Xiangzhen Kong, Xu Wang, and Zonglei Zhen."
                                  "</p>"
                                  "<p><b>FreeROI</b> is under Revised BSD "
                                  "License.</p>"
                                  "<p>Copyright(c) 2012-2014 "
                                  "Neuroinformatic Team in LiuLab "
                                  "from Beijing Normal University</p>"
                                  "<p></p>"
                                  "<p>Please join and report bugs to:</p>"
                                  "<p><b>nitk-user@googlegroups.com</b></p>"))

    def _create_menus(self):
        """Create menus."""
        self.file_menu = self.menuBar().addMenu(self.tr("File"))
        self.file_menu.addAction(self._actions['add_image'])
        self.file_menu.addAction(self._actions['add_template'])
        self.file_menu.addAction(self._actions['save_image'])
        #self.file_menu.addSeparator()
        #self.file_menu.addAction(self._actions['ld_lbl'])
        #self.file_menu.addAction(self._actions['ld_glbl'])
        self.file_menu.addSeparator()
        self.file_menu.addAction(self._actions['close'])
        self.file_menu.addAction(self._actions['quit'])

        self.volume_menu = self.menuBar().addMenu(self.tr("Volume"))
        self.volume_menu.addAction(self._actions['new_image'])
        self.volume_menu.addAction(self._actions['remove_image'])

        self.view_menu = self.menuBar().addMenu(self.tr("View"))
        self.view_menu.addAction(self._actions['grid_view'])
        self.view_menu.addAction(self._actions['orth_view'])
        self.view_menu.addAction(self._actions['original_view'])
        self.view_menu.addAction(self._actions['cross_hover_view'])

        self.tool_menu = self.menuBar().addMenu(self.tr("Tools"))
        basic_tools = self.tool_menu.addMenu(self.tr("Basic Tools"))
        basic_tools.addAction(self._actions['binarization'])
        basic_tools.addAction(self._actions['intersect'])
        basic_tools.addAction(self._actions['localmax'])
        basic_tools.addAction(self._actions['inverse'])
        basic_tools.addAction(self._actions['smoothing'])
        basic_tools.addAction(self._actions['meants'])
        segment_tools = self.tool_menu.addMenu(self.tr("Segmentation"))
        segment_tools.addAction(self._actions['region_grow'])
        segment_tools.addAction(self._actions['watershed'])
        segment_tools.addAction(self._actions['cluster'])
        roi_tools = self.tool_menu.addMenu(self.tr("ROI Tools"))
        roi_tools.addAction(self._actions['edge_dete'])
        roi_tools.addAction(self._actions['roi_merge'])
        roi_tools.addAction(self._actions['regular_roi'])
        roi_tools.addAction(self._actions['r2i'])
        morphological_tools = self.tool_menu.addMenu(
                                    self.tr("Morphological Processing"))
        morphological_tools.addAction(self._actions['opening'])
        morphological_tools.addAction(self._actions['binarydilation'])
        morphological_tools.addAction(self._actions['binaryerosion'])
        morphological_tools.addAction(self._actions['greydilation'])
        morphological_tools.addAction(self._actions['greyerosion'])

        self.help_menu = self.menuBar().addMenu(self.tr("Help"))
        self.help_menu.addAction(self._actions['about_pybp'])
        self.help_menu.addAction(self._actions['about_qt'])

    def _cursor_enable(self):
        """
        Cursor enabled.

        """
        if self._actions['cursor'].isChecked():
            self._actions['cursor'].setChecked(True)
            if isinstance(self.image_view, OrthView):
                self._actions['hand'].setChecked(False)
            if self.roidialog.isVisible():
                self._roidialog_disable()

            self.painter_status.set_draw_settings(ViewSettings())
            self.image_view.set_cursor(Qt.ArrowCursor)
            self.image_view.set_label_mouse_tracking(True)
        else:
            self._actions['cursor'].setChecked(True)

    def _voxel_edit_enable(self):
        """
        Brush enabled.

        """
        self._label_config_center.set_is_roi_edit(False)
        self.painter_status.set_draw_settings(self._label_config_center)
        self.image_view.set_cursor(Qt.CrossCursor)
        self.image_view.set_label_mouse_tracking(False)

    def _roi_edit_enable(self):
        """
        ROI brush enabled.

        """
        self._label_config_center.set_is_roi_edit(True)
        self.painter_status.set_draw_settings(self._label_config_center)
        self.image_view.set_cursor(Qt.CrossCursor)
        self.image_view.set_label_mouse_tracking(False)

    def _roidialog_enable(self):
        if self._actions['edit'].isChecked():
            self._actions['cursor'].setChecked(False)
            if isinstance(self.image_view, OrthView):
                self._actions['hand'].setChecked(False)
            self._actions['edit'].setChecked(True)
            self.roidialog._voxel_clicked()
            self.roidialog.show()
        else:
            self._actions['edit'].setChecked(True)

    def _roi_batch_enable(self):
        self.image_view.set_label_mouse_tracking(False)
        self._label_config_center.set_is_roi_edit(False)
        self.painter_status.set_draw_settings(self.roidialog)

    def _roidialog_disable(self):
        self.roidialog.hide()
        self._actions['edit'].setChecked(False)

    def _hand_enable(self):
        """
        Hand enabled.

        """
        if self._actions['hand'].isChecked():
            self._actions['cursor'].setChecked(False)
            self._actions['hand'].setChecked(True)
 
            if hasattr(self, 'roidialog'):
                self._roidialog_disable()

            self.painter_status.set_draw_settings(MoveSettings())
            self.image_view.set_cursor(Qt.OpenHandCursor)
            self.image_view.set_label_mouse_tracking(True)
        else:
            self._actions['hand'].setChecked(True)

    def _switch_cursor_status(self):
        self._actions['cursor'].setChecked(True)
        self._cursor_enable()

    def _update_undo(self):
        if self.model.current_undo_available():
            self._actions['undo'].setEnabled(True)
        else:
            self._actions['undo'].setEnabled(False)

    def _update_redo(self):
        if self.model.current_redo_available():
            self._actions['redo'].setEnabled(True)
        else:
            self._actions['redo'].setEnabled(False)

    def _init_roi_dialog(self):
        """
        Initialize ROI Dialog

        """
        self.roidialog = ROIDialog(self.model, self._label_config_center, self)
        self.roidialog.voxel_edit_enabled.connect(self._voxel_edit_enable)
        self.roidialog.roi_edit_enabled.connect(self._roi_edit_enable)
        self.roidialog.roi_batch_enabled.connect(self._roi_batch_enable)
        self.list_view._list_view.selectionModel().currentChanged.connect(
                self.roidialog.clear_rois)

    def _init_label_config_center(self):
        """
        Initialize LabelConfigCenter

        """
        lbl_path = os.path.join(self.label_config_dir,
                                '*.' + self.label_config_suffix)
        label_configs = glob.glob(lbl_path)
        self.label_configs = map(LabelConfig, label_configs)
        self._label_config_center = LabelConfigCenter(self.label_configs)

    def _get_label_config(self, file_path):
        """
        Get label config file.

        """
        # Get label config file
        dir = os.path.dirname(file_path)
        file = os.path.basename(file_path)
        split_list = file.split('.')
        nii_index = split_list.index('nii')
        file = ''.join(split_list[:nii_index])
        config_file = os.path.join(file, 'lbl')
        if os.path.isfile(config_file):
            label_config = LabelConfig(config_file, False)
        else:
            label_config = self.label_config

        return label_config

    def _undo(self):
        self.model.undo_current_image()

    def _redo(self):
        self.model.redo_current_image()

    def _regular_roi(self):
        regular_roi_dialog = RegularROIDialog(self.model)
        regular_roi_dialog.exec_()

    def _edge_detection(self):
        edge_detection(self.model)

    def _roi_merge(self):
        new_dialog = ROIMergeDialog(self.model)
        new_dialog.exec_()

    def _r2i(self):
        new_dialog = Roi2gwmiDialog(self.model)
        new_dialog.exec_()

    def _opening(self):
        new_dialog = OpenDialog(self.model)
        new_dialog.exec_()

    def _ld_lbl(self):
        file_name = QFileDialog.getOpenFileName(self,
                                                'Load Label File',
                                                QDir.currentPath(),
                                                "Label files (*.lbl)")
        if file_name:
            label_config = LabelConfig(str(file_name), False)
            self.model.set_cur_label(label_config)

    def _ld_glbl(self):
        file_name = QFileDialog.getOpenFileName(self,
                                                'Load Label File',
                                                QDir.currentPath(),
                                                "Label files (*.lbl)")
        if file_name:
            label_config = LabelConfig(str(file_name), True)
            self.model.set_global_label(label_config)

    def _grid_view(self):
        """
        Grid view option.

        """
        self._actions['grid_view'].setEnabled(False)
        self._actions['orth_view'].setEnabled(True)
        self._actions['hand'].setEnabled(False)
        self._actions['cursor'].trigger()

        self.centralWidget().layout().removeWidget(self.image_view)
        self.image_view.set_display_type('grid')
        self.model.scale_changed.disconnect()
        self.model.repaint_slices.disconnect()
        self.model.cross_pos_changed.disconnect(self.image_view.update_cross_pos)
        self.image_view.deleteLater()
        self._spinbox.setValue(100 * self.model.get_scale_factor('grid'))
        self.image_view = GridView(self.model, self.painter_status,
                                   self._gridview_vertical_scrollbar_position)
        self.centralWidget().layout().addWidget(self.image_view)

    def _orth_view(self):
        """
        Orth view option.
        """


        self._actions['orth_view'].setEnabled(False)
        self._actions['grid_view'].setEnabled(True)
        self._actions['hand'].setEnabled(True)
        self._actions['cursor'].trigger()

        self._gridview_vertical_scrollbar_position = \
            self.image_view.get_vertical_srollbar_position()
        self.centralWidget().layout().removeWidget(self.image_view)
        self.image_view.set_display_type('orth')
        self.model.scale_changed.disconnect()
        self.model.repaint_slices.disconnect()
        self.model.cross_pos_changed.disconnect(self.image_view.update_cross_pos)
        self.image_view.deleteLater()
        self._spinbox.setValue(100 * self.model.get_scale_factor('orth'))
        self.image_view = OrthView(self.model, self.painter_status)
        self.centralWidget().layout().addWidget(self.image_view)

    def _display_cross_hover(self):
        if self.model._display_cross:
            self.model.set_cross_status(False)
            self._actions['cross_hover_view'].setText('Enable cross hover')
            self._actions['cross_hover_view'].setIcon(QIcon(os.path.join(self._icon_dir,'cross_hover_disable.png')))
        else:
            self.model.set_cross_status(True)
            self._actions['cross_hover_view'].setText('Disable cross hover')
            self._actions['cross_hover_view'].setIcon(QIcon(os.path.join(self._icon_dir,'cross_hover_enable.png')))

    def _reset_view(self):
        """
        Reset view parameters.

        """
        if self.image_view.display_type() == 'orth':
            if not self.model.get_scale_factor('orth') == \
                    self.default_orth_scale_factor:
                self._spinbox.setValue(100 * self.default_orth_scale_factor)
            self.image_view.reset_view()
        elif self.image_view.display_type() == 'grid':
            if not self.model.get_scale_factor('grid') == \
                    self.default_grid_scale_factor:
                self._spinbox.setValue(100 * self.default_grid_scale_factor)

    def _binarization(self):
        binarization_dialog = BinarizationDialog(self.model)
        binarization_dialog.exec_()

    def _binaryerosion(self):
        binaryerosion_dialog = BinaryerosionDialog(self.model)
        binaryerosion_dialog.exec_()

    def _binarydilation(self):
        binarydilation_dialog = BinarydilationDialog(self.model)
        binarydilation_dialog.exec_()

    def _greyerosion(self):
        greyerosiondialog = GreyerosionDialog(self.model)
        greyerosiondialog.exec_()

    def _greydilation(self):
        greydilation_dialog = GreydilationDialog(self.model)
        greydilation_dialog.exec_()

    def _intersect(self):
        intersect_dialog = IntersectDialog(self.model)
        intersect_dialog.exec_()

    def _meants(self):
        new_dialog = MeanTSDialog(self.model)
        new_dialog.exec_()

    def _local_max(self):
        new_dialog = LocalMaxDialog(self.model, self)
        new_dialog.exec_()

    def _inverse(self):
        inverse_image(self.model)

    def _smooth(self):
        new_dialog = SmoothingDialog(self.model)
        new_dialog.exec_()

    def _region_grow(self):
        new_dialog = GrowDialog(self.model, self)
        new_dialog.exec_()

    def _watershed(self):
        new_dialog = WatershedDialog(self.model, self)
        new_dialog.exec_()

    def _cluster(self):
        new_dialog = ClusterDialog(self.model)
        new_dialog.exec_()

    def _functional_module_set_enabled(self, status):
        self._actions['binarization'].setEnabled(status)
        self._actions['intersect'].setEnabled(status)
        self._actions['meants'].setEnabled(status)
        self._actions['localmax'].setEnabled(status)
        self._actions['inverse'].setEnabled(status)
        self._actions['smoothing'].setEnabled(status)
        self._actions['region_grow'].setEnabled(status)
        self._actions['watershed'].setEnabled(status)
        self._actions['cluster'].setEnabled(status)
        self._actions['opening'].setEnabled(status)
        self._actions['binarydilation'].setEnabled(status)
        self._actions['binaryerosion'].setEnabled(status)
        self._actions['greydilation'].setEnabled(status)
        self._actions['greyerosion'].setEnabled(status)
        self._actions['regular_roi'].setEnabled(status)
        self._actions['r2i'].setEnabled(status)
        self._actions['edge_dete'].setEnabled(status)
        self._actions['roi_merge'].setEnabled(status)

