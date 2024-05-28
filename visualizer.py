"""
This script sets up a VTK pipeline for visualizing data from a VTK file, using Trame for the UI. 

The VTK pipeline involves:
- Reading an unstructured grid from a VTK file using vtkUnstructuredGridReader.
- Extracting and mapping data arrays from the dataset for visualization.
- Creating and configuring VTK actors and mappers for rendering.
- Setting up callbacks for interactive UI elements to control the visualization.

Trame is used to create a web-based interface for interacting with the VTK visualization.
"""

import vtk as v
from trame.app import get_server
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import vtk, vuetify, trame
from trame_vtk.modules.vtk.serializers import configure_serializer

configure_serializer(encode_lut=True, skip_light=True)
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
# VTK pipeline
# -----------------------------------------------------------------------------
"""
    The VTK Pipeline is for setting up the rendering window and its associated components.
    Notables:
        vtkUnstructuredGridReader() - Sets up the import of the vtk file data.
            - Note: Due to the vtk format from `ngstents` the file is an unstructured grid.
        vtkDataObject - Used for the vtk file to get the data and stored in vtk to be visualized. (?)
        vtkSetDataMapp() - Used to setup the mesh based on the input.
        vtkActor() - Adds the item to the renderer. 
"""
# Create the renderer, render window, and interactor
renderer = v.vtkRenderer()
renderWindow = v.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = v.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

# Read the VTK file
reader = v.vtkUnstructuredGridReader()
reader.SetFileName("file.vtk")
reader.Update()

# Get the output dataset - Used in zlayer ** To Do: Get from below dict array **
dataset = reader.GetOutput()

# Extract data arrays from 'reader'
dataset_arrays = []
fields = [
    (reader.GetOutput().GetPointData(), v.vtkDataObject.FIELD_ASSOCIATION_POINTS),
    (reader.GetOutput().GetCellData(), v.vtkDataObject.FIELD_ASSOCIATION_CELLS),
]
for field in fields:
    field_arrays, association = field
    for i in range(field_arrays.GetNumberOfArrays()):
        array = field_arrays.GetArray(i)
        array_range = array.GetRange()
        dataset_arrays.append(
            {
                "text": array.GetName(),
                "value": i,
                "range": list(array_range),
                "type": association,
            }
        )
default_array = dataset_arrays[0]
default_min, default_max = default_array.get("range")

"""
    Currently setting up two different maps and actors to be used for visualization.
"""
# Default - The normal layer that is mapped as before.
dMapper = v.vtkDataSetMapper()
dMapper.SetInputConnection(reader.GetOutputPort())
dActor = v.vtkActor()
dActor.SetMapper(dMapper)
renderer.AddActor(dActor)

# Z-Layer - Used for rendering the different "levels" of the file.
zLayer = v.vtkmThreshold()
zLayer.SetInputConnection(reader.GetOutputPort())
zMapper = v.vtkDataSetMapper()
zMapper.SetInputConnection(zLayer.GetOutputPort())
zActor = v.vtkActor()
zActor.SetMapper(zMapper)
renderer.AddActor(zActor)

ZValue = 0.5 * (default_max + default_min)
zLayer.SetInputArrayToProcess(0, 0, 0, v.vtkDataObject.FIELD_ASSOCIATION_POINTS, 'tentlevel')
zLayer.SetInputArrayToProcess(1, 0, 0, v.vtkDataObject.FIELD_ASSOCIATION_POINTS_THEN_CELLS,'tentnumber')
zLayer.SetLowerThreshold(default_min)
zLayer.SetUpperThreshold(default_max)
zLayer.Update()


def representation(actor):
    """
    Configure the color mapping for a mapper using a lookup table.

    Args:
        mapper (vtk.vtkDataSetMapper): The VTK data set mapper to configure.
    """
    actor.GetProperty().SetRepresentationToSurface()
    actor.GetProperty().SetPointSize(1)
    actor.GetProperty().EdgeVisibilityOn()


