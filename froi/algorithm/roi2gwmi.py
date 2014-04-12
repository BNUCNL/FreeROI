#!/usr/bin/env python
#code by Dangxiaobin at 2013-11-28

"""
Project the ROI to the gray white matter interface.
"""
import numpy as np
from froi.algorithm import imtool as imt
import time as time
from scipy.spatial import distance as ds

def is_inside(v, shape):
    """
    Check whether the coordinate is inside the shaped volume.
    """
    return ((v[0] >= 0) & (v[0] < shape[0]) &
            (v[1] >= 0) & (v[1] < shape[1]) &
            (v[2] >= 0) & (v[2] < shape[2]))
    
def get_neighbors(coor,radius,shape):
    """
    Get the neighbor coordinates with in radius cube.
    """
    neighbors = []
    offsets = []
   
    for x in np.arange(-radius, radius + 1):
        for y in np.arange(-radius, radius + 1):
            for z in np.arange(-radius, radius + 1):
                offsets.append([x,y,z])
    
    offsets = np.array(offsets)
    #print offsets
    
    for offset in offsets:
        
        if offset.tolist() == [0,0,0]:
            #print offset.tolist()
            continue
           
        tmp_neigh = coor + offset
        #print tmp_neigh
        inside = is_inside(tmp_neigh,shape)
        if inside :
            neighbors.append([tmp_neigh[0],tmp_neigh[1],tmp_neigh[2]])
    
    neighbors = np.array(neighbors)
    #print neighbors.shape
    return neighbors   

def get_neighbors_surface(coor,radius,shape):
    """
    Get the cube surface. 
    """
    neigh = []
    if radius <=0:
        return neigh
    elif radius ==1:
        return get_neighbors(coor,radius,shape)
    else:
        neighbors_all = get_neighbors(coor,radius,shape)
        neighbors_in = get_neighbors(coor,radius-1,shape)
        neigh = [i for i in neighbors_all.tolist() if i not in neighbors_in.tolist()]

        return neigh

def roi_to_gwmi(img,brain_wm,nth):
    """
    Transform the functional roi to wm.
    Algorithm: find the nearest wm voxel.
    """
    #st = time.time()
    data = img
    wmdata = imt.multi_label_edge_detection(brain_wm)
    shape = data.shape

    roi_ids = np.unique(data)
    roi = roi_ids[1:]
    roi = [int(i) for i in roi]
    
    wmdata = wmdata!=0
    result_mask = np.zeros(data.shape)
    #print wmdata   
    
    #First, get the nonzero voxel index in image data.
    #Here image data is a label volume.
    #ROIs is in it
    for roi_id in roi:
        #print roi_id
        tmp_mask = data==roi_id
        #print tmp_mask
        indexs = np.transpose(tmp_mask.nonzero())
        #print indexs
        
        #Second, find the nearest wm voxel for each indexs.
        for coor in indexs:
            #print coor
            x = coor[0]
            y = coor[1]
            z = coor[2]
    
            if wmdata[x,y,z]==1:
                result_mask[x,y,z] = roi_id
            else:
                #find the nearest neighbor.
                flag = False
                radius = 1
                mindist_voxel = []
                mindist = 1000     
                while radius<nth:      
                    neigh_list = get_neighbors(coor,radius,shape)
                    radius += 1
                    #find the nearest white matter voxel.
                    for n in neigh_list:
                        #print n
                        if wmdata[n[0],n[1],n[2]]==1:
                            flag = True
                            dist = np.sqrt((n[0]-x)**2+(n[1]-y)**2+(n[2]-z)**2)
                            # if the distance is smaller than tag, choose it to be nearest.
                            
                            if dist < mindist:
                                mindist = dist
                                mindist_voxel = n
                            
                    if flag:
                        break
                #print mindist_voxel
                if mindist_voxel!=[]:
                    result_mask[mindist_voxel[0],mindist_voxel[1],mindist_voxel[2]] = roi_id 
    """
    for roi_id in roi:
        tmp_mask = result_mask==roi_id
        roi_size = tmp_mask.sum()    
        print roi_id, roi_size
    """
    #print "Time use: %s"%(time.time()-st)
    return result_mask

