import time
import nibabel as nib
import numpy as np

affine = np.array([[0.02910485629, 0.02204488493, 1.01224969, -0.1681282508],
                   [-1.095740656, -0.1306868194, 0.04778140379, 266.117978],
                   [0.1866107588, -1.125221599, 0.02890207587, 187.5450733],
                   [0, 0, 0, 1]])

temp_affine = np.array([[0.02910485629, 0.02204488493, 1.01224969],
                   [-1.095740656, -0.1306868194, 0.04778140379],
                   [0.1866107588, -1.125221599, 0.02890207587]])

transform = np.array([-0.1681282508, 266.117978, 187.5450733])


if __name__ == "__main__":
    starttime = time.clock()
    #load data
    moving_image_img = nib.load("./data/001.nii")
    moving_image_affine = moving_image_img.get_affine().astype(dtype=np.float32)
    moving_image = moving_image_img.get_data()


    fixed_image_img = nib.load("./data/avg152T1.nii.gz")
    fixed_image = fixed_image_img.get_data().astype(dtype=np.float32)
    fixed_image_affine = fixed_image_img.get_affine()
    print 'std_image_img.shape: ', fixed_image.shape

    # from scipy.ndimage.interpolation import affine_transform
    # from nibabel.affines import apply_affine
    # temp = affine_transform(input=image, matrix=transform_matrix_3, offset=offset, output_shape=std_image.shape)
    # # temp = apply_affine(transform_matrix, image.shape)


    import dipy.align.vector_fields as vfu

    # from dipy.segment.mask import median_otsu
    # print 'begin otsu: '
    # print 'standard otsu.'
    # stanford_b0_masked, stanford_b0_mask = median_otsu(std_image, 4, 4)
    # print 'moving otsu.'
    # syn_b0_masked, syn_b0_mask = median_otsu(image, 4, 4)
    #
    # static = stanford_b0_masked
    # static_affine = std_image_img.get_affine()
    # moving = syn_b0_masked
    # moving_affine = image_affine

    transform = np.linalg.inv(moving_image_affine).dot(affine.dot(fixed_image_affine))
    # transform = np.linalg.inv(image_affine).dot(np.linalg.inv(affine).dot(std_image_img.get_affine()))
    # # transform = affine
    #
    # resampled = vfu.warp_3d_affine(image.astype(np.float32),
    #                             np.asarray(std_image.shape, dtype=np.int32),
    #                             transform)
    # resampled = np.asarray(resampled)

    resampled = np.zeros_like(fixed_image)
    from scipy.ndimage.interpolation import affine_transform

    affine_transform(input=moving_image, matrix=affine[:3, :3], offset=affine[:3, 3], output_shape=fixed_image.shape, output=resampled)


    print 'resampled: ', resampled.shape, resampled.max(), resampled.min()

    nib.save(nib.Nifti1Image(resampled, affine), "./result/result_std_1.nii.gz")

    endtime = time.clock()
    print 'Cost time:: ', np.round((endtime - starttime), 3), ' s'





