def set_map_colors(mapper):
    """
    Configure the color mapping for a mapper using a lookup table.

    Args:
        mapper (vtk.vtkDataSetMapper): The VTK data set mapper to configure.
    """
    # Colors 
    color_lut = mapper.GetLookupTable()
    color_lut.SetNumberOfTableValues(256)
    color_lut.SetHueRange(0.666, 0.0)
    color_lut.SetSaturationRange(1.0, 1.0)
    color_lut.SetValueRange(1.0, 1.0)
    color_lut.Build()

    # Mesh: Color by default array
    mapper.SelectColorArray(default_array.get("text"))
    mapper.GetLookupTable().SetRange(default_min, default_max)
    if default_array.get("type") == v.vtkDataObject.FIELD_ASSOCIATION_POINTS:
        mapper.SetScalarModeToUsePointFieldData()
    else:
        mapper.SetScalarModeToUseCellFieldData()
    mapper.SetScalarVisibility(True)
    mapper.SetUseLookupTableScalarRange(True)

representation(dActor)
set_map_colors(dMapper)

representation(zActor)
set_map_colors(zMapper)

# Create an orientation marker
axes = v.vtkAxesActor()
orientationMarker = v.vtkOrientationMarkerWidget()
orientationMarker.SetOrientationMarker(axes)
orientationMarker.SetInteractor(renderWindowInteractor)
orientationMarker.SetViewport(0.0, 0.0, 0.2, 0.2)
orientationMarker.SetEnabled(1)
orientationMarker.InteractiveOn()

renderer.ResetCamera()

# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

# Sets defaults:
state.setdefault("active_ui", "default")
state.setdefault("zlayer_opacity", 0.0)

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------
# Selection Change
def actives_change(ids):
    """
    Callback to handle changes in the active UI elements.

    Args:
        ids (list): List of active UI element IDs.
    """
    _id = ids[0]
    if _id == "1":  # Mesh
        state.active_ui = "default"
        zActor.VisibilityOff()
        dActor.VisibilityOn()
    elif _id == "2":  # Z-Layer
        state.active_ui = "zlayer"
        zActor.VisibilityOn()
        dActor.VisibilityOff()
    else:
        state.active_ui = "nothing"
        dActor.VisibilityOff()
        zActor.VisibilityOff()

# Visibility Change
def visibility_change(event):
    """
    Callback to handle changes in visibility of actors.

    Args:
        event (dict): Event data containing the ID and visibility state.
    """
    _id = event["id"]
    _visibility = event["visible"]

    if _id == "1":  # Default
        dActor.SetVisibility(_visibility)
    elif _id == "2":  # Z-Layer
        zActor.SetVisibility(_visibility)
    ctrl.view_update()

# Representation Callbacks
def update_representation(actor, mode):
    """
    Update the representation mode of an actor.

    Args:
        actor (vtk.vtkActor): The VTK actor to update.
        mode (int): The representation mode (Points, Wireframe, Surface, SurfaceWithEdges).
    """
    property = actor.GetProperty()
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

@state.change("mesh_representation")
def update_mesh_representation(mesh_representation, **kwargs):
    """
    State change callback to update the representation mode of the mesh.

    Args:
        mesh_representation (int): The new representation mode.
    """
    update_representation(dActor, mesh_representation)
    ctrl.view_update()

@state.change("zlayer_representation")
def update_zlayer_representation(zlayer_representation, **kwargs):
    """
    State change callback to update the representation mode of the Z-layer.

    Args:
        zlayer_representation (int): The new representation mode.
    """
    update_representation(zActor, zlayer_representation)
    ctrl.view_update()


# Color By Callbacks
def color_by_array(actor, array):
    """
    Apply color mapping to an actor based on a data array.

    Args:
        actor (vtk.vtkActor): The VTK actor to color.
        array (dict): The data array to use for color mapping.
    """
    _min, _max = array.get("range")
    mapper = actor.GetMapper()
    mapper.SelectColorArray(array.get("text"))
    mapper.GetLookupTable().SetRange(_min, _max)
    if array.get("type") == v.vtkDataObject.FIELD_ASSOCIATION_POINTS:
        dMapper.SetScalarModeToUsePointFieldData()
    else:
        dMapper.SetScalarModeToUseCellFieldData()
    mapper.SetScalarVisibility(True)
    mapper.SetUseLookupTableScalarRange(True)

@state.change("mesh_color_array_idx")
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    """
    State change callback to update the color mapping of the mesh.

    Args:
        mesh_color_array_idx (int): The index of the data array to use for color mapping.
    """
    array = dataset_arrays[mesh_color_array_idx]
    color_by_array(dActor, array)
    ctrl.view_update()