def roi_to_gwmi_1(img,brain_wm):
    """
    Transform the functional roi to wm.
    Algorithm: find the nearest wm voxel.
    """
    #st = time.time()
    neighbors  = [[1,0,0],\
                 [-1,0,0],\
                 [0,1,0],\
                 [0,-1,0],\
                 [0,0,-1],\
                 [0,0,1],\
                 [1,1,0],\
                 [1,1,1],\
                 [1,1,-1],\
                 [0,1,1],\
                 [-1,1,1],\
                 [1,0,1],\
                 [1,-1,1],\
                 [-1,-1,0],\
                 [-1,-1,-1],\
                 [-1,-1,1],\
                 [0,-1,-1],\
                 [1,-1,-1],\
                 [-1,0,-1],\
                 [-1,1,-1],\
                 [0,1,-1],\
                 [0,-1,1],\
                 [1,0,-1],\
                 [1,-1,0],\
                 [-1,0,1],\
                 [-1,1,0]]
    neighbors = np.array(neighbors)

    data = img
    wmdata = imt.multi_label_edge_detection(brain_wm)
    shape = data.shape

    roi_ids = np.unique(data)
    roi = roi_ids[1:]
    roi = [int(i) for i in roi]
    
    wmdata = wmdata!=0
    result_mask = np.zeros(shape)
    #print wmdata   
    
    #First, get the nonzero voxel index in image data.
    #Here image data is a label volume.
    #ROIs is in it
    for roi_id in roi:
        tmp_mask = data==roi_id
        #print tmp_mask
        indexs = np.transpose(tmp_mask.nonzero())
        #print indexs
        
        #Second, find the nearest wm voxel for each indexs.
        #print roi_id,indexs.shape[0]
        for coor in indexs:

            #x = coor[0]
            #y = coor[1]
            # z = coor[2]
            if wmdata[coor[0],coor[1],coor[2]]==1:
                pass
                #result_mask[x,y,z] = roi_id
            else:
                #find the nearest neighbor.        
                neigh_list = [(ioff+coor).tolist() for ioff in neighbors]
                #find the nearest white matter voxel.
                for n in neigh_list:
                    if wmdata[n[0],n[1],n[2]]==1:
                        result_mask[n[0],n[1],n[2]] = roi_id
    """
    for roi_id in roi:
        tmp_mask = result_mask==roi_id
        roi_size = tmp_mask.sum()    
        #print roi_id, roi_size
    """
    #print "Time use: %s"%(time.time()-st)
    return result_mask


def roi_projection(img,roi,dis_th,val_th,mode):
    
    #st = time.time()
    data = img
    
    roi = imt.multi_label_edge_detection(roi)
    result_mask = np.zeros(data.shape)
    con_mask = np.zeros(data.shape)
    
    tmp_mask = data > 0 
    roi_mask = roi > 0

    img_indexs = np.transpose(tmp_mask.nonzero())
    roi_indexs = np.transpose(roi_mask.nonzero())
    
    spacedist = ds.cdist(img_indexs,roi_indexs,'euclidean')
    #print spacedist
    mode = int(mode)
    val_th = float(val_th)
    #  print mode,val_th
    if mode ==0:
        for dist in spacedist:
            index = dist.argmin()
            if dist.min()< dis_th:
                coor = roi_indexs[index]
                result_mask[coor[0]][coor[1]][coor[2]] = 1
    elif mode == 1:
        for dist in spacedist:
            index = dist.argmin()
            if dist.min()< dis_th:
                coor = roi_indexs[index]
                result_mask[coor[0]][coor[1]][coor[2]] = result_mask[coor[0]][coor[1]][coor[2]]+1
        result_mask[  result_mask < val_th] = 0 
    #    print result_mask[result_mask.nonzero()]
        
    elif mode == 2:
        for i,dist in enumerate(spacedist):
            index = dist.argmin()
            if dist.min()< dis_th:
                dcoor = img_indexs[i]   # source coor
                coor = roi_indexs[index]        #target coor
                result_mask[coor[0]][coor[1]][coor[2]] = result_mask[coor[0]][coor[1]][coor[2]]+data[dcoor[0]][dcoor[1]][dcoor[2]]
                con_mask[coor[0]][coor[1]][coor[2]] = con_mask[coor[0]][coor[1]][coor[2]]+1
        result_mask = result_mask/(con_mask+0.0000001)
        result_mask[  result_mask < val_th] = 0 
    #    print result_mask[result_mask.nonzero()]
    # print "Time : %s"%(time.time()-st)
    return result_mask
