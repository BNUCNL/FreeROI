![Logo](/froi/icon/logo_131.png)

FreeROI is a versatile image processing software developed for neuroimaging
data. Its goal is to provide a user-friendly interface for neuroimaging
researchers to visualize and analyze their data, especially in defining region
of interest (ROI) for ROI analysis.

* Website: <http://bnucnl.github.io>

# Installation

Currently supports the following systems:

* ubuntu/debian
* centos/redhat/fedora
* mac osx
* windows

Notes: For Windows users, an exectable version is
[available](http://sourceforge.net/projects/freeroi/files/?source=navbar).
Unzip the package, and store the directory in a place which path has no 
Chinese characters. Double click *freeroi.exe* to run the program.

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

# License

FreeROI is under Revised BSD License.
See the [LICENSE file](https://github.com/BNUCNL/FreeROI/blob/master/LICENSE)
for the full license text.

