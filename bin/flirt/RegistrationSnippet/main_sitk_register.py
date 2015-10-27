# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import time
import nibabel as nib
import numpy as np

import SimpleITK as sitk

import numpy as np

def register_images(fixed_image, moving_image, initial_transform, interpolator):

    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.REGULAR)
    registration_method.SetMetricSamplingPercentage(0.01)
    registration_method.SetInterpolator(interpolator)
    registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=1000)
    registration_method.SetOptimizerScalesFromPhysicalShift()
    registration_method.SetInitialTransform(initial_transform, inPlace=False)

    final_transform = registration_method.Execute(fixed_image, moving_image)

    return( final_transform, registration_method.GetOptimizerStopConditionDescription())

def save_transform_and_image(transform, fixed_image, moving_image, outputfile_prefix):
    """
    Write the given transformation to file, resample the moving_image onto the fixed_images grid and save the
    result to file.

    Args:
        transform (SimpleITK Transform): transform that maps points from the fixed image coordinate system to the moving.
        fixed_image (SimpleITK Image): resample onto the spatial grid defined by this image.
        moving_image (SimpleITK Image): resample this image.
        outputfile_prefix (string): transform is written to outputfile_prefix.tfm and resampled image is written to
                                    outputfile_prefix.mha.
    """
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(fixed_image)

    # SimpleITK supports several interpolation options, we go with the simplest that gives reasonable results.
    resample.SetInterpolator(sitk.sitkLinear)
    resample.SetTransform(transform)
    sitk.WriteImage(resample.Execute(moving_image), outputfile_prefix+'.nii.gz')
    sitk.WriteTransform(transform, outputfile_prefix+'.tfm')

if __name__ == "__main__":
    starttime = time.clock()
    #load data
    fixed_image = sitk.ReadImage("./brain/std.nii.gz", sitk.sitkFloat32)
    fixed_data = sitk.GetArrayFromImage(fixed_image)

    moving_image = sitk.ReadImage("./brain/T1_brain.nii.gz", sitk.sitkFloat32)
    moving_data = sitk.GetArrayFromImage(moving_image)

    # Isotropic voxels with 1mm spacing.
    new_spacing = [1.0]*moving_image.GetDimension()

    # Create resampled image using new spacing and size.
    original_size = moving_image.GetSize()
    original_spacing = moving_image.GetSpacing()
    resampled_image_size = [int(spacing/new_s*size)
                        for spacing, size, new_s in zip(original_spacing, original_size, new_spacing)]
    resampled_moving_image = sitk.Image(resampled_image_size, moving_image.GetPixelIDValue())
    resampled_moving_image.SetSpacing(new_spacing)
    resampled_moving_image.SetOrigin(moving_image.GetOrigin())
    resampled_moving_image.SetDirection(moving_image.GetDirection())

    # Resample original image using identity transform and the BSpline interpolator.
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(resampled_moving_image)
    resample.SetInterpolator(sitk.sitkBSpline)
    resample.SetTransform(sitk.Transform())
    resampled_moving_image = resample.Execute(moving_image)

    print('Original image size and spacing: {0} {1}'.format(original_size, original_spacing))
    print('Resampled image size and spacing: {0} {1}'.format(resampled_moving_image.GetSize(),
                                                         resampled_moving_image.GetSpacing()))
    print('Memory ratio: 1 : {0}'.format((np.array(resampled_image_size)/np.array(original_size).astype(float)).prod()))

    initial_transform = sitk.CenteredTransformInitializer(fixed_image,
                                                          moving_image,
                                                          sitk.Euler3DTransform(),
                                                          sitk.CenteredTransformInitializerFilter.GEOMETRY)
    # We define this variable as global so that it is accessible outside of the cell (timeit wraps the code in the cell
    # making all variables local, unless explicitly declared global).
    global original_resolution_errors

    final_transform, optimizer_termination = register_images(fixed_image, moving_image, initial_transform, sitk.sitkLinear)

    # final_transform, optimizer_termination = register_images(fixed_image, resampled_moving_image, initial_transform,
    #                                                         sitk.sitkNearestNeighbor)

    # moving_resampled = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0,
    #                                  moving_image.GetPixelIDValue())

    save_transform_and_image(final_transform, fixed_image, moving_image, "./result/sitk_output_09")


    # nib.save(nib.Nifti1Image(resampled, affine), "./result/result_std_1.nii.gz")

    endtime = time.clock()






