# Color Map Callbacks
def use_preset(actor, preset):
    """
    Apply a color lookup table preset to an actor.

    Args:
        actor (vtk.vtkActor): The VTK actor to update.
        preset (int): The color preset to apply (Rainbow, Inverted_Rainbow, Greyscale, Inverted_Greyscale).
    """
    lut = actor.GetMapper().GetLookupTable()
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

@state.change("mesh_color_preset")
def update_mesh_color_preset(mesh_color_preset, **kwargs):
    """
    State change callback to update the color preset of the mesh.

    Args:
        mesh_color_preset (int): The new color preset.
    """
    use_preset(dActor, mesh_color_preset)
    ctrl.view_update()

@state.change("zlayer_color_preset")
def update_zlayer_color_preset(zlayer_color_preset, **kwargs):
    """
    State change callback to update the color preset of the Z-layer.

    Args:
        zlayer_color_preset (int): The new color preset.
    """
    use_preset(zActor, zlayer_color_preset)
    ctrl.view_update()


# Opacity Callbacks
@state.change("mesh_opacity")
def update_mesh_opacity(mesh_opacity, **kwargs):
    """
    Update the opacity of the mesh actor when the 'mesh_opacity' state changes.

    Args:
        mesh_opacity (float): The new opacity value for the mesh actor.
    """
    dActor.GetProperty().SetOpacity(mesh_opacity)
    ctrl.view_update()

@state.change("zlayer_opacity")
def update_zlayer_opacity(zlayer_opacity, **kwargs):
    """
    Update the opacity of the Z-layer actor when the 'zlayer_opacity' state changes.

    Args:
        zlayer_opacity (float): The new opacity value for the Z-layer actor.
    """
    zActor.GetProperty().SetOpacity(zlayer_opacity)
    ctrl.view_update()


# ZLayer Callbacks
def update_zlayer(z_value, actor, **kwargs):
    """
    Update the Z-layer by creating a new threshold filter and reconfiguring the actor.

    Args:
        z_value (float): The Z value used to set the lower threshold of the threshold filter.
        actor (vtk.vtkActor): The VTK actor to update.

    Returns:
        vtk.vtkActor, vtk.vtkDataSetMapper: The updated actor and mapper for the Z-layer.
    """
    renderer.RemoveActor(actor)
    threshold_filter = v.vtkThreshold()
    threshold_filter.SetInputData(dataset)
    threshold_filter.SetInputArrayToProcess(0, 0, 0, v.vtkDataObject.FIELD_ASSOCIATION_POINTS, 'tentlevel')
    threshold_filter.SetInputArrayToProcess(1, 0, 0, v.vtkDataObject.FIELD_ASSOCIATION_CELLS, 'tentnumber')
    threshold_filter.UseContinuousCellRangeOn()
    threshold_filter.SetLowerThreshold(z_value)
    threshold_filter.SetUpperThreshold(default_max)
    threshold_filter.Update()

    # Visualize the layer
    zMapper = v.vtkDataSetMapper()
    zMapper.SetInputData(threshold_filter.GetOutput())
    zActor = v.vtkActor()
    zActor.SetMapper(zMapper)
    renderer.AddActor(zActor)
    
    representation(zActor)
    set_map_colors(zMapper)
    
    # Update the view
    renderWindow.Render()
    ctrl.view_update()
    
    # Return new Actor & Map
    return zActor, zMapper

@state.change("z_value")
def update_zlayer_helper(z_value, **kwargs):
    """
    Helper function to update the Z-layer when the 'z_value' state changes.

    Args:
        z_value (float): The new Z value to set the lower threshold of the threshold filter.
    """
    global zActor, zMapper # For change to affect - To Do: make a better solution (?)
    zActor, zMapper = update_zlayer(z_value, zActor)

# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------

