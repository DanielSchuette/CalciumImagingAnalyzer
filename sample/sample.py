'''
developed by Daniel (d.schuette@online.de)
This is an app for analyzing calcium imaging results
-> runs with python 2.7.14 and python 3.6.x on macOS High Sierra
repository: https://github.com/DanielSchuette/CalciumImagingAnalyzer.git
'''
current_app_version = "v0.15"
gui_size = dict(width=850, height=800)
popup_config = dict(width=500, height=500, takefocus=True, bg="light blue")
background_color = "light yellow"
background_color2 = "light blue"
#####################################
#### Import All Required Modules ####
#####################################
import warnings, timeit
with warnings.catch_warnings(): # suppresses keras' annoying numpy warning
	warnings.simplefilter("ignore")
	import keras
	from keras import layers
	import tensorflow as tf
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
import tensorflow.core.protobuf
import google.protobuf
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
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
import helpers as hlp # imports helpers.py
from skimage import measure
from skimage import filters
from skimage.feature import canny
from scipy import ndimage as ndi
from skimage.filters import sobel
from skimage.morphology import watershed
import logging

# initiate logging for debug purposes
import logging
logging.basicConfig(filename="/Users/daniel/Documents/GitHub/CalciumImagingAnalyzer/logfile.txt", 
					level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.debug("Start logging.")					
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
        logging.debug("End logging.")
        sys.exit(0)

def callback_when_restart(): #Restarts the current program.
    if tkMessageBox.askokcancel("Restart", "Do you really want to restart?\nAll unsaved progress will be lost..."):
    	python = sys.executable
    	os.execl(python, python, * sys.argv)

# callback function that activates inactivated entry fields when user clicks them
def activateEntryField(event):
	event.widget["state"] = tk.NORMAL

# catch file paths from open and close buttons
open_file_path = False # initialize a file path to open .lsm from
save_file_path = False # initialize a directory to save to

def pressed_open():
	global open_file_path
	open_file_path = tkFileDialog.askopenfilename(parent=root)
	if open_file_path != False:
		if not open_file_path.endswith(".lsm"):
			tkMessageBox.showerror("Error", "You have to select a .lsm file!")
	return(open_file_path)

def pressed_save():	
	global save_file_path
	save_file_path = tkFileDialog.askdirectory(parent=root)
	return(save_file_path)

def pressed_open_filemenu():
	global open_file_path_entry
	pressed_open()
	if open_file_path and open_file_path.endswith(".lsm"):
		open_file_path_entry.delete(0, tk.END)
		open_file_path_entry.insert(0, ("..." + str(open_file_path)[-32:]))
	else:
		open_file_path_entry.delete(0, tk.END)
		open_file_path_entry.insert(0, "No valid file selected")
		print("Please select a valid file ('.lsm' file as input)!")
	open_file_path_entry["state"] = tk.DISABLED

def pressed_save_filemenu():
	global save_directory_path_entry
	pressed_save()
	if save_file_path and os.path.isdir(save_file_path):
		save_directory_path_entry.delete(0, tk.END)
		save_directory_path_entry.insert(0, ("..." + str(save_file_path)[-32:]))
	else:
		save_directory_path_entry.delete(0, tk.END)
		save_directory_path_entry.insert(0, "No valid directory selected")
		print("Please enter a valid directory (to write output to)!")
	save_directory_path_entry["state"] = tk.DISABLED


## functions defining actions of analysis buttons
def buttonPressed(event):
	for button in button_list:
		button.config(state = "active")
		button.update()
		time.sleep(0.5)
		button.config(state = "normal")

def pressed_prepro_preview():
	global open_file_path
	# create figure using one of the analysis functions
	fig_1 = hlp.preprocessingFunction(image_number=preview_im_no_entry.get(), file_path=open_file_path, 
									  cutoff1=cutoff1_var.get(), cutoff2=cutoff2_var.get())
	
	# initialize a popup window widget:
	popup_window = hlp.PopupWindow(master=root, title="Exploratory Data Analysis", **popup_config)
	if fig_1 != False:
		# plot figure in popup window
		figure_1 = hlp.scrollableFigure(figure=fig_1, master=popup_window)
		print("You plotted an exploratory data analysis!")
	else:
		error_label = tk.Label(popup_window, text="You have to specify an\ninput to plot a preview!", font="Arial 28 bold",
							   bg="light yellow")
		error_label.grid(row=0, column=0, sticky=tk.NSEW)
	
	
ccl_object = False
def pressed_find_cells():
	global open_file_path
	global ccl_object
	
	if open_file_path:
		# load image
		image = tiff.imread(open_file_path)
		selected_image = image[0, 0, (int(analysis_im_no_entry.get()) - 1), :, :]
		ccl_object = hlp.ConnectedComponentsLabeling(input_image=selected_image, pixel_threshold=cutoff_analysis.get(), 
												 	 min_threshold=min_cell_size.get(), max_threshold=max_cell_size.get(), 
												 	 skimage=True, method="segmentation")
		# plot
		fig_2, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(10, 5))
		fig_2.subplots_adjust(wspace=0.45, hspace=0.05, right=0.80, left=0.05, bottom=0.05, top=0.95)

		# subplot 1
		ax1.set_title("Native Image")
		ax1.imshow(selected_image, cmap="gray")
		
		# subplot 2
		ax2.set_title("CCL Processed Image\nAll Sizes")
		ax2.imshow(ccl_object.im_ccl, cmap="nipy_spectral")
		
		# subplot 3
		ax3.set_title("CCL Processed Image\nSelected Sizes")
		subplot3 = ax3.imshow(ccl_object.im_with_cells, cmap="nipy_spectral")
		colbar_ax = fig_2.add_axes([0.85, 0.2, 0.03, 0.6]) 
		fig_2.colorbar(subplot3, cax=colbar_ax)
		
		# set up a popup window to plot figure to
		popup_window_2 = hlp.PopupWindow(master=root, title="Find Cells via CCL", **popup_config)
		figure_2 = hlp.scrollableFigure(figure=fig_2, master=popup_window_2)

	else:
		popup_window = hlp.PopupWindow(master=root, title="Find Cells via CCL", **popup_config)
		error_label = tk.Label(popup_window, text="You have to specify an\ninput to find some cells!", font="Arial 28 bold",
							   bg="light yellow")
		error_label.grid(row=0, column=0, sticky=tk.NSEW)

