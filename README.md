# NGSTents PyVista + Trame Visualizer

A prototype application meant for better visualizing meshes generated from [NGS-Tents](https://github.com/jayggg/ngstents) through
utilizing the libraries [PyVista](https://github.com/pyvista/pyvista) and [Trame](https://github.com/Kitware/trame).
This application takes a valid VTK file generated from NGS-Tents, plots the mesh using PyVista's 3D visualization capabilities, and
encases the viewer around a single-page layout operated by the Vuetify framework made available from Trame.

## Application

Two classes are provided: `PyVistaVTKVisualizer` and `TrameVTKVisualizer`. They are both applications that serve the same
purpose of wrapping a UI around the mesh visualization, but utilize different libraries and default **rendering methods**.

- `PyVistaVTKVisualizer` starts in remote server-side rendering by default. PyVista struggles with its local rendering
  due to desyncing issues, but they offer a very stable remote environment with increased interactivity, at the cost of slower performance. PyVista's simplistic Pythonic API to VTK allows for easier extendability due to needing little to no prior
  knowledge of VTK.
- `TrameVTKVisualizer` starts in local client-side rendering by default. This application exists to provide a tolerable method
  to view meshes using client-side rendering, a naturally faster process that uses local resources. Trame relies on direct calls to the VTK API, resulting in more complex and harder to maintain code.

**Do not import both classes in a given module**, unless done so conditionally. PyVista uses Trame as a backend, so importing
both classes can cause conflicts. By default, both applications utilize the same server, so they cannot be used in conjuction. Use one or the other when visualizing a VTK file through a Jupyter Notebook or Python module.

## Example Demo

Contained in the `/tools_demo` directory are notebooks and a Python module that test the visualizer classes created from PyVista
and pure Trame. After pulling down this repo and installing its dependencies with `pip install -r requirements.txt`,
you can run the tools:

- **(Remote)** Run the `pyvista_vtkvisulizer.ipynb` notebook for a cell that visualizes a VTK file using **server-side** rendering.
- **(Local)** Run the `trame_vtkvisulizer.ipynb` notebook for a cell that visualizes a VTK file using **client-side** rendering.
- **(Browser)** Run `python3 tools_demo/vtkvisualizer.py` to start up a localhost server of the PyVista visualizer.
  - Optionally, you can comment the import and uses of `PyVistaVTKVisualizer` and uncomment the `TrameVTKVisualizer` lines to test the client-side focused app on a browser server.

### Notice when Running for the First Time

First execution of either of the applications may take a while (rendering `demo.vtk` took about 20-30 seconds on PyVista).  
Once the application downloads the necessary VTK resources, subsequently runtime is much faster.

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
