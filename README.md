# Calcium Imaging Analyzer App - Git Repository:

This repository provides a GUI application that facilitates the analysis of calcium imaging data - that includes EDA, cell identification, and extraction of summary statistics. The app is currently under development. The current version 0.11 runs on macOS (tested with High Sierra), but it should be Windows-compatible.


# Requirements:

## System requirements
macOS High Sierra. Other OS might work as well.

### Dependencies
If you want to build the app from source, make sure to install (`$pip install <python_module>`) all dependencies that are listed below. 

- keras and tensorflow backend
- skimage (scikit-image)
- numpy
- pandas
- matplotlib
- tifffile
- Tkinter
- tkMessageBox
- tkFileDialog
- pyobjc

## How I generated the example data
Confocal microscopy images (a 'movie') of live cells are provide as an example ('data/'). The cells were grown on a coverslip for 48h and then incubate with a calcium dye for 30min. During the experiments, cells were stimulated with different concentrations of ATP to evoke calcium responses (i.e. increases in fluorescence intensity).


# Analysis workflow:

## Overview
Currently, the following functionality is available:

#### You can load a file and use the 'Preview' function to see pixel value distribution and the impact of different filters. 

#### You can find cells in your image using the 'Find cells' function from the drop down menu.

#### You can analyze the calcium response of your cells over time using the 'Analysis' function.


## Input format
A .lsm file exported from a Zeiss LSM series confocal microscope (e.g. LSM 710). The source code can be modified to integrate other file formats (e.g. .tif) as well. 

## Analysis
'Preview' provides a pre-processing analysis of pixel value distribution and filters. Identification of cells is done via a connected components labeling algorithm. During the actual analysis, the identified cells are masked and tracked over time to derive a time course of relative fluorescence intensities.

## Output format
Saving the analysis results to an output directory is currently not supported!

## Interpretation of results
See figure titles and 'Analysis' section.

# This software is stil under development! Release of a working version is planned for April '18!