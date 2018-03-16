'''
HELPER FUNCTIONS AND CLASSES! CalciumImagingAnalyzer App
developed by Daniel (d.schuette@online.de)
latest version: v0.03 (as of 03/10/2018)
-> runs with python 2.7.14 and with python 3.6.x
repository: https://github.com/DanielSchuette/CalciumImagingAnalyzer.git
'''
current_app_version = "v0.04"
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
else:  
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
import os, errno

#######################################
#### FigureCanvas Class Definition ####
#######################################

class scrollableFigure():
	'''
	scrollableFigure can display scrollable figures within a master canvas (usually a toplevel or frame widget). 
	Possible parameters are 'figure', 'master', *args and **kwargs (to configure canvas; does not inherit from anything!).
	'''
	def __init__(self, figure, master, *args, **kwargs):
		# put a figure into a master window 
		self.createScrollableFigure(figure=figure, master=master, *args, **kwargs)

	def createScrollableFigure(self, figure, master, *args, **kwargs):
		# create a canvas within the popup window
		popup_canvas = tk.Canvas(master, *args, **kwargs)
		popup_canvas.grid(row=0, column=0, sticky=tk.NSEW)

		# set up scrollbars
		xScrollbar = tk.Scrollbar(master, orient=tk.HORIZONTAL)
		yScrollbar = tk.Scrollbar(master, orient=tk.VERTICAL)
		xScrollbar.grid(row=1, column=0, sticky=tk.EW)
		yScrollbar.grid(row=0, column=1, sticky=tk.NS)

		popup_canvas.config(xscrollcommand=xScrollbar.set)
		xScrollbar.config(command=popup_canvas.xview)
		popup_canvas.config(yscrollcommand=yScrollbar.set)
		yScrollbar.config(command=popup_canvas.yview)

		# add a size grip
		sizegrip = ttk.Sizegrip(popup_canvas)
		sizegrip.grid(in_=yScrollbar, column=1, sticky=tk.SE)

		# plug in the figure
		figure_agg = FigureCanvasTkAgg(figure, popup_canvas)
		figure_canvas = figure_agg.get_tk_widget()
		figure_canvas.grid(sticky=tk.NSEW)

		# lastly, connect figure with scrolling region
		popup_canvas.create_window(0, 0, window=figure_canvas)
		popup_canvas.config(scrollregion=popup_canvas.bbox(tk.ALL))

##########################################
#### ScrollableFrame Class Definition ####
##########################################
class scrollableFrame(ttk.Frame):
	'''
	scrollableFrame inherits from ttk.Frame and can be used to create a scrollable frame in the root window. 
	'''
	def __init__(self, parent, *args, **kwargs):
		ttk.Frame.__init__(self, parent, *args, **kwargs)

		# create a vertical scrollbar
		vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
		vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=False)

		# create a horizontal scrollbar
		hscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
		hscrollbar.pack(fill=tk.X, side=tk.BOTTOM, expand=False)

		# add a size grip
		sizegrip = ttk.Sizegrip(self)
		sizegrip.pack(in_=vscrollbar, side=tk.BOTTOM)

		#Create a canvas object and associate the scrollbars with it
		self.canvas = tk.Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
		self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		#Associate scrollbars with canvas view
		vscrollbar.config(command=self.canvas.yview)
		hscrollbar.config(command=self.canvas.xview)

		# set the view to 0,0 at initialization
		self.canvas.xview_moveto(0)
		self.canvas.yview_moveto(0)

		# create an interior frame to be created inside the canvas     
		self.interior = ttk.Frame(self.canvas)
		interior = self.interior
		interior_id = self.canvas.create_window(0, 0, window=interior, anchor=tk.NW)

		# track changes to the canvas and frame width and sync them,
		# also updating the scrollbar

		def _configure_interior(event):
			# update the scrollbars to match the size of the inner frame
			size = (max(925, interior.winfo_reqwidth()), max(825, interior.winfo_reqheight()))
			self.canvas.config(scrollregion='0 0 %s %s' % size)
			if interior.winfo_reqwidth() != self.canvas.winfo_width():
				# update the canvas's width to fit the inner frame
				self.canvas.config(width=interior.winfo_reqwidth())
		interior.bind('<Configure>', _configure_interior)


