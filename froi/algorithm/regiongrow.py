# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import numpy as np
from scipy.spatial.distance import cdist, pdist

from ..core.dataobject import Geometry
from meshtool import mesh2graph, get_n_ring_neighbor
from graph_tool import graph2parcel
from tools import slide_win_smooth


def region_growing(image, coordinate, number):
    """Give coordinate and size,return a region."""
    # tmp_image store marks and rg_image store new image after region grow
    nt = number
    tmp_image = np.zeros_like(image)
    rg_image = np.zeros_like(image)
    image_shape = image.shape

    x = int(coordinate[0])
    y = int(coordinate[1])
    z = int(coordinate[2])

    # ensure the coordinate is in the image
    inside = (x >= 0) and (x < image_shape[0]) and (y >= 0) and \
             (y < image_shape[1]) and (z >= 0) and (z < image_shape[2])
    if not inside:
        print "The coordinate is out of the image range."
        return False

    # initialize region_mean and region_size
    region_mean = image[x, y, z]
    region_size = 0

    # initialize neighbor_list with 10000 rows 4 columns
    neighbor_free = 10000
    neighbor_pos = -1
    neighbor_list = np.zeros((neighbor_free, 4))

    # 26 direct neighbor points
    neighbors = [[1, 0, 0],
                 [-1, 0, 0],
                 [0, 1, 0],
                 [0, -1, 0],
                 [0, 0, -1],
                 [0, 0, 1],
                 [1, 1, 0],
                 [1, 1, 1],
                 [1, 1, -1],
                 [0, 1, 1],
                 [-1, 1, 1],
                 [1, 0, 1],
                 [1, -1, 1],
                 [-1, -1, 0],
                 [-1, -1, -1],
                 [-1, -1, 1],
                 [0, -1, -1],
                 [1, -1, -1],
                 [-1, 0, -1],
                 [-1, 1, -1],
                 [0, 1, -1],
                 [0, -1, 1],
                 [1, 0, -1],
                 [1, -1, 0],
                 [-1, 0, 1],
                 [-1, 1, 0]]

    while region_size < nt:
        # (xn, yn, zn) store direct neighbor of seed point
        for i in range(6):
            xn = x + neighbors[i][0]
            yn = y + neighbors[i][1]
            zn = z + neighbors[i][2]

            # ensure the coordinate is in the image
            inside = (xn >= 0) and (xn < image_shape[0]) and (yn >= 0) and \
                     (yn < image_shape[1]) and (zn >= 0) and (zn < image_shape[2])

            # ensure the original flag 0 is not changed
            if inside and tmp_image[xn, yn, zn] == 0:
                # add this point to neighbor_list and mark it with 1
                neighbor_pos = neighbor_pos + 1
                neighbor_list[neighbor_pos] = [xn, yn, zn, image[xn, yn, zn]]
                tmp_image[xn, yn, zn] = 1

        # ensure there is enough space to store neighbor_list
        if neighbor_pos + 100 > neighbor_free:
            neighbor_free += 10000
            new_list = np.zeros((10000, 4))
            neighbor_list = np.vstack((neighbor_list, new_list))

        # the distance between every neighbor point value to new region mean value
        distance = np.abs(neighbor_list[:neighbor_pos+1, 3] - np.tile(region_mean, neighbor_pos+1))

        # chose the min distance point
        # voxel_distance = distance.min()
        index = distance.argmin()

        # mark the new region point with 2 and update new image
        tmp_image[x, y, z] = 2
        rg_image[x, y, z] = image[x, y, z]
        region_size += 1

        # (x, y, z) the new seed point
        x = int(neighbor_list[index][0])
        y = int(neighbor_list[index][1])
        z = int(neighbor_list[index][2])

        # update region mean value
        region_mean = (region_mean*region_size+neighbor_list[index, 3])/(region_size+1)

        # remove the seed point from neighbor_list
        neighbor_list[index] = neighbor_list[neighbor_pos]
        neighbor_pos -= 1

    return rg_image


