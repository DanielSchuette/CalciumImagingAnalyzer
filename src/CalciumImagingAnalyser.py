'''
developed by Daniel (d.schuette@online.de)
This is a .app for the analysis of calcium imaging results
latest version: v0.02 (as of 03/08/2018)
-> runs with python 2.7.14 and not with python 3.6.x
repository: https://github.com/DanielSchuette/AppsInDev.git
'''
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
import os
import errno

''' 
--> module 1: analysis workflow 
The following code reads a .lsm file (maybe batches in a future version) and
analyses them. This includes a plot of useful statistics.

--> module 2: grafical user interface to interact with the app 
A tkinter GUI makes it possible to manually adjust certain parameters.
''' 
##############################
#### Adjustable Variables ####
##############################

# whether to write tiffs for inspection to a "tiffs/" directory:
current_app_version = "v0.02"
create_new_directories = False
write_tiff = False
write_entire_movie = False
write_selected_file = False

# another set of adjustable variables is required for variable plotting:
i = 286 # select the i`th image of the movie (0-indexed!)
cutoff1 = 40 # cutoff value 1 for deleting background pixels
cutoff2 = 60 # cutoff value 2 for deleting background pixels

# specify the file path of a .lsm file that should be analyzed
file_path = "../../Yale/Projects/calcium_imaging/20180125_20180213/20180125_SKHep_1.lsm"

# specify figure size and GUI size
figure_size = (9, 9)
gui_size = dict(width=1000, height=1000)

#######################################
#### FigureCanvas Class Definition ####
#######################################
class FigureCanvas(tk.Frame):
	'''
	FigureCanvas is a canvas that can show figures. It inherits from tk.Frame.
	'''
	def __init__(self, figure, master, show=True):
		tk.Frame.__init__(self, master)
		self.createWidgets(figure, show)

	def createWidgets(self, figure, show):
		canvas = FigureCanvasTkAgg(figure, master=root)
		if show:
			canvas.get_tk_widget().grid(row=0, column=1)
			canvas.show() # .draw also works


####################
#### Set GUI up ####
####################

## GUI functions and classes

# include a message box to ask if user wants to quit/restart (via window manager or drop down menu) 
def callback_when_quit():
    if tkMessageBox.askokcancel("Quit", "Do you really want to quit?\nAll unsaved progress will be lost..."):
        root.destroy()
        sys.exit(0)

def callback_when_restart(): #Restarts the current program.
    if tkMessageBox.askokcancel("Restart", "Do you really want to restart?\nAll unsaved progress will be lost..."):
    	python = sys.executable
    	os.execl(python, python, * sys.argv)

# help and about popup windows
helptext = "This is a helpful text."

abouttext = "Copyright, Disclaimer, Version, GitHub."

def open_help_popup():
	if sys.version_info[0] < 3:
		tkMessageBox.showinfo("Help", helptext)
	else:
		messagebox.showinfo("Help", helptext)

def open_about_popup():
	if sys.version_info[0] < 3:
		tkMessageBox.showinfo("About", abouttext)
	else:
		messagebox.showinfo("About", abouttext)

# functions defining actions of analysis buttons
def pressed_preview():
	# display figure in GUI window using the 'draw_figure()' function
	figure_1 = FigureCanvas(figure=fig, master=root, show=True)
	print("A figure should show up!")

def pressed_analyze():
	"nothing"

# make a popup window appear if a button is pressed (needs to be completed!)
class ScrollablePopupWindow():
	'''
	This is a scrollable popup window.
	'''
	def __init__(self, arg):
		self.arg = arg
		clickAbout(arg)

	def clickAbout(arg):
		toplevel = tk.Toplevel()
		label1 = tk.Label(toplevel, text=ARGUMENT1, height=0, width=100)
		label1.pack()
		label2 = tk.Label(toplevel, text=ARGUMENT2, height=0, width=100)
		label2.pack()
		toplevel.focus_force()

## set up window
root = tk.Tk()
root.title("Calcium Imaging Analyzer {}".format(current_app_version))
root.config(**gui_size)

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

def place_holder(): # temporary helper function
	"nothing"

# ... and add a file menu,
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open ...", command=place_holder)
filemenu.add_command(label="Save as...", command=place_holder)
filemenu.add_separator()
filemenu.add_command(label="Restart", command=callback_when_restart)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=callback_when_quit)

