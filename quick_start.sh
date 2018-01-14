#!/bin/bash

pip install -U setuptools
pip install cython

echo "Install required packages..."
pip install numpy scipy nose scikit-image mayavi