def pressed_analyze():
	global ccl_object
	global open_file_path
	if ccl_object:
		# analyze data
		image = tiff.imread(open_file_path)
		fig_3 = hlp.AnalyzeSingleCells(input_movie=image, ccl_object=ccl_object, start=0, stop=30, legend=False).figure
		
		# set up a popup window to plot figure to
		popup_window_3 = hlp.PopupWindow(master=root, title="Data Analysis", **popup_config)
		figure_3 = hlp.scrollableFigure(figure=fig_3, master=popup_window_3)

	else:
		popup_window = hlp.PopupWindow(master=root, title="Data Analysis", **popup_config)
		error_label = tk.Label(popup_window, text="To analyze your experiment,\nyou have to find some cells first!", 
							   font="Arial 28 bold", bg="light yellow")
		error_label.grid(row=0, column=0, sticky=tk.NSEW)

# define callback functions for input fields of main window
def file_entries_callback1(event):
	global open_file_path_entry, open_file_path
	open_file_path_entry["state"] = tk.NORMAL
	print("Please select a valid file ('.lsm' file as input)!")
	open_file_path_entry.delete(0, tk.END)
	open_file_path_entry.config(font="Arial 20")
	open_file_path = pressed_open()
	if open_file_path and open_file_path.endswith(".lsm"):
		open_file_path_entry.delete(0, tk.END)
		open_file_path_entry.insert(0, ("..." + str(open_file_path)[-32:]))
	else:
		open_file_path_entry.delete(0, tk.END)
		open_file_path_entry.insert(0, "No valid file selected")
		print("Please select a valid file ('.lsm' file as input)!")
	open_file_path_entry["state"] = tk.DISABLED

def file_entries_callback2(event):
	global save_directory_path_entry, save_file_path
	save_directory_path_entry["state"] = tk.NORMAL
	print("Please enter a valid directory (to write output to)!")
	save_directory_path_entry.delete(0, tk.END)
	save_directory_path_entry.config(font="Arial 20")
	save_file_path = pressed_save()
	if save_file_path and os.path.isdir(save_file_path):
		save_directory_path_entry.delete(0, tk.END)
		save_directory_path_entry.insert(0, ("..." + str(save_file_path)[-32:]))
	else:
		save_directory_path_entry.delete(0, tk.END)
		save_directory_path_entry.insert(0, "No valid directory selected")
		print("Please enter a valid directory (to write output to)!")
	save_directory_path_entry["state"] = tk.DISABLED

def get_input_file_path():
	global open_file_path_entry, open_file_path
	if open_file_path and open_file_path.endswith(".lsm"):
		input_var.set(str("..." + open_file_path[-53:]))
		main_frame.canvas.update()
		print("You have entered the following file path: {}".format(str(open_file_path)))
	else:
		open_file_path_entry.delete(0, tk.END)
		open_file_path_entry.insert(0, "No valid file selected")
		print("Please select a valid file ('.lsm' file as input)!")
	open_file_path_entry["state"] = tk.DISABLED

