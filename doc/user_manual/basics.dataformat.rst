.. _data-format:

Data Format
============

FreeROI currently supports both 3D and 4D MRI data in NIFTI format.
3D data is commonly one single image, such as the T1 or T2 weighted structural image.
4D data is a image file comprises a series of 3D images.
Functional MRI data (i.e. task fMRI, resting fMRI) are usually 4D.

FreeROI will automatically distinguish the current image as 3D or 4D when load the data.
Besides, most operations are both available to both of these two data format.
