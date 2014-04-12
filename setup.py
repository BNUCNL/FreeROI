# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import sys
import os
import numpy
import sipdistutils
from distutils.core import setup, Extension

import PyQt4.pyqtconfig

config = PyQt4.pyqtconfig.Configuration()

#-- PyQt4 library configuration

# Replace the following with
#  qt_inc_dir = "path/to/Qt/include"
#  qt_lib_dir = "path/to/Qt/lib"
# when automatically extracted paths don't fit your installation.
# (Note that you should use a compatible compiler and Qt version
# as was used for building PyQt.)
qt_inc_dir = config.qt_inc_dir
qt_lib_dir = config.qt_lib_dir

#--

qt_lib_dirs = [qt_lib_dir]
qt_libraries = ['QtCore', 'QtGui']

if 'mingw32' in sys.argv:
    # Need better criterion - this should only apply to mingw32
    qt_lib_dirs.extend((qt_lib_dir.replace(r'\lib', r'\bin'),
                        os.path.dirname(PyQt4.__file__)))
    qt_libraries = [lib + '4' for lib in qt_libraries]

qimageview = Extension('froi.algorithm.qimageview',
                       sources=[r'3rdparty/qimageview.sip'],
                       include_dirs=[numpy.get_include(),
                                     qt_inc_dir,
                                     os.path.join(qt_inc_dir, 'QtCore'),
                                     os.path.join(qt_inc_dir, 'QtGui')])
if sys.platform == 'darwin':
    # Qt is distributed as 'framwork' on OS X
    for lib in qt_libraries:
        qimageview.extra_link_args.extend(['-framework', lib])
    for d in qt_lib_dirs:
        qimageview.extra_link_args.append('-F' + d)
else:
    qimageview.libraries.extend(qt_libraries)
    qimageview.library_dirs.extend(qt_lib_dirs)


class build_ext(sipdistutils.build_ext):
    def _sip_compile(self, sip_bin, source, sbf):
        import PyQt4.pyqtconfig
        config = PyQt4.pyqtconfig.Configuration()
        self.spawn([sip_bin, '-c', self.build_temp, '-b', sbf] +
                   config.pyqt_sip_flags.split() +
                   ['-I', config.pyqt_sip_dir, source])

# Read version from local froi/version.py without pulling in
# froi/__init__.py
sys.path.insert(0, 'froi')
from version import __version__

setup(name='freeroi',
      version=__version__,
      description='Toolbox for ROI defining',
      author='Lijie Huang, Zetian Yang, Guangfu Zhou and Zonglei Zhen, from Neuroinformatic Team@LiuLab',
      author_email=['huanglijie.seal@gmail.com', 'zetian.yang@gmail.com'],
      packages=['froi',
                'froi.algorithm',
                'froi.gui',
                'froi.gui.base',
                'froi.gui.component'],
      scripts=['bin/freeroi', 'bin/freeroi-sess'],
      package_data={'froi': ['data/label/face-object/*',
                             'data/labelconfig/face.lbl',
                             'data/standard/MNI152_T1_2mm_brain.nii.gz',
                             'gui/icon/*']
                    },
      ext_modules=[qimageview],
      cmdclass={'build_ext': build_ext}
      )
