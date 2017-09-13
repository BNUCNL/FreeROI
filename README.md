[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.51123.svg)](http://dx.doi.org/10.5281/zenodo.51123)

![Logo](/froi/icon/logo_131.png)

FreeROI is a versatile image processing software developed for neuroimaging
data. Its goal is to provide a user-friendly interface for neuroimaging
researchers to visualize and analyze their data, especially in defining region
of interest (ROI) for ROI analysis.

# Quickstart

The easiest way to configure your local python environment to support FreeROI is to use the [Anaconda python distribution](https://store.continuum.io/cshop/anaconda/). Download and install anaconda (Python 2.7), then run the following command to install all required and related packages.

```
$ conda install numpy scipy nose scikits-image pyqt=4
```

In addition, one non-standard package (nibabel) for reading and writing fMRI data should be installed:

```
$ pip install nibabel
```

To install FreeROI from the github repository, call the following commands. For both commands, replace `<your_directory>` with the folder where you would like to store the FreeROI source code.

```
$ git clone http://github.com/BNUCNL/FreeROI <your_directory>
$ cd <your_directory>
$ python setup.py install
```

This should work on most platform (i.e., Mac or Linux PCs). You can also skip Anaconda and customize your python environment, please see next section.

For Windows users, an exectable version is [available](http://sourceforge.net/projects/freeroi/files/?source=navbar). Unzip the package, and store the directory in a place which path has no Chinese characters. Double click *freeroi.exe* to run the program.

# DIY on your platform

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
  $ apt-get install libqt4-core libqt4-dev libqt4-gui qt4-dev-tools
  ```

* On CentOS/Fedora/Fedora
  ```
  $ yum install qt4 qt4-devel
  ```

* On Mac OSX
   
  On Mac OSX, the Qt4 could be installed with brew like this
  ```
  $ brew install qt --build-from-source
  ```

If you cannot install Qt4 with above methods, you may need to install it
manually. The source code of Qt4.8 could be downloaded from the
[homepage of Qt](http://qt-project.org/downloads).

## Install related python module

Then, several python modules should be installed. Here we provide a script
`quick_start.sh` to install them automatically. By default, a new virtual
python environment would be generated using `virtualenv`. 

## Install SIP and PyQt4

Third, [SIP](http://www.riverbankcomputing.com/software/sip/download) and 
[PyQt4](http://www.riverbankcomputing.com/software/pyqt/download) should be
installed.

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

## Install FreeROI

After download the source code, you only to execte:

```
python setup.py install
```

# Documentation

Please find more complete documentation for FreeROI at this [page](http://bnucnl.github.io). The documentation for FreeROI is currently incomplete, but will be imporoved in the coming days, weeks, or months.

# License

FreeROI is under Revised BSD License.
See the [LICENSE file](https://github.com/BNUCNL/FreeROI/blob/master/LICENSE)
for the full license text.

