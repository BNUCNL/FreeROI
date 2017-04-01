import os
import sys
import sip

from traits.api import HasTraits, Instance
from traitsui.api import View, Item
from tvtk.api import tvtk
from PyQt4.QtGui import *
from PyQt4 import QtCore
from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel
from mayavi import mlab
from scipy.spatial.distance import cdist
import numpy as np

from treemodel import TreeModel
from my_tools import bfs, toggle_color


# Helpers
# ---------------------------------------------------------------------------------------------------------
def _toggle_toolbar(figure, show=None):
    """
    Toggle toolbar display

    Parameters
    ----------
    figure: the mlab figure
    show : bool | None
        If None, the state is toggled. If True, the toolbar will
        be shown, if False, hidden.
    """

    if figure.scene is not None:
        if hasattr(figure.scene, 'scene_editor'):
            # Within TraitsUI
            bar = figure.scene.scene_editor._tool_bar
        else:
            # Mayavi figure
            bar = figure.scene._tool_bar

        if show is None:
            if hasattr(bar, 'isVisible'):
                show = not bar.isVisble()
            elif hasattr(bar, 'Shown'):
                show = not bar.Shown()

        if hasattr(bar, 'setVisible'):
            bar.setVisible(show)
        elif hasattr(bar, 'Show'):
            bar.Show(show)


# show surface
# ---------------------------------------------------------------------------------------------------------
class Visualization(HasTraits):

    scene = Instance(MlabSceneModel, ())

    view = View(Item("scene", height=400, width=400,
                     editor=SceneEditor(scene_class=MayaviScene), show_label=False),
                resizable=True)


class SurfaceView(QWidget):

    # Signals
    class SeedPicked(QtCore.QObject):
        seed_picked = QtCore.pyqtSignal()
    seed_picked = SeedPicked()

    def __init__(self, parent=None):
        super(SurfaceView, self).__init__(parent)

        # initialize GUI
        self.setMinimumSize(800, 850)
        self.setBackgroundRole(QPalette.Dark)

        # get mayavi scene
        # The edit_traits call will generate the widget to embed.
        self.visualization = Visualization()
        surface_view = self.visualization.edit_traits(parent=self, kind="subpanel").control
        # self.ui.setParent(self)
        # get rid of the toolbar
        figure = mlab.gcf()
        _toggle_toolbar(figure, False)

        # Initialize some fields
        self.surface_model = None
        self.surf = None
        self.coords = None
        self.faces = None
        self.rgba_lut = None
        self.gcf_flag = True
        self.plot_start = None
        self.path = []
        self.graph = None
        self.surfRG_flag = False
        self.seed_pos = []

        hlayout = QHBoxLayout()
        hlayout.addWidget(surface_view)
        self.setLayout(hlayout)

    def _show_surface(self):
        """
        render the overlays
        """

        hemisphere_list = self.surface_model.get_data()

        # clear the old surface
        if self.surf is not None:
            self.surf.remove()
            self.surf = None

        # flag
        no_hemi_flag = True
        first_hemi_flag = True

        # reset
        nn = None
        self.rgba_lut = None
        vertex_number = 0

        for hemisphere in hemisphere_list:
            if hemisphere.is_visible():

                no_hemi_flag = False

                # get geometry's information
                geo = hemisphere.surf['white']  # FIXME 'white' should be replaced with var: surf_type
                hemi_coords = geo.get_coords()
                hemi_faces = geo.get_faces().copy()  # need to be amended in situ, so need copy
                hemi_nn = geo.get_nn()

                # get the rgba_lut
                rgb_array = hemisphere.get_composite_rgb()
                hemi_vertex_number = rgb_array.shape[0]
                alpha_channel = np.ones((hemi_vertex_number, 1), dtype=np.uint8)*255
                hemi_lut = np.c_[rgb_array, alpha_channel]

                if first_hemi_flag:
                    first_hemi_flag = False
                    self.coords = hemi_coords
                    self.faces = hemi_faces
                    nn = hemi_nn
                    self.rgba_lut = hemi_lut
                else:
                    self.coords = np.r_[self.coords, hemi_coords]
                    hemi_faces += vertex_number
                    self.faces = np.r_[self.faces, hemi_faces]
                    nn = np.r_[nn, hemi_nn]
                    self.rgba_lut = np.r_[self.rgba_lut, hemi_lut]
                vertex_number += hemi_vertex_number

        if not no_hemi_flag:
            # generate the triangular mesh
            scalars = np.array(range(vertex_number))
            mesh = self.visualization.scene.mlab.pipeline.triangular_mesh_source(self.coords[:, 0],
                                                                                 self.coords[:, 1],
                                                                                 self.coords[:, 2],
                                                                                 self.faces,
                                                                                 scalars=scalars)
            mesh.data.point_data.normals = nn
            mesh.data.cell_data.normals = None

            # generate the surface
            self.surf = self.visualization.scene.mlab.pipeline.surface(mesh)
            self.surf.module_manager.scalar_lut_manager.lut.table = self.rgba_lut

        # add point picker observer
        if self.gcf_flag:
            self.gcf_flag = False
            fig = mlab.gcf()
            fig.on_mouse_pick(self._picker_callback_left)
            fig.scene.picker.pointpicker.add_observer("EndPickEvent", self._picker_callback)

    def _picker_callback(self, picker_obj, evt):

        picker_obj = tvtk.to_tvtk(picker_obj)
        tmp_pos = picker_obj.picked_positions.to_array()

        if len(tmp_pos):
            picked_pos = np.atleast_2d(tmp_pos[0])
            distance = cdist(self.coords, picked_pos)
            picked_id = np.argmin(distance, axis=0)[0]

            if self.graph is not None:  # plot line
                if self.plot_start is None:
                    self.plot_start = picked_id
                else:
                    self.path.extend(bfs(self.graph, self.plot_start, picked_id))
                    self.plot_start = picked_id
            elif self.surfRG_flag:  # get seed position
                self.seed_pos.append(picked_pos)
                self.seed_picked.seed_picked.emit()

            # plot point
            tmp_lut = self.rgba_lut.copy()
            toggle_color(tmp_lut[picked_id])
            self.surf.module_manager.scalar_lut_manager.lut.table = tmp_lut

    def _picker_callback_left(self, picker_obj):
        pass

    def _create_connections(self):
        self.surface_model.repaint_surface.connect(self._show_surface)

    # user-oriented methods
    # -----------------------------------------------------------------
    def set_model(self, surface_model):

        if isinstance(surface_model, TreeModel):
            self.surface_model = surface_model
            self._create_connections()
        else:
            raise ValueError("The model must be the instance of the TreeModel!")

    def set_graph(self, graph):
        self.graph = graph

    def get_coords(self):
        return self.coords

    def get_faces(self):
        return self.faces


if __name__ == "__main__":

    surface_view = SurfaceView()
    surface_view.setWindowTitle("surface view")
    surface_view.setWindowIcon(QIcon("/nfs/j3/userhome/chenxiayu/workingdir/icon/QAli.png"))
    surface_view.show()

    qApp.exec_()
    sys.exit()
