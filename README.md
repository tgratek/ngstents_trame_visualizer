# NGS-Tents PyVista + Trame Visualizer

A prototype application meant for better visualizing meshes generated from [NGS-Tents](https://github.com/jayggg/ngstents) through
utilizing the libraries [PyVista](https://github.com/pyvista/pyvista) and [Trame](https://github.com/Kitware/trame).
This application takes a valid VTK file generated from NGS-Tents, plots the mesh using PyVista's 3D visualization capabilities, and
encases the viewer around a single-page layout operated by the Vuetify framework made available from Trame.

Refer to NGS-Tents' [documentation](https://jayggg.github.io/ngstents/StartPitching.html) for context on the expected input
for the application. The documentation also showcases the existing NGSolve visualizations that this new visualizer is aiming
to improve upon and provide a means to dynamically render various tent levels within the interface.

## Applications

Two classes are provided: `PyVistaVTKVisualizer` and `TrameVTKVisualizer`. They are both applications that serve the same
purpose of wrapping a UI around the mesh visualization, but utilize different libraries and default **rendering methods**.

- `PyVistaVTKVisualizer` starts with _remote, server-side_ rendering by default.
  - PyVista struggles with its local rendering due to desyncing issues, but they offer a very stable remote environment with increased interactivity, at the cost of slower performance.
  - PyVista's simplistic Pythonic API to VTK allows for easier extendability due to needing little to no prior knowledge of VTK.
- `TrameVTKVisualizer` starts with _local, client-side_ rendering by default.
  - This application exists to provide a tolerable method to view meshes using client-side rendering, a naturally faster process that uses local resources.
  - Trame relies on direct calls to the VTK API, resulting in more complex and harder to maintain code.

For the sake of development transparency and experimentation, both applications contain a button to switch to the opposite rendering method. We do not advise general users to switch
away from the default, especially from `PyVistaVTKVisualizer` Remote -> Local due to the desync issues. Nonetheless, we offer this option to showcase both applications' abilities to
use both types of rendering, albeit with some lack of refinement.

**Do not import both classes in a given module**, unless done so conditionally. PyVista uses Trame as a backend, so importing
both classes can cause conflicts. By default, both applications utilize the same server, so they cannot be used in conjuction. Use one or the other when visualizing a VTK file through
a Jupyter Notebook or Python module.

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

### "Toggle axis" state is incorrect upon starting PyVista app

The UI from `PyVistaVTKVisualizer` mistakenly shows the "Toggle axis" button as turned off, despite the axes orientation
widget showing in the bottom left of the viewer.

_Workaround_: Toggle the button to turn it to its ON state. Clicking the button again will properly hide the axes orientation widget.

### Desync in PyVista Local Rendering

As mentioned, client-side rendering in PyVista suffers problems where state can go out of sync, causing the visualization to entirely de-render or freeze. PyVista often responds to
this by falling back to remote server-side rendering, producing a flaky experience.
This issue occurs when re-renders occur, such as dragging the level slider or toggling the ruler grid.

For the latter example, PyVista affirms such desyncs are a result of their current local rendering pipeline: https://github.com/pyvista/pyvista/issues/5736

There is no definitive workaround, hence why we set the PyVista application's default server rendering to remote and advise against switching to local mode.
