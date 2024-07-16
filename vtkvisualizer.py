from pyvista_trame import VTKVisualizer
# from trame_mod import TrameVTKVisualizer

try:
    visualizer = VTKVisualizer(filename="test-files/demo.vtk")
    visualizer.server.start()
except FileNotFoundError as e:
    print(e)