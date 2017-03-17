from ..core.dataobject import SurfaceDataset
from ..widgets.my_tools import ConstVariable

import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
import numpy as np
import copy

const = ConstVariable()
const.CONTRAST_STEP = 10


class Region(object):
    """
    An object to represent the region and its associated attributes
    """

    def __init__(self, r_id, vtx_feat):
        """
        Parameters
        ----------
        r_id: int
            region id, a unique scalar(actually is vertex number)
        vtx_feat : dict
            key is the id, value is a numpy array with the shape (n_features,)

        Returns
        -------
        """

        # Initialize fields
        # ------------------------------------------------------------------------------------
        self.id = r_id
        self.vtx_feat = vtx_feat
        self.vtx_feat_init = self.vtx_feat.copy()  # save the original vertices.
        self.component = [self]  # component regions list
        self.neighbor = []  # neighbor region list

    def mean_feat(self):
        """
        calculate the mean of the len(self.vtx_feat) feature arrays with the shape of (n_features,)
        """

        # initialize the sum
        s = None
        for v in self.vtx_feat.values():
            s = v.copy()
            s.fill(0)
            break

        # calculate the sum
        for v in self.vtx_feat.values():
            s += v

        return s/len(self.vtx_feat)

    def merge(self, region):
        """
        merge the region to self

        Parameters
        ---------
        region: Region
            a instance of the class Region

        Returns
        -------
        """

        # merge features
        self.vtx_feat.update(region.vtx_feat_init)

        # add region to the component
        self.component.append(region)

        # add region's neighbor to the seed's neighbor
        for i in range(len(region.neighbor)):
            self.add_neighbor(region.neighbor[i])

    def add_neighbor(self, region):
        """
        add the neighbor for self

        Parameters
        ----------
        region: Region
            a instance of the class Region

        Returns
        -------
        """

        if region not in self.component and region not in self.neighbor:
            self.neighbor.append(region)

    def remove_neighbor(self, region):
        """
        remove the neighbor for self

        Parameters
        ----------
        region: Region
            a instance of the class Region

        Returns
        -------
        """

        if region in self.neighbor:
            self.neighbor.remove(region)

    def size(self):
        """
        the size of self

        Returns
        -------
            the size of self
        """

        return len(self.vtx_feat)

    def nearest_neighbor(self):
        """
        find the nearest neighbor of self

        Returns
        -------
            the nearest neighbor and its distance corresponding to self
        """

        measures = np.array([region.mean_feat() for region in self.neighbor])
        self_measure = np.atleast_2d(self.mean_feat())

        # dist = np.sqrt(np.sum((measures - self_measure)**2, 1))  # could be replaced by the following sentence
        dist = cdist(measures, self_measure)

        index = np.argmin(np.array(dist))

        return self.neighbor[index], dist[index]


