# NGSTents PyVista + Trame Visualizer

A prototype application meant for better visualizing meshes generated from [NGS-Tents](https://github.com/jayggg/ngstents) through
utilizing the libraries [PyVista](https://github.com/pyvista/pyvista) and [Trame](https://github.com/Kitware/trame).
This application takes a valid VTK file generated from NGS-Tents, plots the mesh using PyVista's 3D visualization capabilities, and
encases the viewer around a single-page layout operated by the Vuetify framework made available from Trame.

## Usage

After pulling down the repository and installing the necessary libraries, this visualizer supports two methods of usage.
Instantiate a variable of the `VTKVisualizer` class and either call its UI in a notebook or start a server:

**Local Jupyter Notebook**

```python
# vtkVisualizer.ipynb
from pyvista_trame import VTKVisualizer

visualizer = VTKVisualizer(filename="test-files/file.vtk")
await visualizer.ui.ready
visualizer.ui
```

**Local Server Rendering**

```python
# vtkVisualizer.py
from pyvista_trame import VTKVisualizer

visualizer = VTKVisualizer(filename="test-files/file.vtk")
visualizer.server.start()
```

This application is mainly intended for conference or presentation settings, leading to an emphasis on local environment usage.
Fully remote environment usage is not tested and likely not supported.

### Notice when Running for the First Time

Processing a `vtk` file for the first time may take a while (`file.vtk` took about 20-30 seconds) before the visualizer renders.
Once a supposed cache is generated, runtime is much faster on subsequent runs.

## Known Issues

### Dragging the tents level slider while on local view frequently flashes the remote view.

When the rendering mode is local, dragging the tents level slider to render different layers of tents
may sporadically show the VTK viewer from remote mode whilst dragging. Remote view remains unaffected
and is more consistent in rendering appearence. This issue is potentially a result of de-syncing issues
caused between PyVista's visualization and VTK local rendering, hence why PyVista likely falls back to
the more stable remote view in these flashes.

### "Toggle ruler" occasionally hides all objects on local rendering mode

When the rendering mode is local, toggling the ruler may cause the scene to de-render all objects. This is likely
due to the de-syncing issue of local viewing mentioned prior, further emphasized by a PyVista issue expressing
this same problem: https://github.com/pyvista/pyvista/issues/5736

_Workaround_: Toggle the ruler multiple times until the scene restores itself, or simply rerun the cell / refresh
the localhost window.
