# NGSTents PyVista + Trame Visualizer

A prototype application meant for better visualizing meshes generated from [NGS-Tents](https://github.com/jayggg/ngstents) through
utilizing the libraries [PyVista](https://github.com/pyvista/pyvista) and [Trame](https://github.com/Kitware/trame).
This application takes a valid VTK file generated from NGS-Tents, plots the mesh using PyVista's 3D visualization capabilities, and
encases the viewer around a single-page layout operated by the Vuetify framework made available from Trame.

## Example Demo

Contained in the `tools` directory are notebooks and a Python module that test the visualizer classes created from PyVista
and pure Trame. After pulling down this repo and installing its dependencies, you can run the tools:

- **(Remote)** Run the `pyvista_vtkvisulizer.ipynb` notebook for a cell that visualizes a VTK file using **server-side** rendering.
- **(Local)** Run the `trame_vtkvisulizer.ipynb` notebook for a cell that visualizes a VTK file using **client-side** rendering.
- **(Browser)** Run `python3 tools/vtkvisualizer.py` to start up a localhost server of the PyVista visualizer.
  - Optionally, you can comment the import and uses of `PyVistaVTKVisualizer` and uncomment the `TrameVTKVisualizer` lines to test the client-side focused app on a browser server.

### Notice when Running for the First Time

Processing a `vtk` file for the first time may take a while (`file.vtk` took about 20-30 seconds) before the visualizer renders.
Once bundles are installed and a supposed cache is generated, runtime is much faster on subsequent runs.

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
