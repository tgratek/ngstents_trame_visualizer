import pyvista as pv
import vtk
import numpy as np
import os

from trame.app import get_server
from pyvista.trame.ui import plotter_ui, get_viewer
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import html, vuetify3
from pyvista.plotting.themes import DocumentTheme

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
class Representation:
    Points = "points"
    Wireframe = "wireframe"
    Surface = "surface"

class ColorMap:
    Rainbow = "rainbow"
    Rainbow_r = "rainbow_r"
    Viridis = "viridis"
    Plasma = "plasma"
    RedBlue = "RdBu"
    Seismic = "seismic"

# -----------------------------------------------------------------------------
# Main Application Class
# -----------------------------------------------------------------------------
class PyVistaVTKVisualizer:
    def __init__(self, filename="test-files/demo.vtk"):
        # Setup Parameters for Plotting
        pv.global_theme.load_theme(self.setup_theme())

        # Public Data Members
        self.server = get_server(client_type="vue3")
        self.filename = filename
        self._check_file_path()
        self.plotter = pv.Plotter(notebook=True)
        self.viewer = get_viewer(self.plotter, server=self.server)

        # Protected Data Members
        self._mesh = pv.read(self.filename)
        self._dataset_arrays = []
        self._baseActor = None
        self._zActor = None
        self._default_array = None
        self._default_min = None
        self._default_max = None
        self._ui = None
        # Scalar Bar Customization
        self._sargs = dict(
                        title="Tent Level",
                        fmt="%.0f",
                        font_family="arial",
                        vertical=True,
                        height=.8,
                        width=.05,
                        position_y=0.1
                    )
        # Needed for extracting state values provided by PyVista's ui_controls
        # https://github.com/pyvista/pyvista/blob/main/pyvista/trame/ui/base_viewer.py#L45
        self._plotter_id = self.plotter._id_name

        # Theme of the Vuetify Interface
        self.state.theme = "light"

        # Process Mesh and Setup UI
        self.setup_plotter()
        self.extract_data_arrays()
        self.setup_actor()
        self.setup_callbacks()

        # State defaults (triggers callback functions)
        self.state.mesh_representation = Representation.Surface
        self.state.z_value = int(self.default_min)
        self.state.opacity = 1.0  
        self.state.colormap = ColorMap.Rainbow


        # Build UI
        self.ui

    def _check_file_path(self):
        if not os.path.isfile(self.filename):
            raise FileNotFoundError(f"The file '{self.filename}' does not exist or is not a valid file path.")

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
    def baseActor(self):
        return self._baseActor

    @baseActor.setter
    def baseActor(self, value):
        self._baseActor = value
        
    @property
    def zActor(self):
        return self._zActor

    @zActor.setter
    def zActor(self, value):
        self._zActor = value
    
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
    def sargs(self):
        return self._sargs
    
    @property
    def plotter_id(self):
        return self._plotter_id
    
    @property
    def ui(self):
        if self._ui is None:
            with SinglePageWithDrawerLayout(self.server) as layout:
                layout.title.set_text("Spacetime Tents Visualization")

                # Theme of Vuetify Page (Not the Plotter)
                # Works as a callback that inverts colors of Vuetify components
                # when an action with v_model="theme" occurs.
                layout.root.theme = ("theme",)

                # Top Toolbar Components
                with layout.toolbar:                
                    with vuetify3.VContainer(fluid=True, classes="d-flex fill-height"):
                        # Visible Title as container overlays
                        vuetify3.VAppBarTitle(
                            "Spacetime Tents Visualization", 
                            classes="ml-n5 text-button font-weight-black",
                        )

                        # Right aligns the containing elements
                        with vuetify3.VToolbarItems():
                            self.light_dark_toggle()
                            # PyVista's Standard UI Controls - parameters must match that of plotter_ui
                            self.viewer.ui_controls(mode='trame', default_server_rendering=True)

                # Side Drawer Components
                with layout.drawer as drawer:
                    drawer.width = 325
                    vuetify3.VDivider(classes="mb-2")

                    with self.drawer_card(title="Controls"):
                        self.representation_dropdown()
                        self.colormap_dropdown() 
                        self.level_slider()
                        self.opacity_slider()  
                        
 
                with layout.content:
                    with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                        view = plotter_ui(self.plotter, mode='trame', default_server_rendering=True, add_menu=False)
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera

            self._ui = layout
        return self._ui

    def setup_theme(self):
        """
        Sets the default theme for the PyVista Plotter.
        """
        theme = DocumentTheme()
        theme.edge_color = "black"
        theme.split_sharp_edges = True
        theme.full_screen = True
        
        return theme

    def setup_plotter(self):
        """
        Sets the default parameters for the PyVista Plotter.
        """
        self.plotter.view_xy() # Birds-Eye View
        self.plotter.show_grid() # Show Ruler

        # Default to Light Mode
        self.plotter.set_background("snow")
        self.plotter.theme.font.color = "black"
        self.plotter.theme.font.size = 12

        # Customize XYZ Axes Widget
        self.plotter.add_axes(
            line_width=5,
            cone_radius=0.6,
            shaft_length=0.7,
            tip_length=0.3,
            ambient=0.5,
            label_size=(0.4, 0.16),
        )

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
        slice_mesh = self.mesh
        slice_mesh.set_active_scalars('tentlevel')
        slice = slice_mesh.slice_along_axis(n=1, axis='z')

        colormap = self.state.colormap

        # The tent layers to stack upon
        self.zActor = self.plotter.add_mesh(
            self.mesh.flip_z(None),
            scalars="tentlevel",
            scalar_bar_args=self.sargs,
            cmap=colormap,
            name="z-layer",
            opacity=self.state.opacity  
        )

        # Shape frame to stack tent layers on
        # baseActor is added second so that the rainbow-mapped scalar bar from zActor
        # is displayed rather than the single color mapped bar from this actor.
        # baseActor needs to know the scalars so that the bar does not momentarily disappear
        # during the times where the zActor is re-rendered from dragging the level slider.
        self.baseActor = self.plotter.add_mesh(
            slice,
            scalars="tentlevel",
            scalar_bar_args=self.sargs,
            cmap=["#93C572"], # Pistachio
            name="base-layer"
        )

        self.plotter.reset_camera()

    def update_representation(self, mode):
        """
        Update the representation mode of an actor.

        Args:
            mode (int): The representation mode (Points, Wireframe, Surface).
        """
        property = self.zActor.prop
        
        if mode == Representation.Points:
            property.style = 'points'
            property.point_size = 5
        elif mode == Representation.Wireframe:
            property.style = 'wireframe'
            property.point_size = 1
        elif mode == Representation.Surface:
            property.style = 'surface'
            property.point_size = 1
        
        self.zActor.prop = property

    def update_zlayer(self, z_value):
        """
        Updates the Z-Layer of the default actor using a new mesh threshold.

        Args:
            z_value (int): The new threshold to be used by the plotter.
            
        Example: 
            [z_value, self.default_max] - The range between the z_value and the self.default_max to be mapped to a mesh and assigned to the self.actor.
        """
        # Properties to maintain as mesh is re-rendered
        representation = self.state.mesh_representation
        edges_enabled = self.state[f'{self.plotter_id}_edge_visibility']
        colormap = self.state.colormap

        z_layer = self.mesh.threshold(value=(self.default_min, z_value), scalars='tentlevel')

        
        self.zActor = self.plotter.add_mesh(z_layer, scalars='tentlevel', scalar_bar_args=self.sargs,
                                        cmap=colormap, clim=(self.default_min, self.default_max), 
                                        opacity=self.state.opacity,  # Updated opacity value
                                        style=representation, show_edges=edges_enabled,
                                        name="z-layer")

        self.update_representation(self.state.mesh_representation)
        self.plotter.render()
    
    def update_opacity(self, opacity):
        """
        Update the opacity of the z-layer.

        Args:
            opacity (float): The opacity value from the slider.
        """
        self.zActor.prop.opacity = opacity
        

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
            self.update_representation(mesh_representation)
            self.ctrl.view_update()

        @self.state.change("colormap")
        def update_colormap(colormap, **kwargs):
            """
            State change callback to update the colormap of the z-layer.

            Args:
            colormap (str): The new colormap.
            """
            self.update_zlayer(self.state.z_value)
            self.ctrl.view_update()

        @self.state.change("z_value")
        def update_zvalue(z_value, **kwargs):
            """
            State change callback to update the 'Z-Layer' of the mesh.

            Args:
                z_value (int): The new layer to be drawn to.
            """
            self.update_zlayer(z_value)
            self.ctrl.view_update()
            
        @self.state.change("opacity")
        def update_opacity(opacity, **kwargs):
            """
            State change callback to update the opacity of the z-layer.

            Args:
                opacity (float): The new opacity value.
            """
            self.update_opacity(opacity)
            self.ctrl.view_update()

    def light_dark_toggle(self):
        """
        Define Light / Dark checkbox toggle for the GUI to switch the theme of the Vuetify page,
        inverting the colors of Vuetify components contained in the toolbar and drawer.
        """
        with vuetify3.VTooltip(location='bottom'):
            with vuetify3.Template(v_slot_activator='{ props }'):
                with html.Div(v_bind='props'):
                    vuetify3.VCheckboxBtn(
                        v_model="theme",
                        density="compact",
                        false_icon="mdi-weather-sunny",
                        false_value="light",
                        true_icon="mdi-weather-night",
                        true_value="dark",
                        classes="pa-0 ma-0 mr-2",
                        style="max-width: 30px",
                    )

            # Current theme of layout page contained in HTML element
            tooltip = "Toggle Page Theme ({{ theme === 'light' ? 'Light' : 'Dark' }})"
            html.Span(tooltip)

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
                classes="py-1 text-button font-weight-bold text-teal-darken-1",
                style="user-select: none;",
                hide_details=True,
                dense=True,
            )
            content = vuetify3.VCardText(classes="py-2")
        return content

    def representation_dropdown(self):
        """
        The dropdown UI for selecting different representations, e.g. surface, wireframe, points, etc.
        """
        vuetify3.VSelect(
            v_model=("mesh_representation", self.state.mesh_representation),
            items=(
                'representations',
                [
                    {"title": "Points", "value": Representation.Points},
                    {"title": "Wireframe", "value": Representation.Wireframe},
                    {"title": "Surface", "value": Representation.Surface},
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
            classes="mt-3",
            append_icon="mdi-menu-swap-outline",
            hide_details=True,
            dense=True,
            thumb_label=True
        )
    
    def opacity_slider(self):
        """
        The slider UI for adjusting the opacity of the z-layer.
        """
        vuetify3.VSlider(
            v_model=("opacity", 1.0),
            min=0.0,
            max=1.0,
            step=0.01,
            label="Opacity",
            classes="mt-1",
            append_icon="mdi-opacity",
            hide_details=True,
            dense=True,
            thumb_label=True
        )
    def colormap_dropdown(self):
        """
        The dropdown UI for selecting different colormaps.
        """
        vuetify3.VSelect(
            v_model=("colormap", ColorMap.Rainbow),
            items=(
                'colormaps',
                [
                    {"title": "Rainbow", "value": ColorMap.Rainbow},
                    {"title": "Inverted Rainbow", "value": ColorMap.Rainbow_r},
                    {"title": "Viridis", "value": ColorMap.Viridis},
                    {"title": "Plasma", "value": ColorMap.Plasma},
                    {"title": "Red Blue", "value": ColorMap.RedBlue},
                    {"title": "Seismic", "value": ColorMap.Seismic}
                ],
            ),
            label="Color",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
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
