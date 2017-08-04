import time
import numpy as np
from mayavi import mlab


# ------------------common tools-------------------
def func_timer(func, *args, **kwargs):
    """
    Calculate the time cost of a function.

    Parameters
    ----------
    func : function

    Return
    ------
        Return what the func returns.
    """
    start = time.time()
    func_return = func(*args, **kwargs)
    stop = time.time()
    cost = stop - start
    print 'The function {} costs {} seconds.'.format(func.__name__, cost)
    return func_return


class ConstVariable(object):

    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError, "Can't rebind const ({})".format(name)
        self.__dict__[name] = value


# ------------surface-tree-view tools--------------
def get_curr_hemi(index):
    """
    get the current hemisphere

    Parameter
    ---------
    index : QModelIndex

    Returns
    -------
    hemi_item : Hemisphere
        the current hemisphere
    False : bool
        It means the user has not specified a hemisphere.
    """

    if not index.isValid():
        return False

    parent = index.parent()
    if not parent.isValid():
        hemi_item = index.internalPointer()
    else:
        hemi_item = parent.internalPointer()
    return hemi_item


def get_curr_overlay(index):
    """
    get the current overlay

    Parameter
    ---------
    index : QModelIndex

    Returns
    -------
    ol_item : ScalarData
        the current overlay
    False : bool
        It means the user has not specified a overlay.
    """

    if not index.isValid():
        return False

    parent = index.parent()
    if not parent.isValid():
        return False
    else:
        ol_item = index.internalPointer()
        return ol_item


# --------------surface-view tools-----------------
def toggle_color(color):
    """
    make the color look differently

    Parameter
    ---------
    color: a alterable variable and can be modify in situ
        rgb or rgba
    """

    green_max = 255
    red_max = 255
    blue_max = 255
    if green_max-color[1] >= green_max / 2.0:
        color[:3] = np.array((0, 255, 0))
    elif red_max - color[0] >= red_max / 2.0:
        color[:3] = np.array((255, 0, 0))
    elif blue_max-color[2] >= blue_max / 2.0:
        color[:3] = np.array((0, 0, 255))
    else:
        color[:3] = np.array((0, 0, 255))


def surface_plot(edge_list, start, end, coords):
    """
    Plot a shortest path between start and end as a new actor.

    Parameters
    ----------
    edge_list : dict | list
        The indices are vertices of a graph.
        One index's corresponding element is a collection of vertices which connect with the index.
    start : integer
        path's start vertex's id
    end : integer
        path's end vertex's id
    coords : numpy array
        all vertices' coordinates in the current surface view
    """
    path = bfs(edge_list, start, end)
    path_coords = coords[path]
    x, y, z = path_coords[:, 0], path_coords[:, 1], path_coords[:, 2]

    mlab.plot3d(x, y, z, line_width=100.0)


# ------------common graph theory tools------------
def bfs(edge_list, start, end):
    """
    Return a one of the shortest paths between start and end in a graph.
    The shortest path means a route that goes through the fewest vertices.
    There may be more than one shortest path between start and end.
    But the function just return one of them according to the first find.
    The function takes advantage of the Breadth First Search.

    Parameters
    ----------
    edge_list : dict | list
        The indices are vertices of a graph.
        One index's corresponding element is a collection of vertices which connect with the index.
    start : integer
        path's start vertex's id
    end : integer
        path's end vertex's id

    Returns
    -------
    List
        one of the shortest paths
    False : bool
        There is no path between start and end
    """

    if start == end:
        return [start]

    tmp_path = [start]
    path_queue = [tmp_path]  # a queue used to load temporal paths
    old_nodes = [start]

    while path_queue:

        tmp_path = path_queue.pop(0)
        last_node = tmp_path[-1]

        for link_node in edge_list[last_node]:

            # avoid repetitive detection for a node
            if link_node in old_nodes:
                continue
            else:
                old_nodes.append(link_node)

            if link_node == end:
                # find one of the shortest path
                return tmp_path + [link_node]
            elif link_node not in tmp_path:
                # ready for deeper search
                path_queue.append(tmp_path + [link_node])

    return False