class SurfaceToRegions(object):

    def __init__(self, surf, scalars, mask=None, n_ring=1):
        """
        represent the surface to preliminary regions

        Parameters
        ----------
        surf: SurfaceDataset
            a instance of the class SurfaceDataset
        mask: scalar_data
            specify a area where the ROI is in.
        n_ring: int
            The n-ring neighbors of v are defined as vertices that are
            reachable from v by traversing no more than n edges in the mesh.

        Returns
        -------
            a instance of itself
        """

        if not isinstance(surf, SurfaceDataset):
            raise TypeError("The argument surf must be a instance of SurfaceDataset!")

        n_vtx = surf.get_vertices_num()

        # just temporarily use the field to find suitable seed_region
        self.scalar = scalars[0]

        if mask is not None:
            id_iter = np.nonzero(mask)[0]
        else:
            id_iter = range(n_vtx)
        self.id_iter = id_iter

        # initialize regions
        self.regions = []
        self.v_id2r_id = dict()
        scalars_count = len(scalars)
        if mask is None:
            for v_id in id_iter:

                vtx_feat = dict()
                vtx_feat[v_id] = np.zeros(scalars_count)
                for i, scalar in enumerate(scalars):
                    vtx_feat[v_id][i] = scalar[v_id]

                self.regions.append(Region(v_id, vtx_feat))
        else:
            for r_id, v_id in enumerate(id_iter):

                vtx_feat = dict()
                vtx_feat[v_id] = np.zeros(scalars_count)
                for i, scalar in enumerate(scalars):
                    vtx_feat[v_id][i] = scalar[v_id]

                self.regions.append(Region(v_id, vtx_feat))
                self.v_id2r_id[v_id] = r_id

        # find neighbors
        # find 1_ring neighbors' id for each region
        # list_of_neighbor_set = [set()] * len(self.regions)  # each element is
        # the reference to the same set object
        list_of_neighbor_set = [set() for i in range(n_vtx)]
        f = surf.get_faces()
        for face in f:
            for v_id in face:
                list_of_neighbor_set[v_id].update(set(face))

        for v_id in range(n_vtx):
            list_of_neighbor_set[v_id].remove(v_id)

        # n_ring neighbors
        list_of_1_ring_neighbor_set = copy.deepcopy(list_of_neighbor_set)
        list_of_n_ring_neighbor_set = copy.deepcopy(list_of_neighbor_set)
        n = 1
        while n < n_ring:

            for neighbor_set in list_of_n_ring_neighbor_set:
                neighbor_set_tmp = neighbor_set.copy()
                for v_id in neighbor_set_tmp:
                    neighbor_set.update(list_of_1_ring_neighbor_set[v_id])

            if n == 1:
                for v_id in range(n_vtx):
                    list_of_n_ring_neighbor_set[v_id].remove(v_id)

            for v_id in range(n_vtx):
                list_of_n_ring_neighbor_set[v_id] -= list_of_neighbor_set[v_id]
                list_of_neighbor_set[v_id] |= list_of_n_ring_neighbor_set[v_id]

            n += 1

        # add neighbors
        if mask is None:
            for r_id in range(len(self.regions)):
                for neighbor_id in list_of_neighbor_set[r_id]:
                    self.regions[r_id].add_neighbor(self.regions[neighbor_id])
        else:
            for r_id in range(len(self.regions)):
                v_id = self.regions[r_id].id
                for neighbor_v_id in list_of_neighbor_set[v_id]:
                    neighbor_r_id = self.v_id2r_id.get(neighbor_v_id)
                    if neighbor_r_id is not None:
                        self.regions[r_id].add_neighbor(self.regions[neighbor_r_id])

    def get_regions(self):
        return self.regions, self.v_id2r_id

    def get_seed_region(self):
        """
        just temporarily use the method to find suitable seed_region

        return
        ------
            the list of seeds
        """

        if not isinstance(self.id_iter, np.ndarray):
            v_id_array = np.array(self.id_iter)
        else:
            v_id_array = self.id_iter

        data = self.scalar
        mask_data = data[v_id_array]
        mask_max = mask_data.max()
        v_id_index = np.nonzero(mask_data == mask_max)[0]

        cnt = 0
        seed_region = []
        for idx in v_id_index:

            cnt += 1
            if cnt > 10:
                break

            if self.v_id2r_id:  # if mask is not None, we need the v_id2r_id.
                r_id = self.v_id2r_id[v_id_array[idx]]
            else:
                r_id = v_id_array[idx]
            seed_region.append(self.regions[r_id])

        return seed_region


class AdaptiveRegionGrowing(object):
    """
    Adaptive region growing performs a segmentation of an image with respect to a set of points.

    Attributes
    ----------
    similarity_criteria: SimilarityCriteria object
        The similarity criteria which control the neighbor to merge to the region
    stop_criteria: StopCriteria object
        The stop criteria which control when the region growing stop

    Methods
    -------
    _compute(region,image)
        do region growing
    """

    def __init__(self, seed_region, stop_criteria=1000, similarity_measure=None):
        """
        Parameters
        ----------
        similarity_measure:
        stop_criteria:

        Returns
        -------
        """

        # initialize the fields
        self.similarity_measure = similarity_measure
        self.stop_criteria = stop_criteria
        self.seed_region = seed_region

        # call methods of the class
        self._compute()

    def _compute(self):
        """
        do region growing
        """

        n_seed = len(self.seed_region)

        # initialize the region size
        region_size = np.zeros(n_seed)
        for r in range(n_seed):
            region_size[r] = self.seed_region[r].size()

        # initialize the region contrast
        region_contrast = [[] for i in range(n_seed)]

        dist = np.empty(n_seed)
        dist.fill(np.inf)  # fill with 'Inf'(infinite), similar to 'NaN'
        # Not a Number (NaN), positive infinity and negative infinity evaluate to
        # True because these are not equal to zero.
        neighbor = [None] * n_seed
        r_in_seed_list = list(self.seed_region)

        while np.any(np.less(region_size, self.stop_criteria)):
            r_to_grow = np.less(region_size, self.stop_criteria)
            dist[np.logical_not(r_to_grow)] = np.inf

            r_index = np.nonzero(r_to_grow)[0]

            for i in r_index:
                # find the nearest neighbor for the each seed region
                r_neighbor, r_dist, = self.seed_region[i].nearest_neighbor()
                dist[i] = r_dist
                neighbor[i] = r_neighbor

            # find the seed which has min neighbor in this iteration
            r = np.argmin(dist)
            target_neighbor = neighbor[r]

            # Prevent a seed from intersecting with another seed
            if target_neighbor not in r_in_seed_list:
                r_in_seed_list.append(target_neighbor)
                # merge the neighbor to the seed
                self.seed_region[r].merge(target_neighbor)

                # compute contrasts
                if len(self.seed_region[r].component) % const.CONTRAST_STEP == 0:
                    neighbor_mean_feat = np.mean([i.mean_feat() for i in self.seed_region[r].neighbor], 0)
                    contrast = np.sqrt(np.sum((self.seed_region[r].mean_feat() - neighbor_mean_feat)**2))
                    region_contrast[r].append(contrast)

            for i in r_index:

                # remove the neighbor from the neighbor list of growing seeds
                self.seed_region[i].remove_neighbor(target_neighbor)

                # update region_size
                if not self.seed_region[i].neighbor:
                    # If the seed has no neighbor, stop its growing.
                    region_size[i] = np.inf

            region_size[r] = region_size[r] + target_neighbor.size()

        # find the max contrast
        for r in range(n_seed):

            # plot the diagram
            plt.figure(r)
            plt.plot(region_contrast[r], 'b*')
            plt.xlabel('contrast step/10 components')
            plt.ylabel('contrast')

            index = np.argmax(region_contrast[r])
            end_index = (index+1)*const.CONTRAST_STEP

            # update component
            self.seed_region[r].component = self.seed_region[r].component[:end_index]
            # update vtx_feat
            self.seed_region[r].vtx_feat = dict()
            for region in self.seed_region[r].component:
                self.seed_region[r].vtx_feat.update(region.vtx_feat_init)
        plt.show()

    def region2text(self):
        """
        save region into text
        """

        for seed in self.seed_region:

            vtx_feat = seed.vtx_feat
            X = np.zeros(len(vtx_feat))
            for index, key in enumerate(vtx_feat.keys()):
                X[index] = key

            file_name = "/nfs/j3/userhome/chenxiayu/workingdir/" + str(seed.id) + "_srg_zstat.label"
            header = str("the number of vertex: " + str(len(vtx_feat)))
            np.savetxt(file_name, X, fmt='%d',
                       header=header, comments="# ascii, label vertexes saved by genius cxy!\n")


