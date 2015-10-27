# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import time
import nibabel as nib
import numpy as np

affine = np.array([[0.02910485629, 0.02204488493, 1.01224969, -0.1681282508],
                   [-1.095740656, -0.1306868194, 0.04778140379, 266.117978],
                   [0.1866107588, -1.125221599, 0.02890207587, 187.5450733],
                   [0, 0, 0, 1]])

import SimpleITK as sitk
# Always write output to a separate directory, we don't want to pollute the source directory.
import os
OUTPUT_DIR = './result/'


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
    out_image = resample.Execute(moving_image)
    sitk.WriteImage(out_image, outputfile_prefix+'.nii.gz')
    sitk.WriteTransform(transform, outputfile_prefix+'.tfm')

    return out_image

#----------------------------------------------------main-------------------------------------------------------
# Loading Data
fixed_image = sitk.ReadImage("./brain/std.nii.gz", sitk.sitkFloat32)
moving_image = sitk.ReadImage("./brain/T1_brain.nii.gz", sitk.sitkFloat32)

#Initial Alignment
initial_transform = sitk.CenteredTransformInitializer(sitk.Cast(fixed_image,moving_image.GetPixelIDValue()),
                                                      moving_image,
                                                      sitk.Euler3DTransform(),
                                                      sitk.CenteredTransformInitializerFilter.GEOMETRY)

# Save moving image after initial transform and view overlap using external viewer.
out_image = save_transform_and_image(initial_transform, fixed_image, moving_image, os.path.join(OUTPUT_DIR, "initialAlignment"))
print "Initial Alignment (initial_transform): ", (initial_transform)

#Final registration
#Version 1


# registration_method = sitk.ImageRegistrationMethod()
#
# registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
# registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
# registration_method.SetMetricSamplingPercentage(0.01)
#
# registration_method.SetInterpolator(sitk.sitkLinear)
#
# registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100)
# # Scale the step size differently for each parameter, this is critical!!!
# registration_method.SetOptimizerScalesFromPhysicalShift()
#
# registration_method.SetInitialTransform(initial_transform, inPlace=False)
# final_transform_v1 = registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
#                                                  sitk.Cast(moving_image, sitk.sitkFloat32))
# print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
# print('Final metric value: {0}'.format(registration_method.GetMetricValue()))
#
# # Save moving image after registration and view overlap using external viewer.
# save_transform_and_image(final_transform_v1, fixed_image, moving_image, os.path.join(OUTPUT_DIR, "finalAlignment-v1"))
#
# print "Version 1 (final_transform_v1): ", (final_transform_v1)
#
#
# #Version 1.1
# registration_method = sitk.ImageRegistrationMethod()
# registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
# registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
# registration_method.SetMetricSamplingPercentage(0.01)
# registration_method.SetInterpolator(sitk.sitkLinear)
# registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100)
# registration_method.SetOptimizerScalesFromPhysicalShift()
#
# # Set the initial moving and optimized transforms.
# optimized_transform = sitk.Euler3DTransform()
# registration_method.SetMovingInitialTransform(initial_transform)
# registration_method.SetInitialTransform(optimized_transform)
#
# registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
#                             sitk.Cast(moving_image, sitk.sitkFloat32))
#
# # Need to compose the transformations after registration.
# final_transform_v11 = sitk.Transform(optimized_transform)
# final_transform_v11.AddTransform(initial_transform)
#
# print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
# print('Final metric value: {0}'.format(registration_method.GetMetricValue()))
#
# # Save moving image after registration and view overlap using external viewer.
# save_transform_and_image(final_transform_v11, fixed_image, moving_image, os.path.join(OUTPUT_DIR, "finalAlignment-v1.1"))
#
# print "Version 1.1 (final_transform_v11): ", (final_transform_v11)


#Version 2
registration_method = sitk.ImageRegistrationMethod()

registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
registration_method.SetMetricSamplingPercentage(0.01)

registration_method.SetInterpolator(sitk.sitkLinear)

registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100) #, estimateLearningRate=registration_method.EachIteration)
registration_method.SetOptimizerScalesFromPhysicalShift()

final_transform = sitk.Euler3DTransform(initial_transform)
registration_method.SetInitialTransform(final_transform)
registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [4,2,1])
registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas = [2,1,0])
registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

registration_method.Execute(sitk.Cast(fixed_image, sitk.sitkFloat32),
                            sitk.Cast(moving_image, sitk.sitkFloat32))

print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
print('Final metric value: {0}'.format(registration_method.GetMetricValue()))

# Save moving image after registration and view overlap using external viewer.
out_image = save_transform_and_image(final_transform, fixed_image, moving_image, os.path.join(OUTPUT_DIR, 'finalAlignment-v3'))

print "Version 2 (final_transform): ", (final_transform)

print 'Program end!'



