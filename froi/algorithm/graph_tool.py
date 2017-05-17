import numpy as np
from networkx import to_scipy_sparse_matrix
from scipy.sparse import dia_matrix, linalg

# FIXME uncouple the module from skimage's furture module
from skimage.future.graph import _ncut_cy
from skimage.future.graph.graph_cut import partition_by_cut, get_min_ncut, cut_normalized


# ---------------------------get information from graph-----------------------------------
def DW_matrices(graph):
    """
    NOTE: copy from skimage.future.graph._ncut.DW_matrices--version: 0.12.3
    Returns the diagonal and weight matrices of a graph.

    Parameters
    ----------
    graph : nx.Graph

    Returns
    -------
    D : csc_matrix
        The diagonal matrix of the graph. ``D[i, i]`` is the sum of weights of
        all edges incident on `i`. All other entries are `0`.
    W : csc_matrix
        The weight matrix of the graph. ``W[i, j]`` is the weight of the edge
        joining `i` to `j`.
    """
    # sparse.eighsh is most efficient with CSC-formatted input
    W = to_scipy_sparse_matrix(graph, format='csc')
    entries = W.sum(axis=0)
    D = dia_matrix((entries, 0), shape=W.shape).tocsc()

    return D, W


def node_attr2array(graph, attrs):
    """
    extract nodes' attributes into a array
    :param graph: nx.Graph
    :param attrs: tuple (e.g. ('ncut label', 'color'))
        nodes' attributes which are going to be saved
    :return: numpy array
        each row_index represents a node; each column represent a nodes' attribute.
    """
    n_vtx = graph.number_of_nodes()
    arr_shape = (n_vtx, len(attrs))
    arr = np.zeros(arr_shape)
    for node, data in graph.nodes_iter(data=True):
        for idx, attr in enumerate(attrs):
            arr[node, idx] = data[attr]
    return arr


# ------------------------------about normalized cut--------------------------------------
def two_ncut(graph, num_cuts):
    """
    NOTE: Adapt from skimage.future.graph.graph_cut._ncut_relabel--version: 0.12.3
    Perform Normalized Graph cut on the nx.Graph.
    Partition the graph into 2

    Parameters
    ----------
    graph : nx.Graph
    num_cuts : int
        The number or N-cuts to perform before determining the optimal one.

    Returns
    -------
    (nx.Graph, nx.Graph) : two subgraphs of the graph
    (nx.Graph, None) : the first element is the graph itself
        This means the graph can't be further sub-divided.
    """
    d, w = DW_matrices(graph)
    m = w.shape[0]

    if m > 2:
        d2 = d.copy()
        # Since d is diagonal, we can directly operate on its data
        # the inverse of the square root
        d2.data = np.reciprocal(np.sqrt(d2.data, out=d2.data), out=d2.data)

        # Refer Shi & Malik 2001, Equation 7, Page 891
        vals, vectors = linalg.eigsh(d2 * (d - w) * d2, which='SM',
                                     k=min(100, m - 2))

        # Pick second smallest eigenvector.
        # Refer Shi & Malik 2001, Section 3.2.3, Page 893
        vals, vectors = np.real(vals), np.real(vectors)
        index2 = _ncut_cy.argmin2(vals)
        ev = vectors[:, index2]

        cut_mask, mcut = get_min_ncut(ev, d, w, num_cuts)

        if mcut != np.inf:
            # Sub divide and perform N-cut again
            # Refer Shi & Malik 2001, Section 3.2.5, Page 893
            sub1, sub2 = partition_by_cut(cut_mask, graph)

            return sub1, sub2
    return graph, None


