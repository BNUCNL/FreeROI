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
        self.cbar = None
        self.rgba_lut = None
        self.gcf_flag = True
        self.not_first_flag = False

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

        # hide the old color_bar
        if self.cbar is not None:
            self.cbar.visible = False

        for hemisphere in hemisphere_list:
            if hemisphere.is_visible():
                # get geometry's information
                geo = hemisphere.surf['white'] # 'white' should be replaced with var: surf_type
                x, y, z, f, nn = geo.x, geo.y, geo.z, geo.faces, geo.nn
                self.coords = geo.coords

                # get the rgba_lut and create corresponding scalars
                rgb_array = hemisphere.get_composite_rgb()
                vertex_number = rgb_array.shape[0]
                alpha_channel = np.ones((vertex_number, 1), dtype=np.uint8)*255
                self.rgba_lut = np.c_[rgb_array, alpha_channel]
                scalars = np.array(range(vertex_number))

                # generate the triangular mesh
                mesh = self.visualization.scene.mlab.pipeline.triangular_mesh_source(x, y, z, f,
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

                self.cbar = mlab.scalarbar(self.surf)

    def _picker_callback(self, picker_obj, evt):

        picker_obj = tvtk.to_tvtk(picker_obj)
        temp_pos = picker_obj.picked_positions.to_array()

        if len(temp_pos):

            # get the nearest vertex's id
            distance = np.sum(np.abs(self.coords - temp_pos[0]), axis=1)
            picked_id = np.argmin(distance)

            # change the LUT
            temp_lut = self.rgba_lut.copy()
            self._toggle_color(temp_lut[picked_id])
            self.surf.module_manager.scalar_lut_manager.lut.table = temp_lut

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
