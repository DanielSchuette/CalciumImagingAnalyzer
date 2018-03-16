'''
developed by Daniel (d.schuette@online.de)
This is an app for analyzing calcium imaging results
latest version: v0.03 (as of 03/10/2018)
-> runs with python 2.7.14 and with python 3.6.x
repository: https://github.com/DanielSchuette/CalciumImagingAnalyzer.git
'''
current_app_version = "v0.04"
gui_size = dict(width=850, height=800)
popup_config = dict(width=500, height=500, takefocus=True)
background_color = "light yellow"
background_color2 = "light blue"
#####################################
#### Import All Required Modules ####
#####################################
import warnings
with warnings.catch_warnings(): # suppresses keras' annoying numpy warning
    warnings.simplefilter("ignore")
    import keras
    from keras import layers
    import tensorflow as tf
import tifffile as tiff # module downloaded from https://github.com/blink1073/tifffile.git
import numpy as np
import pandas as pd
import matplotlib
import time
matplotlib.use("TkAgg") # otherwise matplotlib will crash the app
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import pylab
import sys
from sys import platform
if sys.version_info[0] < 3:
    import Tkinter as tk
    import ttk as ttk
    import tkMessageBox
    import tkFileDialog  

else: # Python 3 does work as well after fixing 'Foundation' module (from pyobjc)
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox as tkMessageBox
    from tkinter import filedialog as tkFileDialog

import os, errno
import helpers as hlp # imports helpers.py

''' 
--> A grafical user interface makes it possible to interact with the app;
A tkinter GUI makes is set up and allows to manually adjust certain parameters.
''' 
# app starts here!
print("\n" + "********************************" + "\n")
print("Calcium Imaging Analyzer {}".format(current_app_version))
print("\n" + "********************************" + "\n")

####################
#### Set GUI up ####
####################

root = tk.Tk()
root.minsize(100, 100)
root.maxsize(925, 825)
root.title("Calcium Imaging Analyzer {}".format(current_app_version))
root.config()

# use scrollableFrame class to create a scrollable main window (access canvas via scrollableFrame.canvas)
main_frame = hlp.scrollableFrame(root)
main_frame.pack(fill=tk.BOTH, expand=True)
main_frame.config()

# create input and output areas
main_frame.canvas.create_rectangle(5, 5, 430, 805, fill=background_color)
main_frame.canvas.create_rectangle(430, 5, 905, 805, fill=background_color2)

# include a message box to ask if user wants to quit/restart (via window manager or drop down menu) 
def callback_when_quit():
    if tkMessageBox.askokcancel("Quit", "Do you really want to quit?\nAll unsaved progress will be lost..."):
        root.destroy()
        sys.exit(0)

def callback_when_restart(): #Restarts the current program.
    if tkMessageBox.askokcancel("Restart", "Do you really want to restart?\nAll unsaved progress will be lost..."):
    	python = sys.executable
    	os.execl(python, python, * sys.argv)

# catch file paths from open and close buttons
open_file_path = False # initialize a file path to open .lsm from
def pressed_open():
	global open_file_path
	open_file_path = tkFileDialog.askopenfilename(parent=root)
	if open_file_path != False:
		if not open_file_path.endswith(".lsm"):
			tkMessageBox.showerror("Error", "You have to select a .lsm file!")


save_file_path = str("/") ## initialize a directory to save to
def pressed_save():	
	global save_file_path
	save_file_path = tkFileDialog.askdirectory(parent=root)

## functions defining actions of analysis buttons
# file_path = "/Users/daniel/Documents/Yale/Projects/calcium_imaging/20180125_20180213/20180213_SNU475_2.lsm"
def pressed_preview():
	global file_path
	# create figure using one of the analysis functions
	fig = hlp.preprocessingFunction(i=1, file_path=open_file_path)
	
	# initialize a popup window widget:
	popup_window = hlp.PopupWindow(master=root, title="Exploratory Data Analysis", **popup_config)
	if fig != False:
		# plot figure in popup window
		figure_1 = hlp.scrollableFigure(figure=fig, master=popup_window)
		print("You plotted an exploratory data analysis!")
	else:
		error_label = tk.Label(popup_window, text="You have to specify an input to plot a preview!", font="Arial 28 bold")
		error_label.grid(row=0, column=0, sticky=tk.NSEW)
	
	

