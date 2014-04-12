# -*- mode: python -*-
a = Analysis(['F:\\FreeROI\\FreeROI\\bin\\freeroi'],
             pathex=['F:\\FreeROI\\pyinstaller-2.0'],
             hiddenimports=[],
             hookspath=None)
def extra_datas(mydir, type):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" %d, files)
    files = []
    rec_glob("%s/*" %mydir, files)
    extra_datas = []
    if type == 'icon':
        for f in files:
            extra_datas.append((os.path.join('icon', 
                                             os.path.basename(f)),
                               f, 'DATA'))
    elif type == 'data':
        for f in files:
            temp = f.split('\\')
            idx = temp.index('data')
            extra_datas.append((os.path.join(*temp[idx:]), f, 'DATA'))
    return extra_datas

import froi
froi_dir = os.path.dirname(froi.__file__)
data_dir = os.path.join(froi_dir, 'data')
icon_dir = os.path.join(froi_dir, 'gui', 'icon')
a.datas += extra_datas(data_dir, 'data')
a.datas += extra_datas(icon_dir, 'icon')

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\freeroi', 'freeroi.exe'),
          icon='path/to/logo.ico',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               [('skimage._shared.geometry', 'C:\Python27\Lib\site-packages\skimage\_shared\geometry.pyd', 'EXTENSION')],
               [('skimage._shared.interpolation', 'C:\Python27\Lib\site-packages\skimage\_shared\interpolation.pyd', 'EXTENSION')],
               #[('skimage._shared.transform', 'C:\Python27\Lib\site-packages\skimage\_shared\transform.pyd', 'EXTENSION')],
               [('sigtools', 'C:\Python27\Lib\site-packages\scipy\signal\sigtools.pyd', 'EXTENSION')],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'freeroi'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'freeroi.app'))