# --------------new architecture-------------------
class Region(object):
    """
    An object to represent the region unit used for region growing.

    Attributes
    ----------
    vtx_signal : dict
        key is a vertex number, value is a vertex signal with the shape (n_features,)
    neighbors : list
        neighbor regions list
    """

    def __init__(self):
        """
        Parameters
        ----------
        r_id: int
            region id, a unique scalar(actually is vertex number)
        """

        # Initialize fields
        self.vtx_signal = dict()
        self.neighbors = []

    # get region's information
    # -------------------------------------------
    def size(self):
        """
        calculate the number of self's vertices

        Returns
        -------
            the size of self
        """

        return len(self.vtx_signal)

    def mean_signal(self):
        """
        Calculate the mean of all vertices' signals in the region.
        """

        return np.mean(self.vtx_signal.values(), axis=0)

    def nearest_neighbor(self):
        """
        find the nearest neighbor of self

        Returns
        -------
            the nearest neighbor and its distance corresponding to self
        """

        neighbor_signals = np.array([region.mean_signal() for region in self.neighbors])
        self_signal = np.atleast_2d(self.mean_signal())
        dist = cdist(neighbor_signals, self_signal)

        # TODO only suitable for activity value this kind of data
        R_and_N_signals = neighbor_signals + self_signal
        normalize_scale = R_and_N_signals - np.min(R_and_N_signals) + 1
        dist = dist / normalize_scale

        index = np.argmin(np.array(dist))

        return self.neighbors[index], dist[index]

    def get_vertices(self):
        return self.vtx_signal.keys()

    def get_vtx_signal(self):
        return self.vtx_signal

    def get_neighbors(self):
        return self.neighbors

    # update region
    # -------------------------------------------
    def add_neighbor(self, region):
        """
        add the neighbor for self

        Parameters
        ----------
        region: Region
        """

        if region not in self.neighbors:
            self.neighbors.append(region)

    def remove_neighbor(self, region):
        """
        remove the neighbor for self

        Parameters
        ----------
        region: Region
        """

        if region in self.neighbors:
            self.neighbors.remove(region)

    def remove_neighbors(self, regions):
        map(self.remove_neighbor, regions)

    def add_vertex(self, v_id, vtx_signal):
        """
        add intrinsic vertices for self

        Parameters
        ----------
        v_id : integer
            vertex number
        vtx_signal : dict
            vertices and their signals
        """

        self.vtx_signal[v_id] = vtx_signal[v_id]

    # output
    # --------------------------------------------
    def region2text(self, file_name):
        """
        save region into text
        """
        X = np.array(self.get_vertices())
        header = str("the number of vertex: " + str(self.size()))
        np.savetxt(file_name, X, fmt='%d', header=header, comments="# ascii, label vertexes\n")


class EvolvingRegion(Region):
    """
    An object to represent the evolving region.

    Attributes
    ----------
    seeds : list
        the seed vertices' numbers
    component : list
        component regions list
    """

    def __init__(self, seeds):
        """
        Parameters
        ----------
        r_id: int
            region id, a unique scalar(actually is vertex number)
        """
        super(EvolvingRegion, self).__init__()

        # Initialize fields
        # -----------------
        self.seeds = seeds
        self.component = []

    # get information
    # -------------------------------------------
    def get_seeds(self):
        return self.seeds

    def get_component(self):
        return self.component

    # update region
    # -------------------------------------------
    def merge(self, region):
        """
        merge the region to self

        Parameters
        ---------
        region: Region
        """

        # merge vertices and signals
        self.vtx_signal.update(region.vtx_signal)

        # add region to the component
        self.component.append(region)

        # add region's neighbors to the self's neighbors
        for i in region.neighbors:
            self.add_neighbor(i)

    def add_neighbor(self, region):
        """
        add the neighbor for self

        Parameters
        ----------
        region: Region
        """

        if region not in self.component and region not in self.neighbors:
            self.neighbors.append(region)