def pressed_analyze():
	"nothing"

# define callback functions for input fields of main window
def file_entries_callback1(events):
	print("Please enter a valid file path ('.lsm' file as input) or directory (to write output to)!")

def get_input_file_path():
	print("You have entered the following file path: {}".format(open_file_path_entry.get()))	

## add a drop down menu to root window and give the application a name other than 'python'...
if platform == 'darwin': # Check if we're on OS X; This required 'pyobjc' and it's dependencies (among which is 'Foundation')
	from Foundation import NSBundle
	bundle = NSBundle.mainBundle()
	if bundle:
		info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
		if info and info['CFBundleName'] == 'Python':
			info['CFBundleName'] = "Calcium Imaging Analyzer {}".format(current_app_version)

# instantiate a drop down menu...
menubar = tk.Menu(root)

# ... and add a file menu,
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open...", command=pressed_open)
filemenu.add_command(label="Save Directory", command=pressed_save)
filemenu.add_separator()
filemenu.add_command(label="Restart", command=callback_when_restart)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=callback_when_quit)

# ... a help menu,
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help", command=hlp.open_help_popup)
helpmenu.add_command(label="About...", command=hlp.open_about_popup)

# ... and an analysis menu.
analysismenu = tk.Menu(menubar, tearoff=0)

analysismenu.add_command(label="Preview", command=pressed_preview)
analysismenu.add_command(label="Analyze", command=pressed_analyze)

# Then, add drop down menus to menu bar
menubar.add_cascade(label="File", menu=filemenu)
menubar.add_cascade(label="Analysis", menu=analysismenu)
menubar.add_cascade(label="Help", menu=helpmenu)

# add the drop down manu to GUI's root window
root.config(menu=menubar)

# add a message window when user wants to quit the application (similar to menu bar's 'Exit')
root.protocol("WM_DELETE_WINDOW", callback_when_quit)

# column labels
main_frame.canvas.create_text(15, 25, text="DATA INPUT", font="Arial 44 bold", anchor=tk.NW)
main_frame.canvas.create_text(440, 25, text="ANALYSIS OUTPUT", font="Arial 44 bold", anchor=tk.NW)


# file path and directory path entry widgets
open_file_path_entry = tk.Entry(main_frame.canvas, width=35, font="Arial 18 italic", highlightbackground=background_color)
open_file_path_entry.delete(0, tk.END)
open_file_path_entry.insert(0, "No file path entered...")
main_frame.canvas.create_window(15, 85, window=open_file_path_entry, anchor=tk.NW)

save_directory_path_entry = tk.Entry(main_frame.canvas, width=35, font="Arial 18 italic", highlightbackground=background_color2)
save_directory_path_entry.delete(0, tk.END)
save_directory_path_entry.insert(0, "No directory specified...")
main_frame.canvas.create_window(440, 85, window=save_directory_path_entry, anchor=tk.NW)

# creates buttons to get input file path and output directories
input_file_button = tk.Button(main_frame.canvas, width=8, text="Get Input", font="Arial 14", command=get_input_file_path)
main_frame.canvas.create_window(15, 120, window=input_file_button, anchor=tk.NW)

# bind entries and buttons to events
open_file_path_entry.bind("<Button-1>", file_entries_callback1)


'''
open_file_path_label = tk.Label(XXX, text="Please enter a data file:", font="Arial 18", bg=background_color)
open_file_path_label.grid(row=2, column=0, sticky=tk.NW, padx=4, pady=8)

save_directory_path_label = tk.Label(XXX, text="Please enter a data file:", font="Arial 18", bg=background_color)
save_directory_path_label.grid(row=2, column=2, sticky=tk.NW, padx=50, pady=8)
'''

##########################
#### Tkinter mainloop ####
##########################
# start tkinter main loop and make sure that the window comes to the front after starting the app
# another solution: $root.lift() $root.attributes('-topmost',True) $root.after_idle(root.attributes,'-topmost',False)
os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
root.mainloop()


