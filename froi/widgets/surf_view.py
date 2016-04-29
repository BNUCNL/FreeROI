import os
import sys
import sip

from traits.api import HasTraits, Instance
from traitsui.api import View, Item
from PyQt4 import QtGui
from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel
from mayavi import mlab

from treemodel import TreeModel

# First, and before importing any Enthought packages, set the ETS_TOOLKIT
# environment variable to qt4, to tell Traits that we will use Qt.
os.environ["ETS_TOOLKIT"] = 'qt4'

# By default, the PySide binding will be used. If you want the PyQt bindings
# to be used, you need to set the QT_API environment variable to 'pyqt'
os.environ["QT_API"] = "pyqt"

# Also, as Traits runs with PyQt and PySide, if you use PyQt, you must make sure that you swith
# its binding in a mode that is compatible with PySide (internal string representation mode),
# before you import any PyQt code:
sip.setapi("QString", 2)


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


class SurfaceView(QtGui.QWidget):

    def __init__(self, parent=None):
        super(SurfaceView, self).__init__(parent)

        # initialize GUI
        # self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Expanding)
        self.resize(400, 450)

        # get mayavi scene
        # The edit_traits call will generate the widget to embed.
        self.visualization = Visualization()
        self.ui = self.visualization.edit_traits(parent=self, kind="subpanel").control
        self.ui.setParent(self)
        # get rid of the toolbar
        figure = mlab.gcf()
        _toggle_toolbar(figure, False)

        # Initialize some fields
        self.surface_model = None
        self.old_surf = []
        self.old_cbar = []
        self.not_first_flag = False
        self.cbar = None

    @staticmethod
    def _get_start_render_index(hemisphere):
        """
        If an overlay's opacity is 1.0(i.e. completely opaque) and need to cover a whole
        hemisphere, other overlays that below it are no need to be rendered.

        :param hemisphere: Hemisphere
            the instance of the class Hemisphere
        :return: int
            The index that the render starts at.
        """

        for index in hemisphere.overlay_idx[-1::-1]:
            scalar = hemisphere.overlay_list[index]
            if "label" not in scalar.get_name() and scalar.get_alpha() == 1. and scalar.is_visible():
                return hemisphere.overlay_idx.index(index)

        # -1 means that the render will start with the geometry surface.
        return -1

    def _show_surface(self):
        """
        render the overlays
        """

        hemisphere_list = self.surface_model.get_data()

        # clear the old surfaces
        for surf in self.old_surf:
            surf.remove()
            self.old_surf.remove(surf)

        # hide the old color_bars
        for cbar in self.old_cbar:
            cbar.visible = False
            self.old_cbar.remove(cbar)

        for hemisphere in hemisphere_list:
            if hemisphere.is_visible():
                # get geometry's information
                geo = hemisphere.surf
                x, y, z, f, nn = geo.x, geo.y, geo.z, geo.faces, geo.nn

                mesh = self.visualization.scene.mlab.pipeline.triangular_mesh_source(x, y, z, f)
                mesh.data.point_data.normals = nn
                mesh.data.cell_data.normals = None

                start_render_index = self._get_start_render_index(hemisphere)
                if start_render_index == -1:
                    geo_surf = self.visualization.scene.mlab.pipeline.surface(mesh, color=(.5, .5, .5))
                    self.old_surf.append(geo_surf)
                    start_render_index += 1

                for index in hemisphere.overlay_idx[start_render_index:]:
                    scalar = hemisphere.overlay_list[index]
                    if scalar.is_visible():
                        mesh.mlab_source.scalars = scalar.get_data()
                        surf = self.visualization.scene.mlab.pipeline.surface(mesh, vmin=scalar.get_min(),
                                                                              vmax=scalar.get_max(),
                                                                              colormap=scalar.get_colormap(),
                                                                              opacity=scalar.get_alpha(),
                                                                              transparent=True)
                        self.old_surf.append(surf)

                        if scalar.is_colorbar():
                            if self.not_first_flag:
                                '''
                                only show the topside overlay's colorbar
                                '''
                                self.cbar.visible = False
                                self.old_cbar.remove(self.cbar)
                            self.cbar = mlab.scalarbar(surf)
                            self.old_cbar.append(self.cbar)
                            self.not_first_flag = True
                self.not_first_flag = False

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
    surface_view.setWindowIcon(QtGui.QIcon("/nfs/j3/userhome/chenxiayu/workingdir/icon/QAli.png"))
    surface_view.show()

    QtGui.qApp.exec_()
    sys.exit()