def get_output_directory():
	global save_directory_path_entry, save_file_path
	if save_file_path and os.path.isdir(save_file_path):
		output_var.set(str("..." + save_file_path[-60:]))
		main_frame.canvas.update()
		print("You have entered the following output directory: {}".format(str(save_file_path)))
	else:
		save_directory_path_entry.delete(0, tk.END)
		save_directory_path_entry.insert(0, "No valid directory selected")
		print("Please enter a valid directory (to write output to)!")
	save_directory_path_entry["state"] = tk.DISABLED

# get an image number for preview and analysis (i.e. masking the movie)
preview_im_no = tk.IntVar()
preview_im_no.set(1) # default value is 1

analysis_im_no = tk.IntVar()
analysis_im_no.set(1) # default value is 1 as well

def get_preview_im_number(event):
	print("Image number {} will be previewed.".format(preview_im_no_entry.get()))
	preview_im_no.set(preview_im_no_entry.get())	
	event.widget["state"] = tk.DISABLED

def get_analysis_im_number(event):
	print("Image number {} will be used to identify cells.".format(analysis_im_no_entry.get()))
	analysis_im_no.set(analysis_im_no_entry.get())	
	event.widget["state"] = tk.DISABLED

# get two cutoffs for preview
cutoff1_var = tk.IntVar()
cutoff2_var = tk.IntVar()
cutoff_analysis = tk.IntVar()
cutoff1_var.set(30)
cutoff2_var.set(60)
cutoff_analysis.set(10)

def get_cutoff1_prev(event):
	print("A grey scale value cutoff of {} (cutoff 1) will be used for preview.".format(preview_cutoff1_entry.get()))
	cutoff1_var.set(preview_cutoff1_entry.get())
	event.widget["state"] = tk.DISABLED

def get_cutoff2_prev(event):
	print("A grey scale value cutoff of {} (cutoff 2) will be used for preview.".format(preview_cutoff2_entry.get()))
	cutoff2_var.set(preview_cutoff2_entry.get())
	event.widget["state"] = tk.DISABLED

def get_cutoff_analysis(event):
	"Body"

# get min and max cell sizes (in pixels)
min_cell_size = tk.IntVar()
max_cell_size = tk.IntVar()
min_cell_size.set(100)
max_cell_size.set(10000)

def get_min_size(event):
	"Body"

def get_max_size(event):
	"Body"

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
filemenu.add_command(label="Open...", command=pressed_open_filemenu)
filemenu.add_command(label="Save Directory", command=pressed_save_filemenu)
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

analysismenu.add_command(label="Preview Filter Settings", command=pressed_prepro_preview)
analysismenu.add_command(label="Find cells...", command=pressed_find_cells)
analysismenu.add_command(label="Analyze...", command=pressed_analyze)

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

###############
## Section 1 ##
###############
# file path and directory path entry widgets
open_file_path_entry = tk.Entry(main_frame.canvas, width=35, font="Arial 18 italic", highlightbackground=background_color)
open_file_path_entry.delete(0, tk.END)
open_file_path_entry.insert(0, "No file path entered...")
main_frame.canvas.create_window(15, 115, window=open_file_path_entry, anchor=tk.NW)

save_directory_path_entry = tk.Entry(main_frame.canvas, width=35, font="Arial 18 italic", highlightbackground=background_color2)
save_directory_path_entry.delete(0, tk.END)
save_directory_path_entry.insert(0, "No directory specified...")
main_frame.canvas.create_window(440, 115, window=save_directory_path_entry, anchor=tk.NW)

# add some explanatory text
main_frame.canvas.create_text(20, 85, text="Please enter a data file:", font="Arial 18", anchor=tk.NW)
main_frame.canvas.create_text(445, 85, text="Please enter an output directory:", font="Arial 18", anchor=tk.NW)

## creates buttons to get input file path and output directories
# create two buttons to "log" files/directories in
input_file_button = tk.Button(main_frame.canvas, width=8, text="Select File", font="Arial 14", command=get_input_file_path,
							  highlightbackground=background_color)
main_frame.canvas.create_window(15, 155, window=input_file_button, anchor=tk.NW)

output_directory_button = tk.Button(main_frame.canvas, width=12, text="Select Directory", font="Arial 14", command=get_output_directory,
									highlightbackground=background_color2)
main_frame.canvas.create_window(440, 155, window=output_directory_button, anchor=tk.NW)