def standard_buttons():
    """
    Define standard buttons for the GUI, including a checkbox for dark mode and a button to reset the camera.
    """
    vuetify.VCheckbox(
        v_model="$vuetify.theme.dark",
        on_icon="mdi-lightbulb-off-outline",
        off_icon="mdi-lightbulb-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    with vuetify.VBtn(icon=True, click="$refs.view.resetCamera()"):
        vuetify.VIcon("mdi-crop-free")

def pipeline_widget():
    """
    Define the pipeline widget for the GUI, including a tree view to manage the visibility of different components.
    """
    trame.GitTree(
        sources=(
            "pipeline",
            [
                {"id": "1", "parent": "0", "visible": 1, "name": "Default"},
                {"id": "2", "parent": "1", "visible": 1, "name": "Z-Layer"},
            ],
        ),
        
        actives_change=(actives_change, "[$event]"),
        visibility_change=(visibility_change, "[$event]"),
    )

def ui_card(title, ui_name):
    """
    Create a UI card component for organizing GUI elements.

    Args:
        title (str): The title of the card.
        ui_name (str): The name used to show/hide the card based on the active UI state.

    Returns:
        vuetify.VCardText: The content area of the card.
    """
    with vuetify.VCard(v_show=f"active_ui == '{ui_name}'"):
        vuetify.VCardTitle(
            title,
            classes="grey lighten-1 py-1 grey--text text--darken-3",
            style="user-select: none; cursor: pointer",
            hide_details=True,
            dense=True,
        )
        content = vuetify.VCardText(classes="py-2")
    return content

def d_card():
    """
    Define the UI card for the default mesh settings, including options for representation, color, and opacity.
    """
    with ui_card(title="Default", ui_name="default"):
        vuetify.VSelect(
            # Representation
            v_model=("mesh_representation", Representation.SurfaceWithEdges),
            items=(
                "representations",
                [
                    {"text": "Points", "value": 0},
                    {"text": "Wireframe", "value": 1},
                    {"text": "Surface", "value": 2},
                    {"text": "SurfaceWithEdges", "value": 3},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color By
                    label="Color by",
                    v_model=("mesh_color_array_idx", 0),
                    items=("array_list", dataset_arrays),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("mesh_color_preset", LookupTable.Rainbow),
                    items=(
                        "colormaps",
                        [
                            {"text": "Rainbow", "value": 0},
                            {"text": "Inv Rainbow", "value": 1},
                            {"text": "Greyscale", "value": 2},
                            {"text": "Inv Greyscale", "value": 3},
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
        vuetify.VSlider(
            # Opacity
            v_model=("mesh_opacity", 1),
            min=0,
            max=1,
            step=0.05,
            label="Opacity",
            classes="mt-1",
            hide_details=True,
            dense=True,
            thumb_label=True,
        )

def z_card():
    """
    Define the UI card for the Z-layer settings, including options for representation, color, opacity, and Z-layer value.
    """
    with ui_card(title="Z-Layer", ui_name="zlayer"):
        vuetify.VSelect(
            # Representation
            v_model=("zlayer_representation", Representation.Surface),
            items=(
                "representations",
                [
                    {"text": "Points", "value": 0},
                    {"text": "Wireframe", "value": 1},
                    {"text": "Surface", "value": 2},
                    {"text": "SurfaceWithEdges", "value": 3},
                ],
            ),
            label="Representation",
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
        )
        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="6"):
                vuetify.VSelect(
                    # Color Map
                    label="Colormap",
                    v_model=("zlayer_color_preset", LookupTable.Rainbow),
                    items=(
                        "colormaps",
                        [
                            {"text": "Rainbow", "value": 0},
                            {"text": "Inv Rainbow", "value": 1},
                            {"text": "Greyscale", "value": 2},
                            {"text": "Inv Greyscale", "value": 3},
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    outlined=True,
                    classes="pt-1",
                )
        vuetify.VSlider(
            # Opacity
            v_model=("zlayer_opacity", 0),
            min=0,
            max=1,
            step=0.05,
            label="Opacity",
            classes="mt-1",
            hide_details=True,
            dense=True,
        )
        vuetify.VSlider(
            # layers
            v_model=("z_value", 0.0),
            min=0,
            max=30,
            step=1,
            label="Z-Layer",
            classes="mt-1",
            hide_details=True,
            dense=True,
            thumb_label=True,
            reverse=True,
        )

# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

with SinglePageWithDrawerLayout(server) as layout:
    layout.title.set_text("Viewer")

    with layout.toolbar:
        # toolbar components
        vuetify.VSpacer()
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()

    with layout.drawer as drawer:
        # drawer components
        drawer.width = 325
        pipeline_widget()
        vuetify.VDivider(classes="mb-2")
        d_card()
        z_card()

    with layout.content:
        # content components
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            # Some performance hits, but works
            view = vtk.VtkRemoteView(renderWindow, interactive_ratio=1)
            # Fast, but colors don't work/render within
            # view = vtk.VtkLocalView(renderWindow)
            # view = vtk.VtkRemoteLocalView(
            #     renderWindow, namespace="view", mode="local", interactive_ratio=1
            # )
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera
         
# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start()