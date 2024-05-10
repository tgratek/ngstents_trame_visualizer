# Installing ngstents Libraries and Dependancies
Getting the installation of ngstents and being able to have everything run correctly is a bit tricky. This is my attempt in having something that can be
recreated.

My Build:
- Windows 11
- VSCode - (Some extensions: Pylance, Python, Python Debugger, Python Environment Manager, Python Extension Pack, Python Indent, Jupyter)
- Python3.12
- pip v24

## Instructions
1. Install the virtual environment
    `py -m venv env` - Windows
    `python3 -m venv env` - Linux

2. Activate the venv:
    `.\env\Scripts\activate` - Windows
    `source env\bin\activate` - Linux

3. Remove pip cache - may help
    `pip cache purge`

4. Install ngstents
    `pip install ngstents`

5. Run the script:
    `py .\test.py` \\ `python3 .\test.py`
    Or
    `netgen .\test.py`


## Useful Commands
- `pip install --force-reinstall <package>` - Redownloads and reinstalls a package
- `pip uninstall <package>` - Uninstall a package
- `pip cache purge` - Clears the pip cache