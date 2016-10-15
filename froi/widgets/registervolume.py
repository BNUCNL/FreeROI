# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import re
import sys
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ..interface.reg_interface import RegisterMethod
import nibabel as nib



class RegisterVolumeDialog(QDialog):
    """A dialog for register volume."""
    def __init__(self, model, source_image_filename, parent=None):
        super(RegisterVolumeDialog, self).__init__(parent)

        self._model = model
        self._temp_dir = os.path.dirname(source_image_filename)
        self._source_image_filename = source_image_filename
        self._auxiliary_image_filename = ''
        self._delta = 0.01

        self._init_gui()
        self._create_actions()

    def _init_gui(self):
        target_image_label = QLabel("Target Image :")
        self._target_image_combo = QComboBox()
        vol_list = self._model.getItemList()
        # self._target_image_combo.addItems(QStringList(vol_list))
        self._target_image_combo.addItems(vol_list)

        source_image = QLabel('Source Image :')
        self._source_image_dir = QLabel('')
        self._source_image_dir.setText(os.path.basename(self._source_image_filename.strip('/')))

        self._auxiliary_image_check = QCheckBox('Auxiliary Image :')
        self._auxiliary_image_check.setChecked(False)
        self._auxiliary_image_dir = QLineEdit('')
        self._auxiliary_image_dir.setReadOnly(True)
        self._auxiliary_image_dir.setVisible(False)
        self._auxiliary_image_button = QPushButton('Browse')
        self._auxiliary_image_button.setVisible(False)

        grid_layout = QGridLayout()
        grid_layout.addWidget(target_image_label, 0, 0, 1, 1)
        grid_layout.addWidget(self._target_image_combo, 0, 1, 1, 2)
        grid_layout.addWidget(source_image, 1, 0, 1, 1)
        grid_layout.addWidget(self._source_image_dir, 1, 1, 1, 2)
        grid_layout.addWidget(self._auxiliary_image_check, 2, 0, 1, 1)
        grid_layout.addWidget(self._auxiliary_image_dir, 2, 1, 1, 1)
        grid_layout.addWidget(self._auxiliary_image_button, 2, 2, 1, 1)

        input_data_group = QGroupBox("Input Data: ")
        input_data_group.setLayout(grid_layout)

        self._fsl_radio = QRadioButton('FSL',self)
        self._spm_radio = QRadioButton('SPM',self)
        radio_group = QButtonGroup()
        radio_group.addButton(self._fsl_radio)
        radio_group.addButton(self._spm_radio)
        if sys.platform == 'win32':
            self._fsl_radio.setChecked(False)
            self._fsl_radio.setEnabled(False)
            self._spm_radio.setChecked(True)
        else:
            self._fsl_radio.setChecked(True)

        self._nearest_neighbour_cb = QCheckBox('Interpolation: Nearest Neighbour')

        radio_group_vlayout = QVBoxLayout()
        radio_group_vlayout.addWidget(self._fsl_radio)
        radio_group_vlayout.addWidget(self._spm_radio)
        radio_group_vlayout.addWidget(self._nearest_neighbour_cb)

        tools_group = QGroupBox("Tools: ")
        tools_group.setLayout(radio_group_vlayout)

        self._register_button = QPushButton("Register")
        self._register_button.setFixedWidth(120)
        self._register_button.adjustSize()

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setFixedWidth(120)
        self._cancel_button.adjustSize()

        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self._register_button)
        hbox_layout.addWidget(self._cancel_button)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(input_data_group)
        vbox_layout.addWidget(tools_group)
        vbox_layout.addLayout(hbox_layout)

        self.setLayout(vbox_layout)
        self.setMinimumSize(500, 300)

        self._progress_dialog = QProgressDialog(self)
        self._progress_dialog.setMinimumWidth(500)
        self._progress_dialog.setRange(0, 100)
        self._progress_dialog.setWindowTitle('Registering')

        self._progress_value = 0.0
        self._update_timer = QTimer(self)
        self.connect(self._update_timer, SIGNAL("timeout()"), self._update_progress)


    def _create_actions(self):
        self._auxiliary_image_button.clicked.connect(self._auxiliary_image_browse)
        self._auxiliary_image_check.clicked.connect(self._auxiliary_image_checkable)
        self._register_button.clicked.connect(self._register)
        self._cancel_button.clicked.connect(self._regester_canceled)
        self.destroyed.connect(self._regester_canceled)
        self._progress_dialog.destroyed.connect(self._regester_canceled)
        self._progress_dialog.canceled.connect(self._regester_canceled)

    def _auxiliary_image_browse(self):
        auxiliary_image_filepath = self._open_file_dialog("Add auxiliary image file.")
        if auxiliary_image_filepath is not None:
            self._temp_dir = os.path.dirname(auxiliary_image_filepath)
            self._auxiliary_image_dir.setText(os.path.basename(auxiliary_image_filepath.strip('/')))
            self._auxiliary_image_filename = auxiliary_image_filepath

    def _auxiliary_image_checkable(self):
        if self._auxiliary_image_check.isChecked():
            self._auxiliary_image_dir.setVisible(True)
            self._auxiliary_image_button.setVisible(True)
        else:
            self._auxiliary_image_dir.setVisible(False)
            self._auxiliary_image_button.setVisible(False)

    def _open_file_dialog(self, title):
        file_name = QFileDialog.getOpenFileName(self,
                                                title,
                                                self._temp_dir,
                                                "Nifti files (*.nii *.nii.gz)")
        import sys
        file_path = None
        if not file_name.isEmpty():
            if sys.platform == 'win32':
                file_path = unicode(file_name).encode('gb2312')
            else:
                file_path = str(file_name)
        return file_path

    def _update_progress(self, error_info=None):
        value = (2. / (1 + math.exp(-self._progress_value)) - 1.01) * 100
        self._progress_dialog.setValue(value)
        self._progress_value += self._delta

    def _regester_finished(self, error_info=None):
        self._progress_dialog.setValue(100)
        self._progress_dialog.close()
        self._progress_value = 0
        self._update_timer.stop()

        if error_info is not None:
            QMessageBox.warning(self,
                                'Warning',
                                error_info,
                                QMessageBox.Yes)
            self._progress_dialog.done(0)
        else:
            res = self._register_thread.get_output()
            if res is not None:
                for filepath in res:
                    basename = os.path.basename(filepath.strip('/'))
                    filename = re.sub(r'(.*)\.nii(\.gz)?', r'\1', basename)
                    new_vol = nib.load(filepath).get_data()
                    if new_vol.shape != self._model._data[0].get_data_shape():
                        QMessageBox.warning(self,
                                            'Warning',
                                            'This error may be caused by SPM for the wrong calculated boundbingbox, '
                                            'you can use FSL instead.',
                                            QMessageBox.Yes)
                        break

                    self._model.addItem(new_vol,
                                        None,
                                        filename,
                                        self._model._data[0].get_header(),
                                        None, None, 255, 'red2yellow')
                    #delete the register file
                    if not sys.platform == 'win32':
                        temp_filename = os.path.join(basename, filename[6:] + '.nii').replace("\\", "/")
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)
                        os.remove(filepath)

        #delete the temp file
        if os.path.exists(self._target_image_filename):
            os.remove(self._target_image_filename)
        self.done(0)

    def _regester_canceled(self):
        self._progress_dialog.close()
        self._progress_value = 0
        if self._update_timer.isActive():
            self._update_timer.stop()
        self.done(0)


    def _register(self):
        if str(self._source_image_dir.text()) is '':
            QMessageBox.warning(self,
                                'Warning',
                                'The target image cannot be empty!',
                                QMessageBox.Yes)
            return

        if not os.access(os.path.dirname(self._temp_dir), os.W_OK):
            QMessageBox.warning(self,
                                'Warning',
                                'The current directory is not writeable. Please copy the opened file to other directory which can be writeable.',
                                QMessageBox.Yes)
            self.done(0)
            return

        target_image_index_row = self._target_image_combo.currentIndex()
        self._target_image_filename = str(self._generate_temp_image_file(target_image_index_row))
        self._register_button.setEnabled(False)

        if self._auxiliary_image_check.isChecked() and self._auxiliary_image_filename is not '':
            if not str(self._auxiliary_image_filename).endswith('.nii'):
                QMessageBox.warning(self,
                                    'Warning',
                                    'The auxiliary image should be ended with .nii, not .nii.gz or anything else.',
                                    QMessageBox.Yes)
                self._register_button.setEnabled(True)
                return
            self._delta = 0.01
            temp_filename = self._source_image_filename
            self._source_image_filename = self._auxiliary_image_filename
            self._auxiliary_image_filename = temp_filename
        else:
            self._auxiliary_image_filename = ''
            self._delta = 0.03

        self._update_timer.start(500)

        self._register_thread = RegisterThread([self._target_image_filename,
                                               str(self._source_image_filename),
                                               str(self._auxiliary_image_filename),
                                               self._nearest_neighbour_cb.isChecked(),
                                               self._fsl_radio.isChecked()])
        self.connect(self._register_thread, SIGNAL("register"), self._regester_finished)
        self._register_thread.start()
        self.hide()
        self._progress_dialog.exec_()


    def _generate_temp_image_file(self, row):
        temp_file_path = os.path.join(self._temp_dir, 'temp_' + str(self._model.data(self._model.index(row), Qt.DisplayRole)) + '.nii')
        if sys.platform == 'win32':
            file_path = unicode(temp_file_path).encode('gb2312')
        else:
            file_path = str(temp_file_path)
        self._model._data[row].save2nifti(file_path)

        return temp_file_path.replace("\\","/")