class SeededRegionGrowing(object):
    """
    Seeded region growing performs a segmentation of an image with respect to a set of points, known as seeded region.

    Attributes
    ----------
    similarity_criteria: SimilarityCriteria object
        The similarity criteria which control the neighbor to merge to the region
    stop_criteria: StopCriteria object
        The stop criteria which control when the region growing stop

    Methods
    -------
    _compute(region,image)
        do region growing
    """

    def __init__(self, seed_region, stop_criteria=1000, similarity_measure=None):
        """
        Parameters
        ----------
        similarity_measure:
        stop_criteria:

        Returns
        -------
        """

        # initialize the fields
        self.similarity_measure = similarity_measure
        self.stop_criteria = stop_criteria
        self.seed_region = seed_region

        # call methods of the class
        self._compute()

    def _compute(self):
        """
        do region growing
        """

        n_seed = len(self.seed_region)
        region_size = np.zeros(n_seed)
        for r in range(n_seed):
            region_size[r] = self.seed_region[r].size()

        dist = np.empty(n_seed)
        dist.fill(np.inf)  # fill with 'Inf'(infinite), similar to 'NaN'
        # Not a Number (NaN), positive infinity and negative infinity evaluate to
        # True because these are not equal to zero.
        neighbor = [None] * n_seed
        r_in_seed_list = list(self.seed_region)

        while np.any(np.less(region_size, self.stop_criteria)):
            r_to_grow = np.less(region_size, self.stop_criteria)
            dist[np.logical_not(r_to_grow)] = np.inf

            r_index = np.nonzero(r_to_grow)[0]

            for i in r_index:
                # find the nearest neighbor for the each seed region
                r_neighbor, r_dist, = self.seed_region[i].nearest_neighbor()
                dist[i] = r_dist
                neighbor[i] = r_neighbor

            # find the seed which has min neighbor in this iteration
            r = np.argmin(dist)
            target_neighbor = neighbor[r]

            # Prevent a seed from intersecting with another seed
            if target_neighbor not in r_in_seed_list:
                r_in_seed_list.append(target_neighbor)
                # merge the neighbor to the seed
                self.seed_region[r].merge(target_neighbor)

            for i in r_index:

                # remove the neighbor from the neighbor list of growing seeds
                self.seed_region[i].remove_neighbor(target_neighbor)

                # update region_size
                if not self.seed_region[i].neighbor:
                    # If the seed has no neighbor, stop its growing.
                    region_size[i] = np.inf

            region_size[r] = region_size[r] + target_neighbor.size()

    def region2text(self):
        """
        save region into text
        """

        for seed in self.seed_region:

            vtx_feat = seed.vtx_feat
            X = np.zeros(len(vtx_feat))
            for index, key in enumerate(vtx_feat.keys()):
                X[index] = key

            file_name = "/nfs/j3/userhome/chenxiayu/workingdir/" + str(seed.id) + "_srg_zstat.label"
            header = str("the number of vertex: " + str(len(vtx_feat)))
            np.savetxt(file_name, X, fmt='%d',
                       header=header, comments="# ascii, label vertexes saved by genius cxy!\n")
