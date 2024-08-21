import vtk
import sys

""" This is helps check any given VTK file to verify whether it has the correct format. 
    For example, VTK files with machine-error zero must be changed to zero to be correctly read by either PyVistaVTKVisualizer, or TrameVTKVisualizer.
"""

def read_vtk_file(file_path):
    reader = vtk.vtkUnstructuredGridReader()
    reader.SetFileName(file_path)
    reader.Update()

    # Check if there were errors during the read process
    error_code = reader.GetErrorCode()
    if error_code != vtk.vtkErrorCode.NoError:
        raise ValueError(f"Error reading VTK file: {vtk.vtkErrorCode.GetStringFromErrorCode(error_code)}")

    return reader.GetOutput()

def check_file(file_path):
    try:
        output = read_vtk_file(file_path)
        dataset_arrays = []
        fields = [
            (output.GetPointData(), vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS),
            (output.GetCellData(), vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS),
        ]

        for field in fields:
            field_arrays, association = field
            num_arrays = field_arrays.GetNumberOfArrays()

            for i in range(num_arrays):
                array = field_arrays.GetArray(i)
                if array is not None:
                    array_range = array.GetRange()
                    dataset_arrays.append(
                        {
                            "text": array.GetName(),
                            "value": i,
                            "range": list(array_range),
                            "type": association,
                        }
                    )

        if dataset_arrays:
            default_array = dataset_arrays[0]
            default_min, default_max = default_array.get("range")
            
        else:
            print("No arrays found in the dataset.")
            default_min, default_max = None, None
            
        print(f"Input file: '{file_path}' successfully checked...")
        print(f"The default_min: {default_min} and default_max: {default_max}")

    except ValueError as e:
        print(f"An error occurred analyzing the file '{file_path}'... ** ERROR: {e} **")
    
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <path_to_vtk_file>")
    else:
        file_path = sys.argv[1]
        check_file(file_path)