# ... a help menu,
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help", command=open_help_popup)
helpmenu.add_command(label="About...", command=open_about_popup)

# ... and an analysis menu.
analysismenu = tk.Menu(menubar, tearoff=1)
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

########################
#### Analysis Start ####
########################
print("\n" + "********************************" + "\n")
print("Calcium Imaging Analyzer {}".format(current_app_version))
print("\n" + "********************************" + "\n")

# disable popup windows (also no plt.show("hold") otherwise tkinter won't show the figure in canvas1)
matplotlib.interactive(False)

# read in .lsm data and return a numpy array with certain dimensions: 
image = tiff.imread(file_path)
print("You successfully imported a .lsm file from:" + "\n" + str(file_path) + "." + "\n")
print("Image dimensions: " + str(image.shape) + "\n") # [1, 1, no_of_pictures, height, width]
np.amax(image) # max value of 255; that needs to be transformed to range(0, 1)

selected_image = (image[0, 0, i, 0:512, 0:512])

# if user has no permission to create a new folder, an error will be raised:
# https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist

if create_new_directories: 
	'''
	make sure to delete the if statement prior to production! otherwise the app will not run bug-free
	if users select to not create new directories but to write tiffs, results, figures to them!
	'''
	if not os.path.exists("tiffs/"):
		try: 
			os.makedirs("tiffs/")
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise "Could not create a 'tiffs/' folder!"
	if not os.path.exists("figures/"):
		try: 
			os.makedirs("figures/")
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise "Could not create a 'figures/' folder!"
	if not os.path.exists("results/"):
		try: 
			os.makedirs("results/")
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise "Could not create a 'results/' folder!"						

if write_tiff:
	if write_entire_movie:	
		tiff.imsave("{}.tif".format("tiffs/entire_file"), image) # allows to save entire .lsm 'movie' as a .tiff
	if write_selected_file:
		tiff.imsave("{}.tif".format("tiffs/selected_image"), selected_image) # allows to save first image of .lsm file as a .tiff
	print(".tif files written to {}/{}!".format(str(os.getcwd()), "tiffs/") + "\n")
else:
	print("No .tif files written to {}/{}!".format(str(os.getcwd()), "tiffs/") + "\n")

# check image dimensions before plotting
print("The plotted image is of " + str(type(selected_image)) + " and a " + str(selected_image.dtype) 
	  + " with dimensions " + str(selected_image.shape) + "." + "\n")

# plot your image (use .set_action methods for axes!)
fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(nrows=2, ncols=3, figsize=figure_size)
fig.canvas.set_window_title("Figure of {}".format(str(file_path)))
fig.subplots_adjust(wspace=0.2, hspace=0.2, right=0.98, left=0.10, bottom=0.07, top=0.93)

# subplot (1, 1)
ax1.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
im1 = ax1.imshow(selected_image, cmap="viridis", interpolation="bicubic") 
# colormaps "jet", "gray, "viridis" work
# "bicubic" interpolation smoothes the edges, "nearest" leads to a more pixelated figure
colbar_ax = fig.add_axes([0.02, 0.57, 0.035, 0.33]) 
# Add axes for colorbar at [left, bottom, width, height] (quantities are in fractions of figure)
fig.colorbar(im1, cax=colbar_ax)
ax1.set_title("Image {} of {}".format(str(i + 1), str(image.shape[2])))

# create a contour figure that extracts prominent features (origin upper left corner)
ax2.contour(selected_image, origin="image", cmap="gray")
ax2.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False) # Hide the axis but leave the spine
ax2.set_title("Feature Extraction without\nPrior Background Reduction")

# analyze the effect of masking certain pixel values from the image:
# first, a boxplot helps to see the distribution of pixel values
ax3.hist(selected_image.ravel(), bins=256, range=(0.0, 256.0), fc="k", ec="k")
ax3.set_yscale("log", nonposy = "clip")
ax3.set_title("Histogram of Gray Scale\nValues in Image {}".format(str(i + 1)))
ax3.tick_params(width=1.5, which="both", labelsize=12)
ax3.axvline(x=cutoff1, color="darkred", linewidth=3, linestyle='--')
ax3.axvline(x=cutoff2, color="darkblue", linewidth=3, linestyle='--')
ax3.legend(["Cutoff 1 = {}".format(str(cutoff1)), "Cutoff 2 = {}".format(str(cutoff2))], loc="upper right")

