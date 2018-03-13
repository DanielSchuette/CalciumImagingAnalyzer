# build app with python 2.7.14
from cx_Freeze import setup, Executable
import os
import sys
import matplotlib
import tkFileDialog
import FileDialog
import appdirs
import packaging
import packaging.version
import packaging.specifiers

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(includes = ["matplotlib.backends.backend_tkagg"],
					packages = ["Tkinter", "numpy.core._methods", "numpy.lib.format", "tkFileDialog", "matplotlib.style", "matplotlib.legend_handler", "FileDialog", "appdirs", "packaging"], 
					excludes = [])

base = 'Win32GUI' if sys.platform=='win32' else None

os.environ['TCL_LIBRARY'] = "/Library/Frameworks/Tcl.framework/Versions/8.6"

executables = [
    Executable('sample.py', base=base, targetName = 'CalciumImagingAnalyzer App')
]

setup(name='CalciumImagingAnalyzer',
      version = '0.02',
      description = 'This is an application for analyzing calcium imaging data from cm confocal microscopy.',
      options = dict(build_exe = buildOptions),
      executables = executables)
