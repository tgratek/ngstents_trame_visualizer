from pyvista_trame import VTKVisualizer

visualizer = VTKVisualizer(filename="file.vtk")
visualizer.server.start()