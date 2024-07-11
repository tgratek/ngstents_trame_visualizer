from pyvista_trame import VTKVisualizer

try:
    visualizer = VTKVisualizer(filename="test-files/file.vtk")
    visualizer.server.start()
except FileNotFoundError as e:
    print(e)