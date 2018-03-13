'''
developed by Daniel (d.schuette@online.de)
This is an app for analyzing calcium imaging results
latest version: v0.03 (as of 03/10/2018)
-> runs with python 2.7.14 and not with python 3.6.x
repository: https://github.com/DanielSchuette/CalciumImagingAnalyzer.git
'''
current_app_version = "v0.03"
gui_size = dict(width=700, height=700)
popup_config = dict(width=500, height=500, takefocus=True)
#####################################
#### Import All Required Modules ####
#####################################
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
else: # currently, Python 3 does not work 
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
import tkFileDialog    
import os, errno
import helpers as hlp

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

## set up window
root = tk.Tk()
root.title("Calcium Imaging Analyzer {}".format(current_app_version))
root.config(**gui_size)

# include a message box to ask if user wants to quit/restart (via window manager or drop down menu) 
def callback_when_quit():
    if tkMessageBox.askokcancel("Quit", "Do you really want to quit?\nAll unsaved progress will be lost..."):
        root.destroy()
        sys.exit(0)

def callback_when_restart(): #Restarts the current program.
    if tkMessageBox.askokcancel("Restart", "Do you really want to restart?\nAll unsaved progress will be lost..."):
    	python = sys.executable
    	os.execl(python, python, * sys.argv)

# functions defining actions of analysis buttons
def pressed_preview():
	# create figure using one of the analysis functions
	fig = hlp.preprocessingFunction(i=392, 
		file_path="/Users/daniel/Documents/Yale/Projects/calcium_imaging/20180125_20180213/20180213_SNU475_2.lsm")
	
	# initialize a popup window widget:
	popup_window = hlp.PopupWindow(master=root, title="Exploratory Data Analysis", **popup_config)

	# plot figure in popup window
	figure_1 = hlp.scrollableFigure(figure=fig, master=popup_window)
	print("You plotted an exploratory data analysis!")

	# add 'smaller' and 'larger' buttons to figure
	

def pressed_analyze():
	"nothing"

open_file_path = str("Not defined") # initialize a file path to open .lsm from
def pressed_open():
	global open_file_path
	open_file_path = tkFileDialog.askopenfilename(parent=root)
	if open_file_path != "Not defined":
		if not open_file_path.endswith(".lsm"):
			tkMessageBox.showerror("Error", "You have to select a .lsm file!")


save_file_path = str("/") ## initialize a directory to save to
def pressed_save():	
	global save_file_path
	save_file_path = tkFileDialog.askdirectory(parent=root)
	
## add a drop down menu to root window and give the application a name other than 'python'...
if platform == 'darwin': # Check if we're on OS X
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

##########################
#### Tkinter mainloop ####
##########################
# start tkinter main loop and make sure that the window comes to the front after starting the app
# another solution: $root.lift() $root.attributes('-topmost',True) $root.after_idle(root.attributes,'-topmost',False)
os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
root.mainloop()


