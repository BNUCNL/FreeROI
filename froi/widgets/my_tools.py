"""
some tool functions
Tell the world: Almost all of these functions at present are quoted from Pysurfer! Thanks very much!
"""

from mayavi import mlab
import os
from subprocess import Popen, PIPE, check_output

import logging
logger = logging.getLogger('surfer')


def force_render(figure):
    """
    Ensure plots are updated before properties are used

    Parameter
    ---------
    figure: the mlab scene
    """

    figure.render()
    mlab.draw(figure)


def toggle_render(figure, state, view=None):
    """
    Parameters
    ----------
    figure: the mlab figure
    state: Turn rendering on (True) or off (False)
    view: View to see the brain
    """
    if state is False and view is None:
        view = mlab.view(figure=figure)

    # Testing backend doesn't have this option
    if mlab.options.backend != 'test':
        figure.scene.disable_render = not state

    if state is True and view is not None:
        mlab.draw(figure)
        mlab.view(*view, figure=figure)

    if state is True:
        force_render(figure)

    return view


def project_volume_data(filepath, hemi, reg_file=None, subject_id=None,
                        projmeth="frac", projsum="avg", projarg=[0, 1, .1],
                        surf="white", smooth_fwhm=3, mask_label=None,
                        target_subject=None, verbose=None):
    """Sample MRI volume onto cortical manifold.

    Note: this requires Freesurfer to be installed with correct
    SUBJECTS_DIR definition (it uses mri_vol2surf internally).

    Parameters
    ----------
    filepath : string
        Volume file to resample (equivalent to --mov)
    hemi : [lh, rh]
        Hemisphere target
    reg_file : string
        Path to TKreg style affine matrix file
    subject_id : string
        Use if file is in register with subject's orig.mgz
    projmeth : [frac, dist]
        Projection arg should be understood as fraction of cortical
        thickness or as an absolute distance (in mm)
    projsum : [avg, max, point]
        Average over projection samples, take max, or take point sample
    projarg : single float or sequence of three floats
        Single float for point sample, sequence for avg/max specifying
        start, stop, and step
    surf : string
        Target surface
    smooth_fwhm : float
        FWHM of surface-based smoothing to apply; 0 skips smoothing
    mask_label : string
        Path to label file to constrain projection; otherwise uses cortex
    target_subject : string
        Subject to warp data to in surface space after projection
    verbose : bool, str, int, or None
        If not None, override default verbose level (see surfer.verbose).
    """

    env = os.environ
    if 'FREESURFER_HOME' not in env:
        raise RuntimeError('FreeSurfer environment not defined. Define the '
                           'FREESURFER_HOME environment variable.')
    # Run FreeSurferEnv.sh if not most recent script to set PATH
    if not env['PATH'].startswith(os.path.join(env['FREESURFER_HOME'], 'bin')):
        cmd = ['bash', '-c', 'source {} && env'.format(
               os.path.join(env['FREESURFER_HOME'], 'FreeSurferEnv.sh'))]
        envout = check_output(cmd)
        env = dict(line.split('=', 1) for line in envout.split('\n')
                   if '=' in line)

    # Set the basic commands
    cmd_list = ["mri_vol2surf",
                "--mov", filepath,
                "--hemi", hemi,
                "--surf", surf]

    # Specify the affine registration
    if reg_file is not None:
        cmd_list.extend(["--reg", reg_file])
    elif subject_id is not None:
        cmd_list.extend(["--regheader", subject_id])
    else:
        raise ValueError("Must specify reg_file or subject_id")

    # Specify the projection
    proj_flag = "--proj" + projmeth
    if projsum != "point":
        proj_flag += "-"
        proj_flag += projsum
    if hasattr(projarg, "__iter__"):
        proj_arg = map(str, projarg)
    else:
        proj_arg = [str(projarg)]
    cmd_list.extend([proj_flag] + proj_arg)

    # Set misc args
    if smooth_fwhm:
        cmd_list.extend(["--surf-fwhm", str(smooth_fwhm)])
    if mask_label is not None:
        cmd_list.extend(["--mask", mask_label])
    if target_subject is not None:
        cmd_list.extend(["--trgsubject", target_subject])

    # Execute the command
    # out_file = mktemp(prefix="pysurfer-v2s", suffix='.mgz')
    out_file = _get_out_file_path(filepath, hemi)
    cmd_list.extend(["--o", out_file])
    logger.info(" ".join(cmd_list))
    p = Popen(cmd_list, stdout=PIPE, stderr=PIPE, env=env)
    stdout, stderr = p.communicate()
    out = p.returncode
    if out:
        raise RuntimeError(("mri_vol2surf command failed "
                            "with command-line: ") + " ".join(cmd_list))

    # Read in the data
    # surf_data = read_scalar_data(out_file)
    # os.remove(out_file)
    # return surf_data


def _get_out_file_path(in_file_path, hemi):

    dir_name, base_name = os.path.split(in_file_path)

    if base_name.endswith(".nii.gz"):
        base_name = base_name[:-7]
    elif base_name.endswith(".gz"):
        base_name = base_name[:-3]
    if base_name.startswith("%s." % hemi):
        base_name = base_name[3:]
    name = os.path.splitext(base_name)[0]

    out_file_path = os.path.join(dir_name, "%s_%s.nii.gz" % (hemi, name))
    return out_file_path
