import pyvista as pv
import vtk
import numpy as np

from trame.app import get_server
from pyvista.trame.ui import plotter_ui
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import vuetify3
from pyvista.plotting.themes import DarkTheme

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3

class LookupTable:
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3

# -----------------------------------------------------------------------------
# Main Application Class
# -----------------------------------------------------------------------------
class VTKVisualizer:
    def __init__(self, filename="file.vtk"):
        # Setup Parameters for Plotting
        pv.global_theme.load_theme(self.setup_theme())

        # Public Data Members
        self.server = get_server()
        self.filename = filename
        self.plotter = pv.Plotter(notebook=True)

        # Protected Data Members
        self._mesh = pv.read(self.filename)
        self._dataset_arrays = []
        self._actor = None
        self._default_array = None
        self._default_min = None
        self._default_max = None
        self._ui = None

        # Process Mesh and Setup UI
        self.setup_plotter()
        self.extract_data_arrays()
        self.setup_actor()
        self.setup_callbacks()

        self.state.mesh_representation = Representation.SurfaceWithEdges
        self.update_representation(self._actor, self.state.mesh_representation)

        # Build UI
        self.ui

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    @property
    def mesh(self):
        return self._mesh
    
    @property
    def actor(self):
        return self._actor

    @actor.setter
    def actor(self, value):
        self._actor = value
    
    @property
    def dataset_arrays(self):
        return self._dataset_arrays

    @property
    def default_min(self):
        return self._default_min
    
    @default_min.setter
    def default_min(self, value):
        self._default_min = value

    @property
    def default_max(self):
        return self._default_max
    
    @default_max.setter
    def default_max(self, value):
        self._default_max = value

    @property
    def ui(self):
        if self._ui is None:
            with SinglePageWithDrawerLayout(self.server) as layout:
                layout.title.set_text("Spacetime Tents Visualization")
                # Top Toolbar Components
                with layout.toolbar:
                    vuetify3.VSpacer()
                    vuetify3.VDivider(vertical=True)
                    self.standard_buttons()

                # Side Drawer Components
                with layout.drawer as drawer:
                    drawer.width = 325
                    vuetify3.VDivider(classes="mb-2")

                    with self.drawer_card(title="Tents"):
                        self.representation_dropdown()
                        self.test_table()
                        self.level_slider()
                
                with layout.content:
                    with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                        view = plotter_ui(self.plotter, mode='trame', default_server_rendering=False)
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera

            self._ui = layout
        return self._ui

    def setup_theme(self):
        """
        Sets the default theme for the PyVista Plotter.
        """
        theme = DarkTheme()
        theme.show_edges = True
        theme.edge_color = "black"
        theme.split_sharp_edges = True
        
        return theme

    def setup_plotter(self):
        """
        Sets the default parameters for the PyVista Plotter.
        """
        self.plotter.view_xy()
        self.plotter.add_axes()
        self.plotter.show_grid()
        

    def extract_data_arrays(self):
        """
        Reads the provided mesh VTK into an array to contain point and cell data.
        """
        point_data = self.mesh.point_data
        cell_data = self.mesh.cell_data

        for i, (name, array) in enumerate(point_data.items()):
            array_range = np.min(array), np.max(array)
            self.dataset_arrays.append(
                {
                    "text": name,
                    "value": i,
                    "range": list(array_range),
                    "type": vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
                }
            )

        for i, (name, array) in enumerate(cell_data.items()):
            array_range = np.min(array), np.max(array)
            self.dataset_arrays.append(
                {
                    "text": name,
                    "value": i,
                    "range": list(array_range),
                    "type": vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
                }
            )

        self.default_array = self.dataset_arrays[0]
        self.default_min, self.default_max = self.default_array.get("range")

    def setup_actor(self):
        """
        Initialize the actor of the mesh to visualize with default parameters.
        """
        self.actor = self.plotter.add_mesh(
            self.mesh,
            scalars=self.default_array.get("text"),
            cmap="rainbow",
        )

        # Reset the camera to show the full objec
        self.plotter.reset_camera()

    def update_representation(self, actor, mode):
        """
        Update the representation mode of an actor.

        Args:
            actor (vtk.vtkActor): The VTK actor to update.
            mode (int): The representation mode (Points, Wireframe, Surface, SurfaceWithEdges).
        """
        property = actor.prop
        
        if mode == Representation.Points:
            property.style = 'points'
            property.point_size = 5
            property.show_edges = False
        elif mode == Representation.Wireframe:
            property.style = 'wireframe'
            property.point_size = 1
            property.show_edges = False
        elif mode == Representation.Surface:
            property.style = 'surface'
            property.point_size = 1
            property.show_edges = False
        elif mode == Representation.SurfaceWithEdges:
            property.style = 'surface'
            property.point_size = 1
            property.show_edges = True
        
        actor.prop = property

    def update_zlayer(self, z_value, actor):
        # TODO
        pass

    def setup_callbacks(self):
        """
        Sets up all event listener callbacks for when state changes trigger.
        """
        @self.state.change("mesh_representation")
        def update_mesh_representation(mesh_representation, **kwargs):
            """
            State change callback to update the representation mode of the mesh.

            Args:
                mesh_representation (int): The new representation mode.
            """
            self.update_representation(self.actor, mesh_representation)
            self.ctrl.view_update()

        @self.state.change("z_value")
        def update_zvalue(z_value, **kwargs):
            # TODO
            pass

    def standard_buttons(self):
        """
        Define standard buttons for the GUI, including a checkbox for dark mode and a button to reset the camera.
        """
        # Reset Camera
        with vuetify3.VBtn(icon=True, click=self.ctrl.view_reset_camera):
            vuetify3.VIcon("mdi-crop-free")
        
        # Light and Dark Theme
        vuetify3.VCheckbox(
            # Posssibly because vuetify.theme is NOT A THING, the PyVista toolbar appears in place of no theme
            v_model="vuetify.theme.dark", # ??? Causes the PyVista toolbar to appear but overrides Topbar ???
            on_icon="mdi-lightbulb-off-outline",
            off_icon="mdi-lightbulb-outline",
            classes="mx-1",
            hide_details=True,
            dense=True,
        )

    def drawer_card(self, title):
        """
        Create a UI card component for organizing GUI elements.

        Args:
            title (str): The title of the card.

        Returns:
            vuetify.VCardText: The content area of the card.
        """
        with vuetify3.VCard():
            vuetify3.VCardTitle(
                title,
                classes="grey lighten-1 py-1 grey--text text--darken-3",
                style="user-select: none; cursor: pointer",
                hide_details=True,
                dense=True,
            )
            content = vuetify3.VCardText(classes="py-2")
        return content

    def representation_dropdown(self):
        """
        The dropdown UI for selecting different representations, e.g. including edges, wireframe, points, etc.
        """
        vuetify3.VSelect(
            v_model=("mesh_representation", self.state.mesh_representation),
            items=(
                'representations',
                [
                    {"title": "Points", "value": Representation.Points},
                    {"title": "Wireframe", "value": Representation.Wireframe},
                    {"title": "Surface", "value": Representation.Surface},
                    {"title": "SurfaceWithEdges", "value": Representation.SurfaceWithEdges},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )

    def level_slider(self):
        """
        The slider UI for rendering different tent levels of the object.
        """
        vuetify3.VSlider(
            v_model=("z_value", 0),
            min=int(self.default_min),
            max=int(self.default_max),
            step=1,
            label="Level",
            classes="mt-1",
            hide_details=True,
            dense=True,
            thumb_label=True
        )

    def test_table(self):
        with vuetify3.VRow(classes="pt-2", dense=True):
            with vuetify3.VCol(cols="6"):
                vuetify3.VCardTitle(
                    "Default",
                    classes="grey lighten-1 py-1 grey--text text--darken-3",
                    style="user-select: none; cursor: pointer",
                    hide_details=True,
                    dense=True,
                )
            with vuetify3.VCol(cols="6"):
                vuetify3.VCardTitle(
                    "Default",
                    classes="grey lighten-1 py-1 grey--text text--darken-3",
                    style="user-select: none; cursor: pointer",
                    hide_details=True,
                    dense=True,
                )
