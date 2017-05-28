from ..core.dataobject import SurfaceDataset
from ..widgets.my_tools import ConstVariable
from meshtool import get_n_ring_neighbor, mesh2graph
from graph_tool import graph2parcel

import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
import numpy as np

const = ConstVariable()
const.CONTRAST_STEP = 10


class Region(object):
    """
    An object to represent the region and its associated attributes
    """

    def __init__(self, r_id):
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
        self.vtx_feat = dict()
        self.vtx_feat_init = None  # save the original vertices.
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
        self.vtx_feat.update(region.vtx_feat)

        # add region to the component
        self.component.extend(region.component)

        # add region's neighbor to the seed's neighbor
        for i in region.neighbor:
            self.add_neighbor(i)

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

    def add_vertex(self, v_id, vtx_signal):
        self.vtx_feat[v_id] = vtx_signal[v_id]


class SurfaceToRegions(object):

    def __init__(self, surf, vtx_signal, mask=None, n_ring=1, n_parcel=0):
        """
        represent the surface to preliminary regions

        Parameters
        ----------
        surf: SurfaceDataset
            a instance of the class SurfaceDataset
        vtx_signal : numpy array
            NxM array, N is the number of vertices,
            M is the number of measurements or time points.
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
        self.v_id2r_id = -np.ones(n_vtx, dtype=np.int)
        if n_parcel:
            # Prepare parcels, neighbors and v_id2r_id
            graph = mesh2graph(surf.get_faces(),
                               vtx_signal=vtx_signal, weight_normalization=True)
            if mask is not None:
                graph = graph[np.nonzero(mask)[0]]
            graph, region_neighbors = graph2parcel(graph, n_parcel)
            for node, data in graph.nodes_iter(data=True):
                self.v_id2r_id[node] = data['label']
        else:
            # Prepare neighbors and v_id2r_id
            vtx_neighbors = get_n_ring_neighbor(surf.get_faces(), n_ring)
            if mask is None:
                for i in range(n_vtx):
                    self.v_id2r_id[i] = i
                region_neighbors = vtx_neighbors
            else:
                tmp_neighbors = []
                mask_id = np.nonzero(mask)[0]
                for r_id, v_id in enumerate(mask_id):
                    self.v_id2r_id[v_id] = r_id
                    tmp_neighbors.append(vtx_neighbors[v_id].intersection(mask_id))

                # warning: a region's neighbors is stored as a list rather than a set at here.
                region_neighbors = [map(lambda v: self.v_id2r_id[v], vertices) for vertices in tmp_neighbors]

        # initialize regions
        n_regions = np.max(self.v_id2r_id) + 1
        self.regions = [Region(r_id) for r_id in range(n_regions)]
        for v_id, r_id in enumerate(self.v_id2r_id):
            if r_id != -1:
                self.regions[r_id].add_vertex(v_id, vtx_signal=vtx_signal)
        for region in self.regions:
            region.vtx_feat_init = region.vtx_feat.copy()

        # add neighbors
        for r_id, region in enumerate(self.regions):
            for neighbor_id in region_neighbors[r_id]:
                region.add_neighbor(self.regions[neighbor_id])

    def get_regions(self):
        return self.regions, self.v_id2r_id

    def get_seed_region(self):
        """
        used to find a region with max mean feature as seed region.
        The features are usually activity values.

        Return
        ------
            Region
        """

        mean_feat = [np.mean(region.mean_feat()) for region in self.regions]
        seed_r_id = np.argmax(mean_feat)

        return self.regions[seed_r_id]


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

            file_name = "/nfs/j3/userhome/chenxiayu/workingdir/" + str(seed.id) + "_arg_zstat.label"
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
