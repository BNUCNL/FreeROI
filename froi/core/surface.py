# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Dataset definition class for FreeROI GUI system.
"""

import re
import os

import nibabel as nib
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..algorithm import array2qimage as aq
from labelconfig import LabelConfig



