import pyvista as pv
import vtk
import numpy as np

from pyvista.plotting.themes import DocumentTheme # Creating a theme
from pyvista.plotting.opts import ElementType # For element_picking (selecting a 'face')

# Theme testing
my_theme = DocumentTheme()
my_theme.background = '#dddddd'
# my_theme.show_vertices = True
my_theme.show_edges = True
my_theme.split_sharp_edges = True
my_theme.edge_color = 'k'
my_theme.enable_camera_orientation_widget = True # Creates the camera bars in TOP RIGHT
pv.global_theme.load_theme(my_theme)

# Read the VTK file using PyVista
filename = "test-files/file.vtk"
mesh = pv.read(filename)

# Extract data arrays
dataset_arrays = []
point_data = mesh.point_data
cell_data = mesh.cell_data
# These loops get more data via field association? (impacts the meshes and colors..)
for i, (name, array) in enumerate(point_data.items()):
    array_range = np.min(array), np.max(array)
    dataset_arrays.append(
        {
            "text": name,
            "value": i,
            "range": list(array_range),
            "type": vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
        }
    )
for i, (name, array) in enumerate(cell_data.items()):
    array_range = np.min(array), np.max(array)
    dataset_arrays.append(
        {
            "text": name,
            "value": i,
            "range": list(array_range),
            "type": vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
        }
    )

default_array = dataset_arrays[0]
default_min, default_max = default_array.get("range")

# Create the plotter
plotter = pv.Plotter()

# Add the default mesh
dActor = plotter.add_mesh(mesh, scalars=default_array.get("text"), cmap="rainbow")

# Threshold for Z-Layer
threshold_value = 0.5 * (default_min + default_max)
z_layer = mesh.threshold([threshold_value, default_max], scalars='tentlevel')

# Add the Z-Layer mesh
zActor = plotter.add_mesh(z_layer, scalars=default_array.get("text"), cmap="rainbow", opacity=0.5)

# Set up the camera and view
plotter.view_xy()
plotter.add_axes()
plotter.show_grid()

# Define update functions
def update_mesh_representation(representation):
    plotter.remove_actor(dActor)
    if representation == "Points":
        plotter.add_mesh(mesh, scalars=default_array.get("text"), cmap="rainbow", style='points')
    elif representation == "Wireframe":
        plotter.add_mesh(mesh, scalars=default_array.get("text"), cmap="rainbow", style='wireframe')
    elif representation == "Surface":
        plotter.add_mesh(mesh, scalars=default_array.get("text"), cmap="rainbow", style='surface')
    elif representation == "SurfaceWithEdges":
        plotter.add_mesh(mesh, scalars=default_array.get("text"), cmap="rainbow", style='surface')
        plotter.add_mesh(mesh.extract_edges(), color='black')

def update_zlayer_representation(representation):
    plotter.remove_actor(zActor)
    if representation == "Points":
        plotter.add_mesh(z_layer, scalars=default_array.get("text"), cmap="rainbow", style='points')
    elif representation == "Wireframe":
        plotter.add_mesh(z_layer, scalars=default_array.get("text"), cmap="rainbow", style='wireframe')
    elif representation == "Surface":
        plotter.add_mesh(z_layer, scalars=default_array.get("text"), cmap="rainbow", style='surface')
    elif representation == "SurfaceWithEdges":
        plotter.add_mesh(z_layer, scalars=default_array.get("text"), cmap="rainbow", style='surface')
        plotter.add_mesh(z_layer.extract_edges(), color='black')

def update_mesh_color_by_name(index):
    array = dataset_arrays[index]
    plotter.update_scalars(mesh, scalars=array.get("text"), cmap="rainbow")

def update_zlayer_color_by_name(index):
    array = dataset_arrays[index]
    plotter.update_scalars(z_layer, scalars=array.get("text"), cmap="rainbow")

def update_mesh_opacity(opacity):
    dActor.GetProperty().SetOpacity(opacity)
    plotter.render()

def update_zlayer_opacity(opacity):
    zActor.GetProperty().SetOpacity(opacity)
    plotter.render()

def update_zlayer(z_value):
    global z_layer, zActor
    plotter.remove_actor(zActor)
    z_layer = mesh.threshold([z_value, default_max], scalars='tentlevel')
    zActor = plotter.add_mesh(z_layer, scalars=default_array.get("text"), cmap="rainbow", opacity=0.5)
    plotter.render()

# Checkbox callback to show/hide Z-layer or default mesh
def checkbox_callback(value):
    if value:
        dActor.VisibilityOn()
        zActor.VisibilityOff()
    else:
        dActor.VisibilityOff()
        zActor.VisibilityOn()
    plotter.render()

# Add slider to control the Z-layer
def slider_callback(value):
    update_zlayer(value)

# Adjust these values according to your data range
slider_min = default_min
slider_max = default_max

# Add the slider
plotter.add_slider_widget(
    slider_callback,
    rng=[slider_min, slider_max],
    value=threshold_value,
    title="Z-layer Threshold",
    style='modern'
)

# Add the checkbox - Toggle between meshes
plotter.add_checkbox_button_widget(
    checkbox_callback,
    value=True, # Default is checked = default mesh
)

plotter.enable_element_picking(mode=ElementType.FACE)

# Show the plot
plotter.show()

try:
    width, height = plotter.window_size
    plotter.iren._mouse_right_button_press(419, 263)
    plotter.iren._mouse_right_button_release()
except AttributeError:
    pass
