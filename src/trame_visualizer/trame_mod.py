import vtk
import os

from trame.app import get_server
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import html, vuetify3, vtk as trame_vtk
from trame_vtk.modules.vtk.serializers import configure_serializer

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa

configure_serializer(encode_lut=True, skip_light=False)
# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
# RGB Colors
COLOR_BLACK = (0.0, 0.0, 0.0)
COLOR_WHITE = (1.0, 1.0, 1.0)
COLOR_LIGHT = (0.9, 0.9, 0.9)
COLOR_DARK = (0.1, 0.1, 0.1)

class Representation:
    """
    Constants for different types of representations of VTK actors.

    Attributes:
        Points (int): Representation as points.
        Wireframe (int): Representation as wireframe.
        Surface (int): Representation as a surface.
        SurfaceWithEdges (int): Representation as a surface with edges.
    """
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3

class LookupTable:
    """
    Constants for different types of lookup tables for color maps.

    Attributes:
        Rainbow (int): Rainbow color map.
        Inverted_Rainbow (int): Inverted rainbow color map.
        Viridis (int): Viridis color map.
        Inferno (int): Inferno color map.
    """
    Rainbow = 0
    Inverted_Rainbow = 1
    Viridis = 2
    Inferno = 3

# -----------------------------------------------------------------------------
# Main Class
# -----------------------------------------------------------------------------
class TrameVTKVisualizer:
    """
    The base class to be used to read in a `.vtk` file and visualize the mesh.
    Includes a base-layer (slice of the z-axis) as well as a UI to navigate between
    different z-axis layers. The UI provides options for different representations and
    color maps.
    """
    def __init__(self, filename="test-files/demo.vtk"):
        # Public Data Members
        self.server = get_server(client_type="vue3")
        self.filename = filename
        self._check_file_path()

        # VTK components
        self.reader = vtk.vtkUnstructuredGridReader()
        self.reader.SetFileName(self.filename)
        self.reader.Update()

        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputConnection(self.reader.GetOutputPort())

        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.base_layer = self.setup_base_actor()

        self.renderer = vtk.vtkRenderer()
        self.renderer.AddActor(self.actor)
        self.renderer.AddActor(self.base_layer)

        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window.OffScreenRenderingOn() # Disables the OpenGL window from opening.

        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        
        self.renderer.ResetCamera()
        
        # Protected Data Members
        self._dataset_arrays = []
        self._default_array = None
        self._default_min = None
        self._default_max = None
        self._ui = None

        # Theme of the Vuetify Interface
        self.state.theme = "light"

        # Process Mesh and Setup UI
        self.extract_data_arrays()
        self.set_map_colors()
        self.setup_callbacks()
        
        # Axes & Scalar Bar
        self.scalar_bar = self.setup_scalar_bar(self.default_array)
        self.renderer.AddActor(self.scalar_bar)
        self.axes = self.setup_axes_actor()
        self.renderer.AddActor(self.axes)

        # State defaults (triggers callback functions)
        self.state.mesh_representation = Representation.SurfaceWithEdges
        self.state.z_value = self.default_min
        self.state.cube_axes_visibility = True
        self.state.theme = "light"

        # Build UI
        self.ui

    def _check_file_path(self):
        """
        Checks the file path is correct for the file to be read in.

        Raises:
            FileNotFoundError: File path is invalid.
        """
        if not os.path.isfile(self.filename):
            raise FileNotFoundError(f"The file '{self.filename}' does not exist or is not a valid file path.")

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller
    
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
            with SinglePageWithDrawerLayout(self.server)  as layout:
                layout.title.set_text("VTK Visualization")
                layout.root.theme = ("theme",)

                # Top Toolbar Components
                with layout.toolbar:                
                    with vuetify3.VContainer(fluid=True, classes="d-flex fill-height"):
                        vuetify3.VAppBarTitle(
                            "VTK Visualization", 
                            classes="ml-n5 text-button font-weight-black",
                        )

                        # Right aligns the containing elements
                        with vuetify3.VToolbarItems():
                            self.light_dark_toggle()
                            self.standard_buttons()

                # Side Drawer Components
                with layout.drawer as drawer:
                    drawer.width = 325
                    self.drawer_card(title="Controls")
                    self.representation_dropdown()
                    self.color_map()
                    with vuetify3.VContainer(fluid=True, classes="pa-4"):
                        self.opacity_slider()
                        self.level_slider()

                # Content Area
                with layout.content:
                    with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                        view = trame_vtk.VtkRemoteLocalView(
                            self.render_window,
                            namespace="view",
                            mode="remote",
                            interactive_ratio=1,
                            interactive_quality=100
                        )
                        self.ctrl.view_update = view.update
                        self.ctrl.view_reset_camera = view.reset_camera

            self._ui = layout
        return self._ui

    def extract_data_arrays(self):
        """
        Reads the provided mesh VTK into an array to contain point and cell data.
        """
        point_data = self.reader.GetOutput().GetPointData()
        cell_data = self.reader.GetOutput().GetCellData()

        for i in range(point_data.GetNumberOfArrays()):
            array = point_data.GetArray(i)
            array_range = array.GetRange()
            self.dataset_arrays.append(
                {
                    "text": array.GetName(),
                    "value": i,
                    "range": list(array_range),
                    "type": vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
                }
            )

        for i in range(cell_data.GetNumberOfArrays()):
            array = cell_data.GetArray(i)
            array_range = array.GetRange()
            self.dataset_arrays.append(
                {
                    "text": array.GetName(),
                    "value": i,
                    "range": list(array_range),
                    "type": vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
                }
            )

        self.default_array = self.dataset_arrays[0]
        self.default_min, self.default_max = self.default_array.get("range")

    def setup_base_actor(self):
        """
        Function to return a vtkActor that is mapped at the base z-layer of the mesh.

        Returns:
            vtkActor: The base layer actor from the "slice" of the bottom z-axis.
        """
        bounds = self.reader.GetOutput().GetBounds()
        
        clip_plane = vtk.vtkPlane()
        clip_plane.SetOrigin(bounds[0] + (bounds[1] - bounds[0]) / 2,
                             bounds[2] + (bounds[3] - bounds[2]) / 2,
                             0.0001) # Minumum Z-Axis (bounds[5] - Kind of in the way)
        clip_plane.SetNormal(0, 0, 1)
        
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(clip_plane)
        cutter.SetInputData(self.reader.GetOutput())
        cutter.Update()
        
        cutter_mapper = vtk.vtkDataSetMapper()
        cutter_mapper.SetInputConnection(cutter.GetOutputPort())
        base_layer = vtk.vtkActor()
        base_layer.SetMapper(cutter_mapper)
        base_layer.GetProperty().SetColor(0.15, 0.9, 0.15)
        base_layer.GetProperty().SetOpacity(0.7)
        base_layer.GetProperty().SetEdgeVisibility(1)
        base_layer.GetProperty().SetEdgeOpacity(0.7)
        return base_layer

    def setup_axes_actor(self):
        """
        Creates the axes actor for the axes.

        Returns:
            vtkCubeAxesActor(): The actor to be added to the renderer.
        """
        axes = vtk.vtkCubeAxesActor()
        axes.DrawXInnerGridlinesOn() # Unsure on this as they seem to have height
        # axes.DrawXGridpolysOn() # Adds a poly section
        axes.DrawYInnerGridlinesOn() # Unsure on this as they seem to have height
        axes.SetBounds(self.actor.GetBounds())
        axes.SetCamera(self.renderer.GetActiveCamera())
        axes.SetXLabelFormat("%.1e")
        axes.SetYLabelFormat("%.1e")
        axes.SetZLabelFormat("%.1e")
        axes.SetFlyModeToOuterEdges()
        return axes

    def setup_scalar_bar(self, array):
        """
        Creates the scalar bar actor for the plot.

        Args:
            array (dataset_arrays): Single array from the dataset_arrays.

        Returns:
            vtkScalarBarActor(): Returns the scalar bar actor to be rendered.
        """
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(self.mapper.GetLookupTable())
        scalar_bar.SetWidth(0.1)
        scalar_bar.SetLabelFormat("%.1f")
        scalar_bar.SetPosition(0.88, 0.1)
        return scalar_bar

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
        
        @self.state.change("mesh_color_preset")
        def update_mesh_color_preset(mesh_color_preset, **kwargs):
            """
            State change callback to update the color map preset.

            Args:
                mesh_color_preset (int): The new color map.
            """
            self.update_color_preset(mesh_color_preset)
        
        @self.state.change("mesh_color_array_idx")
        def update_mesh_color_index(mesh_color_array_idx, **kwargs):
            """
            State change callback to change the array used for input.

            Args:
                mesh_color_array_idx (int): The index of the new array.
            """
            self.update_color_index(mesh_color_array_idx)
    
        @self.state.change("mesh_opacity")
        def update_mesh_opacity(mesh_opacity, **kwargs):
            """
            State change callback to update the `self.actor` mesh's opacity.

            Args:
                mesh_opacity (float): The new opacity for the mesh.
            """
            self.update_opacity(mesh_opacity)          

        @self.state.change("z_value")
        def update_zvalue(z_value, **kwargs):
            """
            State change callback to update the 'Z-Layer' of the mesh.

            Args:
                z_value (int): The new layer to be drawn to.
            """
            self.update_zlayer(z_value)
        
        @self.state.change("cube_axes_visibility")
        def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
            """
            State change callback to update the axes visibility.

            Args:
                cube_axes_visibility (bool): True: visibile, False: hidden.
            """
            self.axes.SetVisibility(cube_axes_visibility)
            self.ctrl.view_update()
        
        @self.state.change("theme")
        def update_theme(theme, **kwargs):
            """
            Adjusts the color scheme of the renderer background, fonts, and the axes.

            Args:
                theme ("light"/"dark"): Light or Dark theme from toggling associated button. 
            """
            
            def set_colors(background_color, axis_color, gridline_color, text_color):
                """
                Helper function to limit lines of code.

                Args:
                    background_color (tuple[float, float, float]): RGB values as a tuple.
                    axis_color (tuple[float, float, float]): RGB values as a tuple.
                    gridline_color (tuple[float, float, float]): RGB values as a tuple.
                    text_color (tuple[float, float, float]): RGB values as a tuple.
                """
                # Background Color
                self.renderer.SetBackground(*background_color)
                # Axes Lines Color
                self.axes.GetXAxesLinesProperty().SetColor(*axis_color)
                self.axes.GetYAxesLinesProperty().SetColor(*axis_color)
                self.axes.GetZAxesLinesProperty().SetColor(*axis_color)
                # Axes Inner Lines Color
                self.axes.GetXAxesInnerGridlinesProperty().SetColor(*gridline_color)
                self.axes.GetYAxesInnerGridlinesProperty().SetColor(*gridline_color)
                self.axes.GetZAxesInnerGridlinesProperty().SetColor(*gridline_color)
                # Axes Title Color
                self.axes.GetTitleTextProperty(0).SetColor(*text_color)
                self.axes.GetLabelTextProperty(0).SetColor(*text_color)
                self.axes.GetLabelTextProperty(1).SetColor(*text_color)
                self.axes.GetTitleTextProperty(1).SetColor(*text_color)
                self.axes.GetLabelTextProperty(2).SetColor(*text_color)
                self.axes.GetTitleTextProperty(2).SetColor(*text_color)
                # Scalar Bar Color
                self.scalar_bar.GetTitleTextProperty().SetColor(*text_color)
                self.scalar_bar.GetLabelTextProperty().SetColor(*text_color)
            
            if theme == "light":
                set_colors(COLOR_LIGHT, COLOR_BLACK, COLOR_BLACK, COLOR_BLACK)
                
            else:
                set_colors(COLOR_DARK, COLOR_WHITE, COLOR_WHITE, COLOR_WHITE)
                
            self.ctrl.view_update()

    def update_representation(self, mode):
        """
        Update the representation mode of an actor.

        Args:
            mode (int): The representation mode (Points, Wireframe, Surface, SurfaceWithEdges).
        """
        property = self.actor.GetProperty()
        if mode == Representation.Points:
            property.SetRepresentationToPoints()
            property.SetPointSize(5)
            property.EdgeVisibilityOff()
        elif mode == Representation.Wireframe:
            property.SetRepresentationToWireframe()
            property.SetPointSize(1)
            property.EdgeVisibilityOff()
        elif mode == Representation.Surface:
            property.SetRepresentationToSurface()
            property.SetPointSize(1)
            property.EdgeVisibilityOff()
        elif mode == Representation.SurfaceWithEdges:
            property.SetRepresentationToSurface()
            property.SetPointSize(1)
            property.EdgeVisibilityOn()
            
        self.ctrl.view_update()

    def update_color_preset(self, preset):
        """
        Apply a color lookup table preset to an actor.

        Args:
            preset (int): The color preset to apply (Rainbow, Inverted Rainbow, ect..)
        """
        lut = self.actor.GetMapper().GetLookupTable()
        if preset == LookupTable.Rainbow:
            lut.SetHueRange(0.666, 0.0)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
        elif preset == LookupTable.Inverted_Rainbow:
            lut.SetHueRange(0.0, 0.666)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
        elif preset == LookupTable.Viridis: # WIP
            lut.SetHueRange(0.85, 0.12)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(0.25, 1.0)
        elif preset == LookupTable.Inferno: # WIP
            lut.SetHueRange(0.00, 0.2)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(0.2, 1.0)
        lut.Build()
        self.ctrl.view_update()

    def update_color_index(self, index):
        """
        Function to use the index argument to switch to a different array from the
        `self._dataset_arrays`.

        Args:
            index (int): Retrieved from the the callback.
        """
        array = self.dataset_arrays[index]
        self.color_by_array(array)
        self.scalar_bar.SetTitle(array['text']) # Dynamically update the scalar bar title.
        self.ctrl.view_update()

    def color_by_array(self, array):
        """
        Apply color mapping to an actor based on a data array.

        Args:
            array (dict): The data array to use for color mapping.
        """
        _min, _max = array.get("range")
        mapper = self.actor.GetMapper()
        mapper.SelectColorArray(array.get("text"))
        mapper.GetLookupTable().SetRange(_min, _max)
        if array.get("type") == vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS:
            mapper.SetScalarModeToUsePointFieldData()
        else:
            mapper.SetScalarModeToUseCellFieldData()
        mapper.SetScalarVisibility(True)
        mapper.SetUseLookupTableScalarRange(True)
        self.mapper = mapper

    def update_opacity(self, opacity):
        """
        Sets the default actor's `self.actor` opacity from the opacity argument.

        Args:
            opacity (float): The desired opacity, from a callback.
        """
        self.actor.GetProperty().SetOpacity(opacity)
        self.ctrl.view_update()

    def update_zlayer(self, z_value):
        """
        Updates the Z-Layer of the default actor using a new mesh threshold.

        Args:
            z_value (int): The new threshold to be used by the plotter.
            
        Example: 
            [z_value, self.default_max] - The range between the z_value and the self.default_max to be mapped to a mesh and assigned to the self.actor.
        """
        threshold = vtk.vtkThreshold()
        threshold.SetInputConnection(self.reader.GetOutputPort())
        threshold.SetInputArrayToProcess(0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, 'tentlevel')
        threshold.SetInputArrayToProcess(1, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, 'tentnumber')
        threshold.SetLowerThreshold(self._default_min)
        threshold.SetUpperThreshold(z_value)
        threshold.Update()

        self.mapper.SetInputConnection(threshold.GetOutputPort())

        self.actor.SetMapper(self.mapper)
        self.render_window.Render()
        self.ctrl.view_update()

    def drawer_card(self, title):
        """
        Create a UI card component for organizing GUI elements.

        Args:
            title (str): The title of the card.

        Returns:
            vuetify3.VCardText: The content area of the card.
        """
        with vuetify3.VCard():
            vuetify3.VCardTitle(
                title,
                classes="py-1 text-button font-weight-bold text-teal-darken-1",
                style="user-select: none;",
                hide_details=True,
                density="compact",
            )
            content = vuetify3.VCardText(classes="py-2")
        return content

    def representation_dropdown(self):
        """
        The dropdown UI for selecting different representations, e.g. surface, wireframe, points, etc.
        """
        vuetify3.VSelect(
            v_model=("mesh_representation", Representation.SurfaceWithEdges),
            items=( 
                "representations",
                [
                {"title": "Points", "value": 0},
                {"title": "Wireframe", "value": 1},
                {"title": "Surface", "value": 2},
                {"title": "SurfaceWithEdges", "value": 3},
               ],
            ),
            label="Representation",
            hide_details=True,
            classes="pt-1",
        )

    def color_map(self):
        """
        UI section for the color map. Controlled from the `"mesh_color_array_idx"`,
        which differentiates between the two arrays. For Vuetify3, had to 'hard' code
        the `"array_list"` for the information to be visable.
        Also houses the UI for selecting the desired colormap.
        """
        with vuetify3.VRow(classes="pt-2", dense=True):
            with vuetify3.VCol(cols="6"):
                vuetify3.VSelect(
                    # Color By
                    label="Color by",
                    v_model=("mesh_color_array_idx", 0),
                    items=(
                        "array_list",
                        [
                            { "title": "tentlevel", "value": 0 },
                            { "title": "tentnumber", "value": 1},
                        ]),
                    hide_details=True,
                    density="compact",
                    variant="outlined",
                    classes="pt-1",
                )
            with vuetify3.VCol(cols="6"):
                vuetify3.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("mesh_color_preset", LookupTable.Rainbow),
                    items=(
                        "colormaps",
                        [
                            {"title": "Rainbow", "value": 0},
                            {"title": "Inv Rainbow", "value": 1},
                            {"title": "Viridis", "value": 2},
                            {"title": "Inferno", "value": 3},
                        ],
                    ),
                    hide_details=True,
                    density="compact",
                    variant="outlined",
                    classes="pt-1",
                )

    def opacity_slider(self):
        """
        Vuetify slider for controlling the opacity. Uses `"mesh_opacity"` for callbacks.
        """
        vuetify3.VSlider(
            v_model=("mesh_opacity", 1),
            min=0,
            max=1,
            step=0.05,
            label="Opacity",
            classes="mt-1",
            prepend_icon="mdi-opacity",
            hide_details=True,
            max_width=290,
            density="compact",
            thumb_label=True,
        )
        
    def level_slider(self):
        """
        Vuetify slider for rendering different tent levels of the object. Uses `"z_value"`
        for callbacks.
        """
        vuetify3.VSlider(
            v_model=("z_value", 0),
            min=int(self._default_min),
            max=int(self._default_max),
            step=1,
            label="Level",
            classes="mt-1",
            prepend_icon="mdi-arrow-up-down-bold",
            hide_details=True,
            max_width=290,
            density="compact",
            thumb_label=True,
        )

    def set_map_colors(self):
        """
        Configure the color mapping for a mapper using a lookup table.
        """
        # Colors 
        color_lut = self.mapper.GetLookupTable()
        color_lut.SetNumberOfTableValues(256)
        color_lut.SetHueRange(0.666, 0.0)
        color_lut.SetSaturationRange(1.0, 1.0)
        color_lut.SetValueRange(1.0, 1.0)
        color_lut.Build()

        # Mesh: Color by default array
        self.mapper.SelectColorArray(self.default_array.get("text"))
        self.mapper.GetLookupTable().SetRange(self.default_min, self.default_max)
        if self.default_array.get("type") == vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS:
            self.mapper.SetScalarModeToUsePointFieldData()
        else:
            self.mapper.SetScalarModeToUseCellFieldData()
        self.mapper.SetScalarVisibility(True)
        self.mapper.SetUseLookupTableScalarRange(True)

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

    def standard_buttons(self):
        """
        Define standard buttons for the GUI, including a checkbox for axes, view type, and a button to reset the camera.
        """
        with vuetify3.VTooltip(location='bottom'):
            with vuetify3.Template(v_slot_activator='{ props }'):
                with html.Div(v_bind='props'):
                    vuetify3.VCheckboxBtn(
                        v_model=("cube_axes_visibility", True),
                        true_icon="mdi-cube-outline",
                        false_icon="mdi-cube-off-outline",
                        classes="mx-1",
                        hide_details=True,
                        density="compact"
                    )
                    
            tooltip = "Toggle axes ruler ({{ cube_axes_visibility ? 'On' : 'Off' }})."
            html.Span(tooltip) 
                   
        with vuetify3.VTooltip(location='bottom'):
            with vuetify3.Template(v_slot_activator='{ props }'):
                with html.Div(v_bind='props'):
                    vuetify3.VCheckboxBtn(
                        v_model=("viewMode", "local"),
                        true_icon="mdi-lan-disconnect",
                        true_value="local",
                        false_icon="mdi-lan-connect",
                        false_value="remote",
                        classes="mx-1",
                        hide_details=True,
                        density="compact",
                    )
                    
            tooltip = "Toggle ({{ viewMode === 'local' ? 'Local' : 'Remote' }}) View."
            html.Span(tooltip)
                    
        with vuetify3.VBtn(icon=True, click=self.ctrl.view_reset_camera):
            with vuetify3.VTooltip(location='bottom'):
                with vuetify3.Template(v_slot_activator='{ props }'):
                    with html.Div(v_bind='props'):
                        vuetify3.VIcon("mdi-camera-flip")
                
                tooltip = "Reset Camera"
                html.Span(tooltip)

if __name__ == "__main__":
    visualizer = TrameVTKVisualizer()
    visualizer.server.start()