class RegionGrow(object):
    """
    Region growing performs a segmentation of an object with respect to a set of points.

    Attributes
    ----------


    Methods
    -------
    _compute(region,image)
        do region growing

    Examples
    --------
    Use vertex with peak value as a seed:
        rg = RegionGrow([], stop_criteria)
        evolved_regions = rg.arg_parcel(surf, vtx_signal, mask, n_ring)
    Specify seeds manually:
        rg = RegionGrow(seeds_id, stop_criteria)
        evolved_regions = rg.arg_parcel(surf, vtx_signal, mask, n_ring)
    """

    def __init__(self):

        # initialize fields
        # -----------------
        self.regions = []
        self.v_id2r_id = None
        self._assess_func = None

        self.assess_dict = {
            'transition level': self._assess_transition_level,
            'mean signal dist': self._assess_mean_signal_dist,
            'gray level dist1': self._assess_gray_level_dist1,
            'gray level dist2': self._assess_gray_level_dist2,
            'gray level dist3': self._assess_gray_level_dist3
        }

    def surf2regions(self, surf, vtx_signal, mask=None, n_ring=1, n_parcel=0):
        """
        represent the surface to preliminary regions

        Parameters
        ----------
        surf : Geometry
            a instance of the class GeometryData
        vtx_signal : numpy array
            NxM array, N is the number of vertices,
            M is the number of measurements or time points.
        mask : scalar_data
            specify a area where the ROI is in.
        n_ring : integer
            The n-ring neighbors of v are defined as vertices that are
            reachable from v by traversing no more than n edges in the mesh.
        n_parcel : integer
            If n_parcel is 0, each vertex will be a region,
            else the surface will be partitioned to n_parcel parcels.
        """

        if not isinstance(surf, Geometry):
            raise TypeError("The argument surf must be a instance of GeometryData!")

        n_vtx = surf.vertices_count()
        self.v_id2r_id = -np.ones(n_vtx, dtype=np.int)
        if n_parcel:
            # Prepare parcels, neighbors and v_id2r_id
            graph = mesh2graph(surf.faces, n=n_ring,
                               vtx_signal=vtx_signal, weight_normalization=True)
            if mask is not None:
                graph = graph[np.nonzero(mask)[0]]
            graph, region_neighbors = graph2parcel(graph, n_parcel)
            for node, data in graph.nodes_iter(data=True):
                self.v_id2r_id[node] = data['label']
        else:
            # Prepare neighbors and v_id2r_id
            if mask is None:
                for i in range(n_vtx):
                    self.v_id2r_id[i] = i
                region_neighbors = get_n_ring_neighbor(surf.faces, n_ring)
            else:
                mask_id = np.nonzero(mask)[0]
                vtx_neighbors = get_n_ring_neighbor(surf.faces, n_ring, mask=mask)
                region_neighbors = []
                for r_id, v_id in enumerate(mask_id):
                    self.v_id2r_id[v_id] = r_id
                    region_neighbors.append(vtx_neighbors[v_id])

                # warning: a region's neighbors is stored as a list rather than a set at here.
                region_neighbors = [map(lambda v: self.v_id2r_id[v], vertices) for vertices in region_neighbors]

        # initialize regions
        n_regions = np.max(self.v_id2r_id) + 1
        self.regions = [Region() for r_id in range(n_regions)]
        for v_id, r_id in enumerate(self.v_id2r_id):
            if r_id != -1:
                self.regions[r_id].add_vertex(v_id, vtx_signal=vtx_signal)

        # add neighbors
        for r_id, region in enumerate(self.regions):
            for neighbor_id in region_neighbors[r_id]:
                region.add_neighbor(self.regions[neighbor_id])

    def arg_parcel(self, seeds_id, stop_criteria, whole_results=False, half_width=0, assess_step=1):
        """
        Adaptive region growing performs a segmentation of an object with respect to a set of points.

        Parameters
        ----------
        seeds_id : list
            Its elements are also list, called sub-list,
            each sub-list contains a group of seed vertices which are used to initialize a evolving region.
            Different sub-list initializes different evolving region.
        stop_criteria : integer
            The stop criteria which control when the region growing stop
        whole_results : bool
            If true, then return max_assess_regions, evolved_regions, region_assessments and more.
            If false, then just return max_assess_region.
        half_width : integer
        assess_step : integer
            do one assessment per 'assess_step' components

        Returns
        -------
        max_assess_regions : list
            max-assess region is of max assessment value
            among corresponding evolved region's evolving history.
        evolved_regions : list
            Include all evolved regions after self._compute()
        region_assessment : list
            All assessment values for corresponding evolved region
        assess_step : integer
        r_outer_mean : list
        r_inner_min: list
        """

        # call methods of the class
        evolved_regions, region_assessments, r_outer_mean, r_inner_min\
            = self._compute(seeds_id, stop_criteria, assess_step)
        max_assess_regions = [EvolvingRegion(r.get_seeds()) for r in evolved_regions]
        # find the max assessed value
        for r_idx, r in enumerate(evolved_regions):

            region_assessments[r_idx] = slide_win_smooth(region_assessments[r_idx], half_width)
            index = np.argmax(region_assessments[r_idx])
            end_index = (index+1) * assess_step

            for region in r.get_component()[:end_index]:
                max_assess_regions[r_idx].merge(region)

        if whole_results:
            return max_assess_regions, evolved_regions, region_assessments, assess_step, r_outer_mean, r_inner_min
        else:
            return max_assess_regions

    def srg_parcel(self, seeds_id, stop_criteria):
        """
        Seed region growing performs a segmentation of an object with respect to a set of points.

        Parameters
        ----------
        seeds_id : list
            Its elements are also list, called sub-list,
            each sub-list contains a group of seed vertices which are used to initialize a evolving region.
            Different sub-list initializes different evolving region.
        stop_criteria : integer
            The stop criteria which control when the region growing stop

        Returns
        -------
        evolved_regions : list
            Include all evolved regions after self._compute()
        """
        # call methods of the class
        evolved_regions, _, _, _ = self._compute(seeds_id, stop_criteria)
        return evolved_regions

    @staticmethod
    def connectivity_grow(seeds_id, edge_list):
        """
        Find all vertices for each group of initial seeds.

        Parameters
        ----------
        seeds_id : list
            Its elements are also list, called sub-list,
            each sub-list contains a group of seed vertices which are used to initialize a evolving region.
            Different sub-list initializes different connected region.
        edge_list : dict | list
            The indices are vertices of a graph.
            One index's corresponding element is a collection of vertices which connect with the index.
        Return
        ------
        connected_regions : list
            Its elements are set, each set contains all vertices which connect with corresponding seeds.
        """
        connected_regions = [set(seeds) for seeds in seeds_id]

        for idx, region in enumerate(connected_regions):
            outmost_vtx = region.copy()
            while outmost_vtx:
                print 'connected region{idx} size: {size}'.format(idx=idx, size=len(region))
                region_old = region.copy()
                for vtx in outmost_vtx:
                    region.update(edge_list[vtx])
                outmost_vtx = region.difference(region_old)
        return connected_regions

    def _compute(self, seeds_id, stop_criteria, assess_step=0):
        """
        do region growing
        """

        # -------initialize evolving_regions and merged_regions------
        evolving_regions = []
        merged_regions = []
        if seeds_id:
            for seeds in seeds_id:
                evolving_region = EvolvingRegion(seeds)
                merged_regions_tmp = []
                for seed in seeds:
                    seed_r_id = self.v_id2r_id[seed]
                    if seed_r_id == -1:
                        raise RuntimeError("At least one of your seeds is out of the mask!")
                    else:
                        seed_region = self.regions[seed_r_id]
                        if seed_region in merged_regions:
                            raise RuntimeError("More than one evolving regions are"
                                               "assigned with a same unit region initially!")
                        elif seed_region in merged_regions_tmp:
                            # do not merge the same unit region repeatedly
                            continue
                        else:
                            evolving_region.merge(seed_region)
                            merged_regions_tmp.append(seed_region)
                evolving_regions.append(evolving_region)
                merged_regions.extend(merged_regions_tmp)
        else:
            evolving_regions.append(self.get_seed_region())
            for evo_r in evolving_regions:
                merged_regions.extend(evo_r.get_component())

        for evo_r in evolving_regions:
            evo_r.remove_neighbors(merged_regions)

        # ------initialize other variables-------
        n_seed = len(evolving_regions)
        region_size = np.array([region.size() for region in evolving_regions])
        region_assessments = [[] for _ in range(n_seed)]
        r_outer_mean = [[] for _ in range(n_seed)]  # mean value of the region's outer boundary
        r_inner_min = [[] for _ in range(n_seed)]  # minimum value in the region

        # Positive infinity and negative infinity evaluate to True, because they are not equal to zero.
        dist = np.empty(n_seed)
        dist.fill(np.inf)

        neighbor = [None] * n_seed

        if assess_step:
            for i in range(len(evolving_regions)):
                if len(evolving_regions[i].get_component()) % assess_step == 0:
                    assessed_value = self._assess_func(evolving_regions[i])
                    region_assessments[i].append(assessed_value)
                    outer_signals = [r.mean_signal() for r in evolving_regions[i].get_neighbors()]
                    inner_signals = [r.mean_signal() for r in evolving_regions[i].get_component()]
                    r_outer_mean[i].append(np.mean(outer_signals))
                    r_inner_min[i].append(np.min(inner_signals))
                    print 'Evolving region{} size: {}'.format(i, evolving_regions[i].size())

        # ------main cycle------
        while np.any(np.less(region_size, stop_criteria)):
            r_to_grow = np.less(region_size, stop_criteria)
            dist[np.logical_not(r_to_grow)] = np.inf

            r_index = np.nonzero(r_to_grow)[0]

            for i in r_index:
                # find the nearest neighbor for the each seed region
                r_neighbor, r_dist, = evolving_regions[i].nearest_neighbor()
                dist[i] = r_dist
                neighbor[i] = r_neighbor

            # find the seed which has the nearest neighbor in this iteration
            r = np.argmin(dist)
            target_neighbor = neighbor[r]

            # Prevent a seed from intersecting with another seed
            if target_neighbor not in merged_regions:
                merged_regions.append(target_neighbor)
                # merge the neighbor to the seed
                evolving_regions[r].merge(target_neighbor)
                region_size[r] = region_size[r] + target_neighbor.size()

                if assess_step:
                    # compute assessments
                    if len(evolving_regions[r].get_component()) % assess_step == 0:
                        assessed_value = self._assess_func(evolving_regions[r])
                        region_assessments[r].append(assessed_value)
                        outer_signals = [i.mean_signal() for i in evolving_regions[r].get_neighbors()]
                        inner_signals = [i.mean_signal() for i in evolving_regions[r].get_component()]
                        r_outer_mean[r].append(np.mean(outer_signals))
                        r_inner_min[r].append(np.min(inner_signals))
                        print 'Evolving region{} size: {}'.format(r, evolving_regions[r].size())

            for i in r_index:
                # remove the neighbor from the neighbor list of growing seeds
                evolving_regions[i].remove_neighbor(target_neighbor)

                # update region_size
                if not evolving_regions[i].neighbors:
                    # If the seed has no neighbor, stop its growing.
                    try:
                        region_size[i] = stop_criteria[i]
                    except IndexError:
                        # It means that the user uses one stop criteria for all evolving regions.
                        region_size[i] = stop_criteria[0]

        return evolving_regions, region_assessments, r_outer_mean, r_inner_min

    def get_regions(self):
        return self.regions, self.v_id2r_id

    def get_seed_region(self):
        """
        used to find a region with max mean feature as seed region.
        The features are usually activity values.

        Return
        ------
            evolving_region : EvolvingRegion
        """

        mean_signal = [np.mean(region.mean_signal()) for region in self.regions]
        seed_r_id = np.argmax(mean_signal)
        seed_v_id = np.where(self.v_id2r_id == seed_r_id)[0][0]
        evolving_region = EvolvingRegion(seed_v_id)
        evolving_region.merge(self.regions[seed_r_id])

        return evolving_region

    def set_assessment(self, assess_type):
        self._assess_func = self.assess_dict[assess_type]

    def get_assess_types(self):
        return self.assess_dict.keys()

    @staticmethod
    def _assess_mean_signal_dist(region):
        """
        Calculate the euclidean distance between the region's mean signal and its neighbors' mean signal.
        The distance is regarded as the region's assessed value

        Parameter
        ---------
        region : Region

        Return
        ------
        assessed_value : float
            Larger assessed_value means better grown region.
        """

        neighbor_mean_signal = np.mean([i.mean_signal() for i in region.get_neighbors()], 0)
        assessed_value = np.sqrt(np.sum((region.mean_signal() - neighbor_mean_signal)**2))

        return assessed_value

    @staticmethod
    def _assess_transition_level(region):
        """
        Calculate the transition level on the region's boundary.
        The result is regarded as the region's assessed value.
        Adapted from (Chantal et al. 2002).

        Parameter
        ---------
        region : Region

        Return
        ------
        assessed_value : float
            Larger assessed_value means better grown region.
        """

        outer_boundary = region.get_neighbors()

        # find all couples
        couples = []
        for i in outer_boundary:
            tmp_couples = [(n, i) for n in i.get_neighbors() if n in region.get_component()]
            couples.extend(tmp_couples)
        # calculate assessed value
        couples_signal = map(lambda x: [x[0].mean_signal(), x[1].mean_signal()], couples)
        couples_dist = map(pdist, couples_signal)
        assessed_value = np.mean(couples_dist)

        return assessed_value

    @staticmethod
    def _assess_gray_level_dist1(region):
        """
        Calculate the within-cluster similarity for the region.
        The result is regarded as the region's assessed value.
        Adapted from (Chantal et al. 2002).
        Parameter
        ---------
        region : Region
        Return
        ------
        inv_gray_level_dist : float
            Larger assessed_value means better grown region.
        """

        mean_signal = np.atleast_2d(region.mean_signal())
        r_variance = np.mean(cdist(region.vtx_signal.values(), mean_signal))

        gray_level_dist = np.sqrt(r_variance)
        if gray_level_dist != 0:
            inv_gray_level_dist = 1 / float(gray_level_dist)
        else:
            inv_gray_level_dist = np.inf

        return inv_gray_level_dist

    def _assess_gray_level_dist2(self, region):
        """
        Calculate the within-cluster similarity for the region and its complement.
        The result is regarded as the region's assessed value.
        Adapted from (Chantal et al. 2002).

        Parameter
        ---------
        region : Region

        Return
        ------
        inv_gray_level_dist : float
            Larger assessed_value means better grown region.
        """
        r_c = EvolvingRegion('region_complement')
        for r in self.regions:
            if r not in region.get_component():
                r_c.merge(r)

        r_mean_signal = np.atleast_2d(region.mean_signal())
        r_c_mean_signal = np.atleast_2d(r_c.mean_signal())
        r_variance = np.mean(cdist(region.get_vtx_signal().values(), r_mean_signal))
        r_c_variance = np.mean(cdist(r_c.get_vtx_signal().values(), r_c_mean_signal))

        gray_level_dist = np.sqrt(r_variance + r_c_variance)
        if gray_level_dist != 0:
            inv_gray_level_dist = 1 / float(gray_level_dist)
        else:
            inv_gray_level_dist = np.inf

        return inv_gray_level_dist

    def _assess_gray_level_dist3(self, region):
        """
        Calculate the within-cluster similarity for the region and its complement.
        The result is regarded as the region's assessed value.
        Adapted from (Chantal et al. 2002).

        Parameter
        ---------
        region : Region

        Return
        ------
        inv_gray_level_dist : float
            Larger assessed_value means better grown region.
        """
        r_c = EvolvingRegion('region_complement')
        for r in self.regions:
            if r not in region.get_component():
                r_c.merge(r)

        r_mean_signal = np.atleast_2d(region.mean_signal())
        r_c_mean_signal = np.atleast_2d(r_c.mean_signal())
        r_variance = np.sum(cdist(region.get_vtx_signal().values(), r_mean_signal))
        r_c_variance = np.sum(cdist(r_c.get_vtx_signal().values(), r_c_mean_signal))

        gray_level_dist = np.sqrt(r_variance + r_c_variance)
        if gray_level_dist != 0:
            inv_gray_level_dist = 1 / float(gray_level_dist)
        else:
            inv_gray_level_dist = np.inf

        return inv_gray_level_dist