def graph2parcel(graph, n=2, num_cuts=10, in_place=True, max_edge=1.0):
    """
    NOTE: Adapt from skimage.future.graph.graph_cut.cut_normalized--version: 0.12.3
    Divide the graph into n parcels according to nodes' similarity.
    All nodes belonging to a parcel are assigned a unique label in the output.

    Parameters
    ----------
    graph : nx.Graph
    n : integer
        Decide the number of parcels for output.
    num_cuts: int
        The number or N-cuts to perform before determining the optimal one.
    in_place: bool
        If set, modifies `graph` in place. For each node `n` the function will
        set a new attribute ``graph.node[n]['label']``.
    max_edge: float, optional
        The maximum possible value of an edge in the graph. This corresponds to
        an edge between identical regions. This is used to put self
        edges in the graph.

    Returns
    -------
    out1: nx.Graph
        The new labeled Graph.
    out2: list
        A Element which belongs to the list's first axis is a list of parcel neighbors.
        A element's index is equivalent to a parcel's label.
        So the parcel neighbors belong to the parcel which has a related label.
    """
    if not in_place:
        graph = graph.copy()

    for node, data in graph.nodes_iter(data=True):
        graph.add_edge(node, node, weight=max_edge)

    # normalized cut begins
    subgraphs = [graph]
    min_parcels = []
    while len(subgraphs)+len(min_parcels) < n and subgraphs:
        subgraphs.sort(key=lambda x: x.number_of_nodes(), reverse=True)
        subgraph = subgraphs.pop(0)
        sub1, sub2 = two_ncut(subgraph, num_cuts)
        if sub2 is None:
            min_parcels.append(sub1)
        else:
            subgraphs.extend([sub1, sub2])
    if not subgraphs:
        print 'The graph can not be further sub-divided!'

    # assign labels for each parcel & find neighbor parcels
    node_neighbors = list()
    edge_dict = graph.edge
    for label, parcel in enumerate(subgraphs):
        node_neighbors.append(set())  # initialize the parcel's neighbor set
        for node, data in parcel.nodes_iter(data=True):
            data['label'] = label  # assign label for the parcel
            node_neighbors[label].update(edge_dict[node].keys())
        node_neighbors[label].difference_update(parcel.nodes())  # remove the parcel's own nodes
    for label, parcel in enumerate(min_parcels, len(subgraphs)):
        node_neighbors.append(set())  # initialize the parcel's neighbor set
        for node, data in parcel.nodes_iter(data=True):
            data['label'] = label
            node_neighbors[label].update(edge_dict[node].keys())
        node_neighbors[label].difference_update(parcel.nodes())  # remove the parcel's own nodes
    # transform node to parcel label
    parcel_neighbors = [map(lambda x: graph.node[x]['label'], nodes) for nodes in node_neighbors]
    parcel_neighbors = [np.unique(parcels) for parcels in parcel_neighbors]

    return graph, parcel_neighbors


def graph_ncut_thr(graph, thresh=0.001, num_cuts=10, in_place=True, max_edge=1.0):
    """
    Perform Normalized Graph cut on the nx.Graph. Recursively perform
    a 2-way normalized cut on it. All nodes belonging to a subgraph
    that cannot be cut further are assigned a unique label in the output.

    Parameters
    ----------
    graph: nx.Graph
    thresh: float
        The threshold. A subgraph won't be further subdivided if the
        value of the N-cut exceeds `thresh`.
    num_cuts: int
        The number or N-cuts to perform before determining the optimal one.
    in_place: bool
        If set, modifies `graph` in place. For each node `n` the function will
        set a new attribute ``graph.node[n]['ncut label']``.
    max_edge: float, optional
        The maximum possible value of an edge in the graph. This corresponds to
        an edge between identical regions. This is used to put self
        edges in the graph.

    Returns
    -------
    out: nx.Graph
        The new labeled Graph.
    """
    if not in_place:
        graph = graph.copy()

    # If sorted(graph.nodes()) == range(graph.number_of_nodes()),
    # then the vector named labels which is defined later has a direct representation.
    # That means the vector's index is equal to node,
    # and its element represents the node's label.
    sorted_nodes = sorted(graph.nodes())
    for label, node in enumerate(sorted_nodes):
        # prepare for skimage.future.graph.graph_cut._label_all--version: 0.12.3
        graph.node[node]['labels'] = [label]

    labels = np.array(range(graph.number_of_nodes()))
    labels = cut_normalized(labels, graph, thresh=thresh,
                            num_cuts=num_cuts, in_place=in_place, max_edge=max_edge)

    return labels
