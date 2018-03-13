# Calcium Imaging Analyzer App - Git Repository:

This repository will contain an app that facilitates the analysis of calcium imaging data. 
The app is currently under development and undergoes major changes. Thus, some python source code is still stored in my 'AppsInDev' repository. Future changes to the app will be managed in this repository; as soon as I released a working beta version. The current version 0.02 provides a stand-alone application but works only on macOS (tested with High Sierra).

# Requirements:

## System requirements
macOS High Sierra. Other macOS should also work since the current version 0.02 is a stand-alone application and comes with python 2.7 and all modules ('sample/'). 

## How I generated the example data
Confocal microscopy images / a 'movie' of live cells that were incubate with a calcium dye are provide as an example ('data/').


# Analysis workflow:

## Overview
Currently, only very limited functionality is available.

## Input format
A .lsm file exported from a Zeiss LSM series confocal microscope (e.g. LSM 710). The source code can be modified to integrate other file formats (e.g. .tif) as well. 

## Analysis
'Preview' provides a pre-processing analysis of pixel value distribution and filters. 

## Output format
A pop-up window displaying pre-processing analysis results.

## Interpretation of results
See figure titles.

# This software is stil under development! Release of a working version is planned for March '18!