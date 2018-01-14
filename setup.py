# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import sys
import os.path
import numpy
from distutils.core import setup, Extension
import sipdistutils


try:
    import PyQt4.pyqtconfig
    pyqtcfg = PyQt4.pyqtconfig.Configuration()
except ImportError:
    print 'No module named pyqtconfig found in PyQt4'
    import PyQt4.QtCore
    # won't work for SIP v5
    import sipconfig
    cfg = sipconfig.Configuration()
    sip_dir = cfg.default_sip_dir
    for p in (os.path.join(sip_dir, 'PyQt4'), sip_dir):
        if os.path.exists(os.path.join(p, 'QtCore', 'QtCoremod.sip')):
            sip_dir = p
            break
    cfg = {
        'pyqt_version': PyQt4.QtCore.PYQT_VERSION,
        'pyqt_version_str': PyQt4.QtCore.PYQT_VERSION_STR,
        'pyqt_sip_flags': PyQt4.QtCore.PYQT_CONFIGURATION['sip_flags'],
        'pyqt_mod_dir': cfg.default_mod_dir,
        'pyqt_sip_dir': sip_dir,
        'pyqt_bin_dir': cfg.default_bin_dir}
    pyqtcfg = sipconfig.Configuration([cfg])

print("pyqt_version:%06.0x" % pyqtcfg.pyqt_version)
print("pyqt_version_num:%d" % pyqtcfg.pyqt_version)
print("pyqt_version_str:%s" % pyqtcfg.pyqt_version_str)

#-- Qt library configuration
try:
    qt_inc_dir = pyqtcfg.qt_inc_dir
    qt_lib_dir = pyqtcfg.qt_lib_dir
except AttributeError:
    print("Can't extract qt library paths which fit your installation automatically.\nPlease provide the paths of Qt_include and Qt_lib.\nSuch as:")
    print('qt_inc_dir = path/to/Qt_include')
    print('qt_lib_dir = path/to/Qt_lib')
    print('Note that you should use a compatible compiler and Qt version as was used for building PyQt.')
    qt_inc_dir = input('qt_inc_dir = ')
    qt_lib_dir = input('qt_lib_dir = ')
#--

qt_lib_dirs = [qt_lib_dir]
qt_libraries = ['QtCore', 'QtGui']

if sys.platform == 'win32':
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

qimageview.libraries.extend(qt_libraries)
qimageview.library_dirs.extend(qt_lib_dirs)

#if sys.platform == 'darwin':
#    ## Qt is distributed as 'framwork' on OS X
#    #for lib in qt_libraries:
#    #    qimageview.extra_link_args.extend(['-framework', lib])
#    #for d in qt_lib_dirs:
#    #    qimageview.extra_link_args.append('-F' + d)
#    qimageview.libraries.extend(qt_libraries)
#    qimageview.library_dirs.extend(qt_lib_dirs)
#else:
#    qimageview.libraries.extend(qt_libraries)
#    qimageview.library_dirs.extend(qt_lib_dirs)


class build_ext(sipdistutils.build_ext):
    def _sip_compile(self, sip_bin, source, sbf):
        try:
            import PyQt4.pyqtconfig
            pyqtcfg = PyQt4.pyqtconfig.Configuration()
        except ImportError:
            print 'No module named pyqtconfig found in PyQt4'
            import PyQt4.QtCore
            # won't work for SIP v5
            import sipconfig
            cfg = sipconfig.Configuration()
            sip_dir = cfg.default_sip_dir
            for p in (os.path.join(sip_dir, 'PyQt4'), sip_dir):
                if os.path.exists(os.path.join(p, 'QtCore', 'QtCoremod.sip')):
                    sip_dir = p
                    break
            cfg = {
                'pyqt_version': PyQt4.QtCore.PYQT_VERSION,
                'pyqt_version_str': PyQt4.QtCore.PYQT_VERSION_STR,
                'pyqt_sip_flags': PyQt4.QtCore.PYQT_CONFIGURATION['sip_flags'],
                'pyqt_mod_dir': cfg.default_mod_dir,
                'pyqt_sip_dir': sip_dir,
                'pyqt_bin_dir': cfg.default_bin_dir}
            pyqtcfg = sipconfig.Configuration([cfg])
        self.spawn([sip_bin, '-c', self.build_temp, '-b', sbf] +
                   pyqtcfg.pyqt_sip_flags.split() +
                   ['-I', pyqtcfg.pyqt_sip_dir, source])

# Read version from local froi/version.py without pulling in
# froi/__init__.py
sys.path.insert(0, 'froi')
from version import __version__

setup(name='freeroi',
      version=__version__,
      description='Toolbox for ROI defining',
      author='Lijie Huang, Zetian Yang, Xiayu Chen, Guangfu Zhou, Zhaoguo Liu, and Zonglei Zhen, from Neuroinformatic Team@LiuLab',
      author_email=['huanglijie.seal@gmail.com', 'zetian.yang@gmail.com', 'sunshine_drizzle@foxmail'],
      packages=['froi',
                'froi.algorithm',
                'froi.core',
                'froi.widgets',
                'froi.interface',
                'froi.io'],
      scripts=['bin/freeroi', 'bin/freeroi-sess'],
      package_data={'froi': ['data/label/face-object/*',
                             'data/labelconfig/*',
                             'data/standard/*',
                             'data/atlas/*',
                             'icon/*']
                    },
      ext_modules=[qimageview],
      cmdclass={'build_ext': build_ext}
      )