# creates labels to show which files/directories are "logged in"
input_var = tk.StringVar()
input_var.set("Please select a file.")
input_label = tk.Label(main_frame.canvas, textvariable=input_var, font="Arial 10 italic", bg=background_color)
main_frame.canvas.create_window(115, 161, window=input_label, anchor=tk.NW)

output_var = tk.StringVar()
output_var.set("Please select a directory.")
output_label = tk.Label(main_frame.canvas, textvariable=output_var, font="Arial 10 italic", bg=background_color2)
main_frame.canvas.create_window(570, 161, window=output_label, anchor=tk.NW)

###############
## Section 2 ##
###############
## Preview Settings
main_frame.canvas.create_text(115, 220, text="Image Preview Settings:", font="Arial 18")

# Preview image number
main_frame.canvas.create_text(128, 260, text="** Preview Image Number  ---", font="Arial 14 italic")

preview_im_no_entry = tk.Entry(main_frame.canvas, width=5, font="Arial 14 italic", highlightbackground=background_color)
preview_im_no_entry.delete(0, tk.END)
preview_im_no_entry.insert(0, str(preview_im_no.get()))
preview_im_no_entry.bind("<Return>", get_preview_im_number)
preview_im_no_entry.bind("<Button-1>", activateEntryField)
main_frame.canvas.create_window(228, 246, window=preview_im_no_entry, anchor=tk.NW)

# apply two cutoffs
main_frame.canvas.create_text(100, 300, text="** Filter 1 (0-255)  ---", font="Arial 14 italic")
preview_cutoff1_entry = tk.Entry(main_frame.canvas, width=4, font="Arial 14 italic", highlightbackground=background_color)
preview_cutoff1_entry.delete(0, tk.END)
preview_cutoff1_entry.insert(0, str(cutoff1_var.get()))
preview_cutoff1_entry.bind("<Return>", get_cutoff1_prev)
preview_cutoff1_entry.bind("<Button-1>", activateEntryField)
main_frame.canvas.create_window(172, 286, window=preview_cutoff1_entry, anchor=tk.NW)

main_frame.canvas.create_text(300, 300, text="** Filter 2 (0-255)  ---", font="Arial 14 italic")
preview_cutoff2_entry = tk.Entry(main_frame.canvas, width=4, font="Arial 14 italic", highlightbackground=background_color)
preview_cutoff2_entry.delete(0, tk.END)
preview_cutoff2_entry.insert(0, str(cutoff2_var.get()))
preview_cutoff2_entry.bind("<Return>", get_cutoff2_prev)
preview_cutoff2_entry.bind("<Button-1>", activateEntryField)
main_frame.canvas.create_window(372, 286, window=preview_cutoff2_entry, anchor=tk.NW)

# add button to start preprocessing/preview (linked to same function as drop down menu)
prepro_preview_button = tk.Button(main_frame.canvas, width=12, text="Preview Filters", font="Arial 18", 
								  highlightbackground=background_color, command=pressed_prepro_preview)
main_frame.canvas.create_window(30, 330, window=prepro_preview_button, anchor=tk.NW)

## Analysis Settings
main_frame.canvas.create_text(115, 410, text="Image Analysis Settings:", font="Arial 18")

# Analyze image number
main_frame.canvas.create_text(160, 450, text="** Identify Cells in Image Number  ---", font="Arial 14 italic")

analysis_im_no_entry = tk.Entry(main_frame.canvas, width=5, font="Arial 14 italic", highlightbackground=background_color)
analysis_im_no_entry.delete(0, tk.END)
analysis_im_no_entry.insert(0, str(analysis_im_no.get()))
analysis_im_no_entry.bind("<Return>", get_analysis_im_number)
analysis_im_no_entry.bind("<Button-1>", activateEntryField)
main_frame.canvas.create_window(280, 436, window=analysis_im_no_entry, anchor=tk.NW)

## button callbacks and bindings
# list all buttons for callback effects (buttonPressed)!
button_list = [input_file_button, output_directory_button]
input_file_button.bind("<Button-1>", buttonPressed)
output_directory_button.bind("<Button-1>", buttonPressed)

## bind entries and buttons to corresponding events
# open file path entry field
open_file_path_entry.bind("<Button-1>", file_entries_callback1)

# save directory entry field
save_directory_path_entry.bind("<Button-1>", file_entries_callback2)



##########################
#### Tkinter mainloop ####
##########################
# start tkinter main loop and make sure that the window comes to the front after starting the app
# another solution: $root.lift() $root.attributes('-topmost',True) $root.after_idle(root.attributes,'-topmost',False)
os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
root.mainloop()