# second, a scatter plot demonstrating the number of pixels below certain cutoff
pixel_values = []
cutoffs = []

tmp1 = np.copy(selected_image) # --> assignment statements in python do NOT copy objects but create binding
for cutoff in range(selected_image.max()):
	mask = tmp1 < cutoff
	tmp1[mask] = 0
	pixel_values.append(pylab.mean(mask) * 100)
	cutoffs.append(cutoff)

# create another subplot where subplot '4' would usually be and plot scatter plot with y axis break
# also, determine optimal break point for the upper panel ax4_1 using the second smallest pixel value
y_limits_top = (pixel_values[1] - 2, 102) 
y_limits_bottom = (-0.5, 2) 

ax4_1 = plt.subplot2grid((6, 3), (3, 0), rowspan=2) # 0-indexed!
ax4_2 = plt.subplot(6, 3, 16)
ax4_1.scatter(x=cutoffs, y=pixel_values, s=20, c="darkred")
ax4_1.set_title("% of Pixels Below Gray Scale Cutoff")
ax4_1.tick_params(width=1.5, labelsize=12)
ax4_1.set_ylim(y_limits_top)
ax4_1.axvline(x=cutoff1, color="darkred", linewidth=3, linestyle='--')
ax4_1.axvline(x=cutoff2, color="darkblue", linewidth=3, linestyle='--')
ax4_1.tick_params(bottom = False, labelbottom = False)

ax4_2.scatter(x=cutoffs, y=pixel_values, s=20, c="darkred")
ax4_2.tick_params(width=1.5, labelsize=12)
ax4_2.set_ylim(y_limits_bottom)
ax4_2.set_xlabel("Gray Scale Value Cutoff")
ax4_2.axvline(x=cutoff1, color="darkred", linewidth=3, linestyle='--')
ax4_2.axvline(x=cutoff2, color="darkblue", linewidth=3, linestyle='--')
ax4_2.legend(["Cutoff 1 = {}".format(str(cutoff1)), "Cutoff 2 = {}".format(str(cutoff2))], loc="lower right")

# hide spines:
ax4_1.spines["bottom"].set_visible(False)
ax4_2.spines["top"].set_visible(False)

# unfortunately the y label is not centered...
ax4_1.set_ylabel("Percentage of Pixels Below Cutoff")

# add diagonal 'break' lines
d = .025  # size of diagonal lines in axes coordinates
# arguments to pass to plot, just so we don't keep repeating them
kwargs = dict(transform=ax4_1.transAxes, color="black", clip_on=False, lw=3)
ax4_1.plot((-d, +d), (0, 0), **kwargs)        # top-left diagonal
ax4_1.plot((1 - d, 1 + d), (0, 0), **kwargs)  # top-right diagonal
kwargs.update(transform=ax4_2.transAxes)  # switch to the bottom axes
ax4_2.plot((-d, +d), (1,  1), **kwargs)  # bottom-left diagonal
ax4_2.plot((1 - d, 1 + d), (1, 1), **kwargs)  # bottom-right diagonal

# mask different gray scale values from the image
tmp2 = np.copy(selected_image)
tmp2[tmp2 < cutoff1] = 0

ax5.contour(tmp2, origin="image", cmap="gray")
ax5.set_title("Gray Scale Cutoff = {}".format(str(cutoff1)))
ax5.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)

tmp3 = np.copy(selected_image)
tmp3[tmp3 < cutoff2] = 0

ax6.contour(tmp3, origin="image", cmap="gray")
ax6.set_title("Gray Scale Cutoff = {}".format(str(cutoff2)))
ax6.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)

# change width of spine and spine color for some of the subplots
subplots_list = [ax1, ax2, ax3, ax4_1, ax4_2, ax5, ax5, ax6]

for axis in subplots_list:
	[i.set_linewidth(2) for i in axis.spines.values()]	
######################
#### Analysis End ####
######################

##########################
#### Tkinter mainloop ####
##########################

# start tkinter main loop and make sure that the window comes to the front after starting the app
# another solution: $root.lift() $root.attributes('-topmost',True) $root.after_idle(root.attributes,'-topmost',False)
os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
root.mainloop()

#####################
#### Program End ####
#####################