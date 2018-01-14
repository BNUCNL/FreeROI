[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.51123.svg)](http://dx.doi.org/10.5281/zenodo.51123)

![Logo](/froi/icon/logo_131.png)

FreeROI is a versatile image processing software developed for neuroimaging
data. Its goal is to provide a user-friendly interface for neuroimaging
researchers to visualize and analyze their data, especially in defining region
of interest (ROI) for ROI analysis.

# Easy installation

The easiest way to configure your local python environment to support FreeROI is to use the [Anaconda python distribution](https://store.continuum.io/cshop/anaconda/). Download and install anaconda2 (We recommend [anaconda-4.1.1](https://repo.continuum.io/archive/)), then run the following command to install all required and related packages. (If your anaconda forcely installs PyQt5, you have to execute ```conda uninstall pyqt=5``` before install PyQt4)

```
$ conda install numpy scipy nose scikit-image pyqt=4 mayavi
```

In addition, one non-standard package (nibabel) for reading and writing neuroimaging data should be installed:

```
$ pip install nibabel
```

Finally, download FreeROI source code to <your_directory> by [clicking here](https://github.com/BNUCNL/FreeROI/archive/surface_lab.zip) or executing ```$ git clone http://github.com/BNUCNL/FreeROI <your_directory>```. Then:

```
$ cd <your_directory>
$ python setup.py install
```

This should work on most platform (i.e., Mac or Linux PCs). You can also skip Anaconda and customize your python environment, please see next section.

For Windows users, an exectable version is [available](http://sourceforge.net/projects/freeroi/files/?source=navbar). Unzip the package, and store the directory in a place which path has no Chinese characters. Double click *freeroi.exe* to run the program.

# DIY on your environment

Currently supports the following systems:

* ubuntu/debian
* centos/redhat/fedora
* mac osx
* windows

## Dependency

* Python 2.7
* pip >= 1.4.1
* Qt4 >= 4.7

## Install Qt4

* On Ubuntu/Debian
  ```
  $ apt-get install libqt4-dev 
  ```

* On CentOS/Fedora/Fedora
  ```
  $ yum install qt4 qt4-devel
  ```

* On Mac OSX
  ```
  $ brew install qt --build-from-source
  ```

If you cannot install Qt4 with above methods, you may need to install it
manually. The source code of Qt4.8 could be downloaded from the
[homepage of Qt](http://qt-project.org/downloads).


## Install SIP and PyQt4

* On Ubuntu/Debian
  ```
  $ apt-get install python-qt4 python-qt4-dev
  ```

If you cannot install SIP and PyQt4 with above methods, you may need to install it
manually. The source codes can be downloaded from [SIP](http://www.riverbankcomputing.com/software/sip/download) and 
[PyQt4](http://www.riverbankcomputing.com/software/pyqt/download).
Untar these packages, and install them like this
```
# install SIP
$ cd SIP
$ python configure.py
$ make
$ make install
# install PyQt4
$ cd ../PyQt
$ python configure.py
$ make
$ make install
```


## Install VTK

* On Ubuntu/Debian
  ```
  $ apt-get install python-vtk
  ```
 
* On any 64-bit platform
  $ pip install [VTK-5.10.1+qt486-cp27-none-win_amd64.whl](https://www.lfd.uci.edu/~gohlke/pythonlibs/#vtk)

* On any 32-bit platform
  $ pip install [VTK-5.10.1+qt486-cp27-none-win32.whl](https://www.lfd.uci.edu/~gohlke/pythonlibs/#vtk)


## Install related python module

Then, several python modules should be installed. Here we provide a script
`quick_start.sh` to install them automatically.


## Install FreeROI

After download the source code of FreeROI, you only to execute:
```
python setup.py install
```

# Documentation

Please find more complete documentation for FreeROI at this [page](http://bnucnl.github.io). The documentation for FreeROI is currently incomplete, but will be imporoved in the coming days, weeks, or months.

# License

FreeROI is under Revised BSD License.
See the [LICENSE file](https://github.com/BNUCNL/FreeROI/blob/master/LICENSE)
for the full license text.

