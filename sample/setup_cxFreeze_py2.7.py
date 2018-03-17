# build app with python 2.7.14
from cx_Freeze import setup, Executable
import os
import sys
import io
import matplotlib
import tkFileDialog
import FileDialog
import appdirs
import packaging
import packaging.version
import packaging.specifiers
import tensorflow
import tensorflow.core.protobuf
from google.protobuf import descriptor as _descriptor

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(includes = ["matplotlib.backends.backend_tkagg"],
					include_files = ["../data/if_application-x-python_8974.icns", "../data/example_data.lsm"],
					packages = ["Tkinter", "numpy.core._methods", "numpy.lib.format", "tkFileDialog", "matplotlib.style", "matplotlib.legend_handler", "FileDialog", "appdirs", "packaging", "io"], 
					excludes = [])

base = 'Win32GUI' if sys.platform=='win32' else None

os.environ['TCL_LIBRARY'] = "/Library/Frameworks/Tcl.framework/Versions/8.6"

executables = [
    Executable("sample.py", base=base, targetName = "CalciumImagingAnalyzer App", icon="../data/if_application-x-python_8974.icns")
]

setup(name='CalciumImagingAnalyzer',
      version = '0.02',
      description = 'This is an application for analyzing calcium imaging data generated via confocal microscopy.',
      options = dict(build_exe = buildOptions),
      executables = executables)