class RegisterThread(QThread):
    def __init__(self, subreddits):
        QThread.__init__(self)
        self._subreddits = subreddits

        self._target_image_filename = subreddits[0]
        self._source_image_filename = subreddits[1]
        self._auxiliary_image_filename = subreddits[2]
        self._interpolation_method = subreddits[3]
        self._is_fsl = subreddits[4]
        self._output = None

    def __del__(self):
        self.wait()

    def run(self):
        rm = RegisterMethod(self._target_image_filename,
                            self._source_image_filename,
                            self._auxiliary_image_filename,
                            self._interpolation_method)
        res = None
        try:
            if self._is_fsl:
                #fsl register
                res = rm.fsl_register()
            else:
                #detect if the chose file is ended with '.nii', because spm cannot process the .nii.gz file.
                if not str(self._source_image_filename).endswith('.nii'):
                    rm.set_error_info("The source image should be ended with .nii, not .nii.gz or anything else.")
                else:
                    #spm register
                    res = rm.spm_register()
        except Exception as e:
            # 'Register error occur!'
            rm.set_error_info("Error occured! " + str(e))
            if os.path.exists(self._target_image_filename):
                os.remove(self._target_image_filename)

        self._output = res
        self.emit(SIGNAL('register'), rm.get_error_info())

    def get_output(self):
        return self._output


