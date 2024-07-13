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
        Greyscale (int): Greyscale color map.
        Inverted_Greyscale (int): Inverted greyscale color map.
    """
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3

# -----------------------------------------------------------------------------
# Main Class
# -----------------------------------------------------------------------------
class VTKVisualizer:
    def __init__(self, filename="test-files/file.vtk"):
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

        self.renderer = vtk.vtkRenderer()
        self.renderer.AddActor(self.actor)

        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        
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

        # State defaults (triggers callback functions)
        self.state.mesh_representation = Representation.SurfaceWithEdges
        self.state.z_value = self._default_min

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
    def ui(self):
        if self._ui is None:
            with SinglePageWithDrawerLayout(self.server)  as layout:
                layout.title.set_text("VTK Visualization")

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
                            with vuetify3.VBtn(icon=True, click=self.ctrl.view_reset_camera):
                                vuetify3.VIcon("mdi-camera-flip")

                # Side Drawer Components
                with layout.drawer as drawer:
                    drawer.width = 325
                    vuetify3.VDivider(classes="mb-2")
                    self.drawer_card(title="Controls")
                    self.representation_dropdown()
                    self.color_map()
                    self.opacity_slider()
                    self.level_slider()

                # Content Area
                with layout.content:
                    with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                        view = trame_vtk.VtkRemoteLocalView(
                            self.render_window,
                            namespace="view",
                            mode="local",
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
            self._dataset_arrays.append(
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
            self._dataset_arrays.append(
                {
                    "text": array.GetName(),
                    "value": i,
                    "range": list(array_range),
                    "type": vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
                }
            )

        self._default_array = self._dataset_arrays[0]
        self._default_min, self._default_max = self._default_array.get("range")

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
            self.update_color_preset(mesh_color_preset)
        
        @self.state.change("mesh_color_array_idx")
        def update_mesh_color_index(mesh_color_array_idx, **kwargs):
            self.update_color_index(mesh_color_array_idx)
    
        @self.state.change("mesh_opacity")
        def update_mesh_opacity(mesh_opacity, **kwargs):
            self.update_opacity(mesh_opacity)          

        @self.state.change("z_value")
        def update_zvalue(z_value, **kwargs):
            """
            State change callback to update the 'Z-Layer' of the mesh.

            Args:
                z_value (int): The new layer to be drawn to.
            """
            self.update_zlayer(z_value)

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
        elif preset == LookupTable.Greyscale:
            lut.SetHueRange(0.0, 0.0)
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(0.0, 1.0)
        elif preset == LookupTable.Inverted_Greyscale:
            lut.SetHueRange(0.0, 0.666)
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(1.0, 0.0)
        lut.Build()
        self.ctrl.view_update()

    def update_color_index(self, index):
        array = self._dataset_arrays[index]
        self.color_by_array(array)
        self.ctrl.view_update()

    def color_by_array(self, array):
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

        # mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputConnection(threshold.GetOutputPort())

        self.actor.SetMapper(self.mapper)
        self.render_window.Render()
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
                            {"title": "Greyscale", "value": 2},
                            {"title": "Inv Greyscale", "value": 3},
                        ],
                    ),
                    hide_details=True,
                    density="compact",
                    variant="outlined",
                    classes="pt-1",
                )

    def opacity_slider(self):
        vuetify3.VSlider(
            # Opacity
            v_model=("mesh_opacity", 1),
            min=0,
            max=1,
            step=0.05,
            label="Opacity",
            classes="mt-1",
            hide_details=True,
            density="compact",
            thumb_label=True,
    )

    def level_slider(self):
        """
        The slider UI for rendering different tent levels of the object.
        """
        vuetify3.VSlider(
            v_model=("z_value", 0),
            min=int(self._default_min),
            max=int(self._default_max),
            step=1,
            label="Level",
            classes="mt-1",
            hide_details=True,
            density="compact",
            thumb_label=True,
            thumb_color="red",
            ticks="always"
        )

    def set_map_colors(self):
        """
        Configure the color mapping for a mapper using a lookup table.

        Args:
            mapper (vtk.vtkDataSetMapper): The VTK data set mapper to configure.
        """
        # Colors 
        color_lut = self.mapper.GetLookupTable()
        color_lut.SetNumberOfTableValues(256)
        color_lut.SetHueRange(0.666, 0.0)
        color_lut.SetSaturationRange(1.0, 1.0)
        color_lut.SetValueRange(1.0, 1.0)
        color_lut.Build()

        # Mesh: Color by default array
        self.mapper.SelectColorArray(self._default_array.get("text"))
        self.mapper.GetLookupTable().SetRange(self._default_min, self._default_max)
        if self._default_array.get("type") == vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS:
            self.mapper.SetScalarModeToUsePointFieldData()
        else:
            self.mapper.SetScalarModeToUseCellFieldData()
        self.mapper.SetScalarVisibility(True)
        self.mapper.SetUseLookupTableScalarRange(True)

if __name__ == "__main__":
    visualizer = VTKVisualizer()
    visualizer.server.start()