################################################
#### ScrollablePopupWindow Class Definition ####
################################################
class PopupWindow(tk.Toplevel):
	'''
	This is a popup window. It's main purpose is to put ScrollableFigureCanvas objects inside!
	Possible parameters are 'master', 'title', *args, **kwargs (inherits from tk.Toplevel).
	'''
	def __init__(self, master, title="", *args, **kwargs):
		# initialize a toplevel widget (basically a popup window!)
		tk.Toplevel.__init__(self, master, *args, **kwargs)
		# configure popup window
		self.title(title)
		self.focus_force()
				
		# return a popup window 
		self.returnPopup()

	def returnPopup(self):
		self.columnconfigure(0, weight=1) # a figure will not resize if this option is not specified!
		self.rowconfigure(0, weight=1) # a figure will not resize if this option is not specified!
		return(self)
        
####################################
#### GUI popup window functions ####
####################################
# help page and about page - popup windows
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

# helpful placeholder function
def place_holder(): 
	"nothing"

#############################
#### Analysis Function 1 ####
#############################

def preprocessingFunction(
	create_new_directories=False, write_tiff=False, write_entire_movie=False, write_selected_file=False,
	i=1, cutoff1=40, cutoff2=60, figure_size=(9, 9), file_path=False # rename i!!
	):
	''' 
	Analysis function 1 Doc String: Explore different filters / data pre-processing
	The following code reads a .lsm file (maybe batches in a future version) and
	analyses them. This includes a plot of useful statistics.
	''' 
	# disable popup windows (also no plt.show("hold") otherwise tkinter won't show the figure in canvas1)
	matplotlib.interactive(False)

	# read in .lsm data and return a numpy array with certain dimensions: 
	if file_path != False:
		try:
			image = tiff.imread(file_path)
			print("You successfully imported a .lsm file from:" + "\n" + str(file_path) + "." + "\n")
			print("Image dimensions: " + str(image.shape) + "\n") # [1, 1, no_of_pictures, height, width]
			np.amax(image) # max value of 255; that needs to be transformed to range(0, 1)
			selected_image = (image[0, 0, (i-1), 0:512, 0:512])
		except Exception as error:
			raise error
	else:
		print("Specify a .lsm file to upload!")	
		return(False)	

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
	print("The plotted image is of " + str(type(selected_image)) + " and a " + str(selected_image.dtype) + " with dimensions " + str(selected_image.shape) + "." + "\n")

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
	ax1.set_title("Image {} of {}".format(str(i), str(image.shape[2])))

	# create a contour figure that extracts prominent features (origin upper left corner)
	ax2.contour(selected_image, origin="image", cmap="gray")
	ax2.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False) # Hide the axis but leave the spine
	ax2.set_title("Feature Extraction without\nPrior Background Reduction")

	# analyze the effect of masking certain pixel values from the image:
	# first, a boxplot helps to see the distribution of pixel values
	ax3.hist(selected_image.ravel(), bins=256, range=(0.0, 256.0), fc="k", ec="k")
	ax3.set_yscale("log", nonposy = "clip")
	ax3.set_title("Histogram of Gray Scale\nValues in Image {}".format(str(i)))
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

	return(fig)
		
#############################
#### Analysis Function 2 ####
#############################

def compute_image_convolution(image, kernel_size=(3, 3)):
	'''
	Analysis function 2 Doc String: This functions takes a numpy array as an input and computes a convolution
	using the keras interface. It does take Kernel size as an additional adjustable parameter.
	'''
	print(kernel_size[0])
	model = keras.Sequential()
	model.add(layers.Convolution2D(filters=3, kernel_size=kernel_size, input_shape=image.shape, 
		strides=(1, 1), padding='valid', data_format=None, dilation_rate=(1, 1), activation=None, use_bias=True, 
		kernel_initializer='glorot_uniform', bias_initializer='zeros', kernel_regularizer=None, bias_regularizer=None, 
		activity_regularizer=None, kernel_constraint=None, bias_constraint=None))
	
	# keras expects batches of images so the one image has to be expanded to get the behavior we want
	image_pseudo_batch = np.expand_dims(image, axis=0)
	conv_image = model.predict(image_pseudo_batch)

	def visualize_image(conv_batch):
		image_for_print = np.squeeze(conv_batch, axis=0)
		print("The image shape was re-transformed from {batch} to {single}.".image(batch=image_pseudo_batch, single=image_for_print))
		plt.imshow(image_for_print)











