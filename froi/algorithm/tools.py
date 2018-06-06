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


def normalize_arr(array, normalize, scale_length=255.0):
    """Normalize the array."""

    # If normalize is in (None, False, 0), return the original array.
    if not normalize:
        return array

    if normalize is True:
        normalize = array.min(), array.max()
    elif np.isscalar(normalize):
        normalize = (0, normalize)
    elif isinstance(normalize, tuple) and (normalize[0] == normalize[1]):
        normalize = array.min(), array.max()
    nmin, nmax = normalize

    if nmin:
        array = array - nmin

    if nmax == nmin:
        # If the original array's elements are same, return zero array.
        return array
    else:
        scale = float(scale_length) / (nmax - nmin)
        if scale != 1.0:
            array = array * scale
        return array.clip(0, scale_length)


class ConstVariable(object):

    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError, "Can't rebind const ({})".format(name)
        self.__dict__[name] = value


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
def bfs(edge_list, start, end, deep_limit=np.inf):
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
    deep_limit : integer
        Limit the search depth to keep off too much computation.
        The deepest depth is specified by deep_limit.
        If the search depth reach the limitation without finding the end vertex, it returns False.

    Returns
    -------
    List
        one of the shortest paths
        If the list is empty, it means we can't find a path between
        the start and end vertices within the limit of deep_limit.
    """

    if start == end:
        return [start]

    tmp_path = [start]
    path_queue = [tmp_path]  # a queue used to load temporal paths
    old_nodes = [start]

    while path_queue:

        tmp_path = path_queue.pop(0)
        if len(tmp_path) > deep_limit:
            return []
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

    return []


# ----------------signal processing----------------
def slide_win_smooth(seq, half_width=0):
    """
    smooth a sequence by slide window
    :param seq: numpy.ndarray or other sequences
    :param half_width: integer
        The half width of the slide window
    :return: seq_smoothed: 1-D numpy.ndarray
    """
    if not isinstance(seq, np.ndarray):
        seq = np.array(seq)
    if seq.ndim != 1:
        raise ValueError("The function only supports for 1-D sequence at present!")
    if 2*half_width >= len(seq):
        raise RuntimeError("The half_width is too big!")

    seq_smoothed = np.array(seq, dtype=np.float64)
    for idx in range(half_width, len(seq)-half_width):
        seq_smoothed[idx] = np.mean(seq[idx-half_width:idx+half_width+1])

    return seq_smoothed


# --------------matplotlib plot tools--------------
class VlineMover(object):
    def __init__(self, vline, x_round=False):
        self.vline = vline
        self.x_round = x_round
        self.ax = vline.axes
        self.x = vline.get_xdata()
        self.y = vline.get_ydata()
        self.cid = vline.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event):
        if event.button == 1 and event.inaxes == self.ax:
            if self.x_round:
                self.x = [round(event.xdata)] * 2
            else:
                self.x = [event.xdata] * 2
            self.vline.set_data(self.x, self.y)
            self.vline.figure.canvas.draw()
