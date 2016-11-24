import os
import sys
import sip

from traits.api import HasTraits, Instance
from traitsui.api import View, Item
from tvtk.api import tvtk
from PyQt4.QtGui import *
from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel
from mayavi import mlab
import numpy as np

from treemodel import TreeModel


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
        self.rgba_lut = None
        self.gcf_flag = True

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

        # reset
        first_hemi_flag = True
        faces = None
        nn = None
        self.rgba_lut = None
        vertex_number = 0

        for hemisphere in hemisphere_list:
            if hemisphere.is_visible():
                # get geometry's information
                geo = hemisphere.surf['white']  # 'white' should be replaced with var: surf_type
                hemi_coords = geo.get_coords()
                hemi_faces = geo.get_faces()
                hemi_nn = geo.get_nn()

                # get the rgba_lut
                rgb_array = hemisphere.get_composite_rgb()
                hemi_vertex_number = rgb_array.shape[0]
                alpha_channel = np.ones((hemi_vertex_number, 1), dtype=np.uint8)*255
                hemi_lut = np.c_[rgb_array, alpha_channel]

                if first_hemi_flag:
                    first_hemi_flag = False
                    self.coords = hemi_coords
                    faces = hemi_faces
                    nn = hemi_nn
                    self.rgba_lut = hemi_lut
                else:
                    self.coords = np.r_[self.coords, hemi_coords]
                    hemi_faces += vertex_number
                    faces = np.r_[faces, hemi_faces]
                    nn = np.r_[nn, hemi_nn]
                    self.rgba_lut = np.r_[self.rgba_lut, hemi_lut]
                vertex_number += hemi_vertex_number

        # generate the triangular mesh
        scalars = np.array(range(vertex_number))
        mesh = self.visualization.scene.mlab.pipeline.triangular_mesh_source(self.coords[:, 0],
                                                                             self.coords[:, 1],
                                                                             self.coords[:, 2],
                                                                             faces,
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
            distance = np.sum(np.abs(self.coords - tmp_pos[0]), axis=1)
            picked_id = np.argmin(distance)

            tmp_lut = self.rgba_lut.copy()
            self._toggle_color(tmp_lut[picked_id])
            self.surf.module_manager.scalar_lut_manager.lut.table = tmp_lut

    @staticmethod
    def _toggle_color(color):
        """
        make the color look differently

        :param color: a alterable variable
            rgb or rgba
        :return:
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


if __name__ == "__main__":

    surface_view = SurfaceView()
    surface_view.setWindowTitle("surface view")
    surface_view.setWindowIcon(QIcon("/nfs/j3/userhome/chenxiayu/workingdir/icon/QAli.png"))
    surface_view.show()

    qApp.exec_()
    sys.exit()
