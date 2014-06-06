Q&A
====

1. How to display an image that showing both positive and negative activation
   in different colors simultaneously?

   Currently, an image could be displayed with only one color scheme, so a
   remedy to do that is inverting the image first, and assigning two different
   color schemes for them.

2. How to get a MNI coordinate of a voxel?

   The coordinate showed in the software is in voxel units. If a MNI standard
   template (voxel size: 2mm x 2mm x 2mm) is loaded, then the MNI coordinate
   could be computed as

   MNI_x = (45 - voxel_x) * 2 mm

   MNI_y = (voxel_y - 63) * 2 mm

   MNI_z = (voxel_z - 36) * 2 mm
