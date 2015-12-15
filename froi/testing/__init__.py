# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Utilities for testing."""

from os.path import abspath, dirname, join as pjoin

data_path = abspath(pjoin(dirname(__file__), '..', 'tests', 'data'))
bench_path = abspath(pjoin(data_path, 'benchmark'))
tmp_path = abspath(pjoin('.', 'pybp_test_tmp'))
