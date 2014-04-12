#!/bin/bash

echo "Init virtualenv..."
which virtualenv > /dev/null 2>&1
if [ $? != 0];then
	echo "Install virtualenv..."
	pip install virtualenv
fi
virtualenv venv
. venv/bin/activate
pip install -U setuptools
pip install cython

echo "Install required packages..."
pip install -r requirements.txt

echo "Install FreeROI..."
python setup.py install
