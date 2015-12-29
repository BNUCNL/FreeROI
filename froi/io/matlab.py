# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import subprocess


def run_matlab(cmd):
    matlab_cmd = 'matlab -nojvm -nosplash  -wait'
    return subprocess.call('%s -r \"%s;exit\" ' % (matlab_cmd, cmd), shell=True)


def run_matlab_script(script_lines, script_name='pyscript'):
    """Put multiline matlab script into script file and run."""
    mfile = open(script_name + '.m', 'wt')
    mfile.write(script_lines)
    mfile.close()

    return run_matlab(script_name)
