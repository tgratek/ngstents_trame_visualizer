import sys
import os

# Construct the full path to the src directory and add to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '../src'))

"""
    If PyVistaVTKVisualizer is imported alongside TrameVTKVisualizer, uses of the
    former class will result in a ZeroDivisionError, originating from an attempt
    to start a web server from the trame_server external dependency. 
    
    This likely occurs because PyVista uses trame as a backend, so importing
    TrameVTKVisualizer conflicts with what PyVista expects.

    As such, the visualizers should not be used together, and should only
    be imported together if done so conditionally.
"""
# from pyvista_visualizer import PyVistaVTKVisualizer
from trame_visualizer import TrameVTKVisualizer

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    # TODO: Argument parsing to choose which visualizer to import
    # --port #### will open the instance on the given port.
    
    # visualizer = PyVistaVTKVisualizer(filename=os.path.join(ROOT_DIR, "test-files/demo.vtk"))
    visualizer = TrameVTKVisualizer(filename=os.path.join(ROOT_DIR, "test-files/demo.vtk"))

    visualizer.server.start()

except FileNotFoundError as e:
    print(e)