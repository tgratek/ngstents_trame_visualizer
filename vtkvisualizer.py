from pyvista_trame import VTKVisualizer

visualizer = VTKVisualizer(filename="test-files/file.vtk")
visualizer.server.start()