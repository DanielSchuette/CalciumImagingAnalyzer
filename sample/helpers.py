'''
HELPER FUNCTIONS AND CLASSES! CalciumImagingAnalyzer App
developed by Daniel (d.schuette@online.de)
-> runs with python 2.7.14 and python 3.6.x on macOS High Sierra
repository: https://github.com/DanielSchuette/CalciumImagingAnalyzer.git
'''
current_app_version = "v0.2"
#####################################
#### Import All Required Modules ####
#####################################
import warnings, timeit
from datetime import datetime
with warnings.catch_warnings(): # suppresses keras' annoying numpy warning
    warnings.simplefilter("ignore")
    import keras
    from keras import layers
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
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
os.environ["TF_CPP_MIN_LOG_LEVEL"] = '2'
from skimage import measure
from skimage import filters
from skimage.feature import canny
from scipy import ndimage as ndi
from skimage.filters import sobel
from skimage.morphology import watershed

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

	## bind mousepad scroll events to window scrolling
	# two callback functions to handle "swiping" with mousepad
	def scroll_vertical_pop(self, event):
		self.popup_canvas.yview_scroll(-1 * event.delta, 'units')

	def scroll_horizontal_pop(self, event):
		self.popup_canvas.xview_scroll(-1 * event.delta, 'units')

	def createScrollableFigure(self, figure, master, *args, **kwargs):
		# create a canvas within the popup window
		self.popup_canvas = tk.Canvas(master, *args, **kwargs)
		self.popup_canvas.grid(row=0, column=0, sticky=tk.NSEW)

		# set up scrollbars
		xScrollbar = tk.Scrollbar(master, orient=tk.HORIZONTAL)
		yScrollbar = tk.Scrollbar(master, orient=tk.VERTICAL)
		xScrollbar.grid(row=1, column=0, sticky=tk.EW)
		yScrollbar.grid(row=0, column=1, sticky=tk.NS)

		self.popup_canvas.config(xscrollcommand=xScrollbar.set)
		xScrollbar.config(command=self.popup_canvas.xview)
		self.popup_canvas.config(yscrollcommand=yScrollbar.set)
		yScrollbar.config(command=self.popup_canvas.yview)

		# add a size grip
		sizegrip = ttk.Sizegrip(master)
		sizegrip.grid(row=1, column=1, sticky=tk.SE)
		
		# plug in the figure
		figure_agg = FigureCanvasTkAgg(figure, self.popup_canvas)
		figure_canvas = figure_agg.get_tk_widget()
		figure_canvas.grid(sticky=tk.NSEW)

		self.popup_canvas.bind('<MouseWheel>', self.scroll_vertical_pop) # probably just the figure-canvas needs to be bound
		self.popup_canvas.bind('<Shift-MouseWheel>', self.scroll_horizontal_pop)

		figure_canvas.bind('<MouseWheel>', self.scroll_vertical_pop)
		figure_canvas.bind('<Shift-MouseWheel>', self.scroll_horizontal_pop)

		# lastly, connect figure with scrolling region
		self.popup_canvas.create_window(0, 0, window=figure_canvas)
		self.popup_canvas.config(scrollregion=self.popup_canvas.bbox(tk.ALL))

##########################################
#### ScrollableFrame Class Definition ####
##########################################
class scrollableFrame(ttk.Frame):
	'''
	scrollableFrame inherits from ttk.Frame and can be used to create a scrollable frame in the root window. 
	'''
	# two callback functions to handle "swiping" with mousepad
	def scroll_vertical(self, event):
		self.canvas.yview_scroll(-1 * event.delta, 'units')

	def scroll_horizontal(self, event):
		self.canvas.xview_scroll(-1 * event.delta, 'units')

    # class __init__ method	
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
		
		# bind mousepad scroll events to window scrolling
		self.canvas.bind('<MouseWheel>', self.scroll_vertical)
		self.canvas.bind('<Shift-MouseWheel>', self.scroll_horizontal)

		# create an interior frame to be created inside the canvas     
		self.interior = ttk.Frame(self.canvas)
		interior = self.interior
		interior_id = self.canvas.create_window(0, 0, window=interior, anchor=tk.NW)

		# track changes to the canvas and frame width and sync them,
		# also updating the scrollbar

		def _configure_interior(event):
			# update the scrollbars to match the size of the inner frame
			size = (max(925, interior.winfo_reqwidth()), max(760, interior.winfo_reqheight()))
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
		self.protocol("WM_DELETE_WINDOW", self.destroy)
				
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
helptext = """Please refer to the README file accompanying the GitHub repository or this software at:
git@github.com:DanielSchuette/CalciumImagingAnalyzer.git"""

abouttext = """MIT License

Copyright (c) 2018 Daniel Schuette

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

GitHub Repository: git@github.com:DanielSchuette/CalciumImagingAnalyzer.git
"""

def open_help_popup():
	if sys.version_info[0] < 3:
		tkMessageBox.showinfo("Help", helptext)
	else:
		messagebox.showinfo("Help", helptext)

def open_about_popup(master):
	about_window = PopupWindow(master)
	about_window.title("About")
	about_window.minsize(300, 250)
	about_window.maxsize(600, 400)

	# add a text widget
	about_text = tk.Text(about_window, height=15, width=80)
	about_text.pack(side=tk.LEFT, fill=tk.Y)

	# add a scrollbar
	scrollbar = tk.Scrollbar(about_window)
	scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	# configure scrollbar and text
	about_text.config(yscrollcommand=scrollbar.set)
	scrollbar.config(command=about_text.yview)

	# insert about text and disable widget afterwards
	about_text.insert(tk.END, abouttext)
	about_text.config(state=tk.DISABLED)

def create_new_directories(save_directory):
	'''
	This functions checks whether directories exist in specified 'save directory' to save output files to!
	'''
	if not os.path.exists("{}/tiffs/".format(save_directory)):
		try: 
			os.makedirs("{}/tiffs/".format(save_directory))
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise Exception("Could not create a 'tiffs/' folder!")
	if not os.path.exists("{}/figures/".format(save_directory)):
		try: 
			os.makedirs("{}/figures/".format(save_directory))
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise Exception("Could not create a 'figures/' folder!")
	if not os.path.exists("{}/results/".format(save_directory)):
		try: 
			os.makedirs("{}/results/".format(save_directory))
		except OSError as error:
			if error.errno != errno.EEXIST:
				raise Exception("Could not create a 'results/' folder!")

def save_tiffs(save_directory, image, save_tiff_checkbox):
	'''
	This function saves .tif images to a designated directory that was previously specified.
	'''
	if save_tiff_checkbox:
		try:
			tiff.imsave("{dir}/tiffs/{day}_{time}_{name}.tif".format(
				dir=save_directory, 
				day=datetime.now().strftime("%Y_%m_%d"), 
				time=datetime.now().strftime("%H.%M.%S"),
				name="analysis_input"), image)
			print("Image saved to: " + "{}/{}".format(save_directory, "tiffs"))
		except:
			print("You did not save a .tif! Check the specified save directory!")
	else:
		print("No .tif files written to {}/{}!".format(save_directory, "tiffs"))

def save_pdf(save_directory, figure, save_pdf_checkbox, name):
	'''
	This function saves .pdf images to a designated directory that was previously specified.
	'''
	if save_pdf_checkbox:
		try:
			figure.savefig("{dir}/figures/{day}_{time}_{name}.pdf".format(
				dir=save_directory, 
				day=datetime.now().strftime("%Y_%m_%d"), 
				time=datetime.now().strftime("%H.%M.%S"),
				name=name))
			print("Figure saved to: " + "{}/{}".format(save_directory, "figures"))
		except:
			print("You did not save a .pdf! Check the specified save directory!")
	else:
		print("No .pdf files written to {}/{}".format(save_directory, "figures"))


def save_txt(save_directory, matrix, save_txt_checkbox, name):
	'''
	This function saves .txt files to a designated directory that was previously specified.
	'''
	if save_txt_checkbox:
		try:
			np.savetxt("{dir}/results/{day}_{time}_{name}.txt".format(
				dir=save_directory, 
				day=datetime.now().strftime("%Y_%m_%d"), 
				time=datetime.now().strftime("%H.%M.%S"),
				name=name), matrix)
			print("Text file saved to: " + "{}/{}".format(save_directory, "results"))
		except:
			print("You did not save a .txt! Check the specified save directory!")
	else:
		print("No .txt files written to {}/{}".format(save_directory, "results"))

#############################
#### Analysis Function 1 ####
#############################

def preprocessingFunction(image_number, cutoff1, cutoff2, file_path, save_directory, save_tiff_checkbox, save_pdf_checkbox,
	figure_size=(9, 9)):
	''' 
	Analysis function 1 Doc String: Explore different filters / data pre-processing
	The following code reads a .lsm file (maybe batches in a future version) and
	analyses them. This includes a plot of useful statistics.
	''' 
	# disable popup windows (also no plt.show("hold") otherwise tkinter won't show the figure in canvas)
	matplotlib.interactive(False)

	# read in .lsm data and return a numpy array with certain dimensions: 
	if file_path and file_path.endswith(".lsm"):
		try:
			image = tiff.imread(file_path)
			print("You successfully imported a .lsm file from:" + "\n" + str(file_path) + ".")
			selected_image = (image[0, 0, (int(image_number)-1), 0:512, 0:512])
			print("You selected image number {}.".format(str(image_number)))
		except Exception as error: # raise exception if user has no permission to write in directory!
			raise error
	else:
		print("Specify a .lsm file to upload!")	
		return(False)	

	# create new directories for output files and save tiffs if checkbox is checked	
	create_new_directories(save_directory=save_directory)
	save_tiffs(save_directory=save_directory, image=image, save_tiff_checkbox=save_tiff_checkbox)
		
	# check image dimensions before plotting
	print("Image format is " +  str(selected_image.dtype) + " with dimensions " + str(selected_image.shape) + ".")

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
	ax1.set_title("Image {} of {}".format(str(image_number), str(image.shape[2])))

	# create a contour figure that extracts prominent features (origin upper left corner)
	ax2.contour(selected_image, origin="image", cmap="gray")
	ax2.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False) # Hide the axis but leave the spine
	ax2.set_title("Feature Extraction without\nPrior Background Reduction")

	# analyze the effect of masking certain pixel values from the image:
	# first, a boxplot helps to see the distribution of pixel values
	ax3.hist(selected_image.ravel(), bins=256, range=(0.0, 256.0), fc="k", ec="k")
	ax3.set_yscale("log", nonposy = "clip")
	ax3.set_title("Histogram of Gray Scale\nValues in Image {}".format(str(image_number)))
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

	# if the checkbox is checked, save figure as pdf
	save_pdf(save_directory=save_directory, figure=fig, save_pdf_checkbox=save_pdf_checkbox, name="exploratory_data_analysis")

	return(fig)
		
############################
#### Analysis 2 - Class ####
############################
# skimage help page (http://www.scipy-lectures.org/packages/scikit-image/auto_examples/plot_labels.html)
# also useful: https://stackoverflow.com/questions/46441893/connected-component-labeling-in-python
class ConnectedComponentsLabeling():
    '''
    ConnectedComponentsLabeling class can be used to analyze a gray scale image with respect to components it contains.
	'method' is 'ccl' by default but 'segmentation' via a watershed algorithm is also implementation
    '''
    def __init__(self, input_image, pixel_threshold=200, min_threshold=100, max_threshold=10000, skimage=True, fully_connected=True,
    			 method="ccl"):
        # monitor elapsed time
        timer_start = timeit.default_timer()
        
        # transform input image to binary image
        if method == "ccl":
        	self.im_ccl = self.transformToClusterImage(input_im=input_image, pixel_threshold=pixel_threshold, skimage=skimage, 
        										   	   fully_connected=fully_connected)
        elif method == "segmentation":
        	self.im_ccl = self.imageSegmentation(input_im=input_image, pixel_threshold=pixel_threshold)

        else:
        	raise ValueError("Enter a valid cell identification method! ('ccl', 'segmentation')")

        # find clusters in ccl image 
        print("Looking for cells...")
        self.clust_list = self.findClusterSize(input_im_ccl=self.im_ccl)
        print("Cells found!")

        # analyze cluster list "clust_list" with respect to size thresholds to find cluster indices for subsetting the original image
        print("Applying min/max size thresholds...")
        self.clust_index = self.findClusterIndex(input_list=self.clust_list, min_threshold=min_threshold, max_threshold=max_threshold)

        # lastly, subset the original image with indices and derive "cells" from those clusters
        self.im_with_cells = self.findCellsInClusters(input_im_ccl=self.im_ccl, cluster_index=self.clust_index)
        
        # end and print counter
        timer_end = timeit.default_timer()
        print("Done!")
        print("{} sec elapsed.".format(timer_end - timer_start))

    def CCL_algorithm(self, binary_image, fully_connected):
	'''
	!!!!!!!!!!!!!!
	ATTENTION: Does currently not work. No second-pass loop with 'union-find' implemented. Thus, labels are still a mess! Use
			   skimage's build-in function for connected components labeling!
	!!!!!!!!!!!!!!
	Connected components labeling algorithm. Takes a binary image (0, 1) as an input.
	'Fully_connected=boolean' defines whether to use 4- or 8-connectivity:
		# i = row index
		# j = column index
		### which positions to test ###
		###
		###	[i-1, j-1]  [i-1, j] [i-1, j+1]
		###	          \	  |	    /
		###	[i, j-1] - 	[i, j]
		###
	'''
	print("Start CCL algorithm.")

	# initialize an all-0 np.array and a counter
	cluster_counter = 0
	ccl_image = np.zeros(shape=binary_image.shape, dtype=np.int)

	# iterator over image (actual algorithm)
	for i in range(0, binary_image.shape[0]): 

		for j in range(0, binary_image.shape[1]): 
			
			# test elements
			if binary_image[i, j] == 1:
				## test all adjacent elements
				# -- 1 --
				if fully_connected and i != 0 and j != 0 and binary_image[i-1, j-1] == 1: 
					ccl_image[i, j] = ccl_image[i-1, j-1]
				# -- 2 --
				elif i != 0 and binary_image[i-1, j] == 1: 
					ccl_image[i, j] = ccl_image[i-1, j]
				# -- 3 --
				elif binary_image[i, j-1] == 1: 
					ccl_image[i, j] = ccl_image[i, j-1]
				# -- 4 --
				# test whether element is last in a row as well!
				elif fully_connected and j < (binary_image.shape[1]-1) and i != 0 and binary_image[i-1, j+1] == 1: 
					ccl_image[i, j] = ccl_image[i-1, j+1]
				
				# if none of them is a 'positive' neighbor, assign a new cluster number to the element
				else:
					cluster_counter += 1
					ccl_image[i, j] = cluster_counter

	return(ccl_image)
	'''
	The second half of the algorithm needs to be implemented if you want to use this self-made function for CCL!
    '''
    
    def transformToClusterImage(self, input_im, pixel_threshold, skimage, fully_connected):
        '''
        Transform input image to binary image and analyze with skimage's connected components labeling algorithm or with
        a home-made algorithm. Output is a np.array with same dimension as input image and cluster numbers as matrix elements.
        '''
        internal_copy = np.copy(input_im)
        internal_copy[internal_copy < pixel_threshold] = 0
        internal_copy[internal_copy != 0] = 1
        
        if skimage:
        	copy1_ccl = measure.label(internal_copy)
        else:
        	copy1_ccl = self.CCL_algorithm(internal_copy, fully_connected)
        
        return(copy1_ccl)

    def imageSegmentation(self, input_im, pixel_threshold):
		'''
		Might be more robust than CCL under certain circumstances. 
		Resource: http://scikit-image.org/docs/dev/user_guide/tutorial_segmentation.html
		'''

		markers = np.zeros_like(input_im)
		markers[input_im < pixel_threshold] = 1 # set pixel values to marker values depending on 'pixel_treshold'
		markers[input_im >= pixel_threshold] = 2
		elevation_map = sobel(input_im) # compute an elevation map

		segmentation = watershed(elevation_map, markers) # apply whatershed algorithm
		segmentation2 = ndi.binary_fill_holes(segmentation - 1) # fill small holes
		labeled_image, x = ndi.label(segmentation2) # label cells in image

		return(labeled_image)

    def findClusterSize(self, input_im_ccl):
        '''
        v0.15: np.unique() based algorithm finds clusters.
        ***************************
        DEPRECATED: Loops over "Connected components image" and finds clusters. A counter is integrated so that users can 
        approximate how long the analysis will take. Throws an error if number of clusters is very large.
        ***************************
        '''        
        # initialize counters, a list of clusters to append cluster size to, and loop over matrix elements to find clusters
        #cluster_list = list()
        #row_count, elem_count = 0, 0

        #for number in range(1, input_im_ccl.max()+1, 1):
        #    print("Evaluating cluster {number} of {max_number}.".format(number=number, max_number=input_im_ccl.max()))
        #    cluster_count = 0
        #    for row in input_im_ccl:
        #        for element in row:
        #            if element == number:
        #                cluster_count += 1
        #    cluster_list.append(cluster_count)

        # warning if input has a large number of clusters
        #if input_im_ccl.max() > 500:
        #    warnings.warn("Consider to reduce the number of potential cells that are evaluated by using a filter.", RuntimeWarning, 
        #                  stacklevel=2)

		# a faster alternative to looping over the matrix elements!
        unique_clusts, counts_clusts = np.unique(input_im_ccl, return_counts=True)
        cluster_list = list(counts_clusts)
        cluster_list.pop(0)
        
        # return list of cluster sizes
        return(cluster_list)

    def findClusterIndex(self, input_list, min_threshold, max_threshold):
        '''
        Finds indices of clusters.
        '''
        cluster_index = list()
        for element in input_list:
            if element >= min_threshold and element <= max_threshold:
                cluster_index.append(input_list.index(element)+1)

        if len(cluster_index) == 0:
        	raise ValueError("No cells in range {min} - {max}!".format(min=min_threshold, max=max_threshold))
        else:
        	return(cluster_index)

    def findCellsInClusters(self, input_im_ccl, cluster_index):
        '''
        Finds "cells" in clusters.
        '''
        # duplicate input image to make sure that it does not get changed during analysis
        input_im_ccl_2 = np.copy(input_im_ccl)

        # subset input image with cluster indices to delete background and identify actual cells
        for row in range(0, input_im_ccl_2.shape[0]):
            for col in range(0, input_im_ccl_2.shape[1]):
                if input_im_ccl_2[row, col] in set(cluster_index): # using a set considerably speeds up this step
                    input_im_ccl_2[row, col] = cluster_index.index(input_im_ccl_2[row, col]) + 1
                else:
                    input_im_ccl_2[row, col] = 0
        return(input_im_ccl_2)

############################
#### Analysis 3 - Class ####
############################
class AnalyzeSingleCells():
	'''
	To initialize an instance of this class, pass in a .lsm 'movie' and a mask in form of a 'ccl_object'.
	Start/stop defines the time span that should be used as baseline or for normalization.
	'''
	def __init__(self, input_movie, ccl_object, start, stop, method="mean", legend=True):
		'''
		Calls all class functions and ultimately returns a figure
		'''
		self.single_cell_traces = self.subsetWithCclObject(input_mov=input_movie, ccl_object=ccl_object, method=method)

		self.normalized_traces = self.NormalizeCellTraces(cell_traces=self.single_cell_traces, start=start, stop=stop)

		self.figure = self.PlotCellTraces(cell_traces=self.normalized_traces, legend=legend)
	

	def subsetWithCclObject(self, input_mov, ccl_object, method):
		# create a list to save all 'mean pixel value per cell over time' to
		clusters_list = list()
	
		# loop over all cells or clusters that were identified
		if method == "mean":
			for i in range(1, (ccl_object.im_with_cells.max()+1)):
				mask = (ccl_object.im_with_cells == i) # creates a mask for a particular cluster i
				cells_list = list() # create a list to save mean values to
				# loop over all images in movie and extract sum of pixel values for a particular cluster i	
				for j in range(0, input_mov.shape[2]):
					tmp_im = input_mov[0, 0, j, :, :]
					cells_list.append(np.mean(tmp_im[mask]))

				# append 'cells_list' to list of all clusters
				clusters_list.append(cells_list)

		elif method == "sum":
			for i in range(1, (ccl_object.im_with_cells.max()+1)):
				mask = (ccl_object.im_with_cells == i) # creates a mask for a particular cluster i
				cells_list = list() # create a list to save mean values to
				# loop over all images in movie and extract sum of pixel values for a particular cluster i	
				for j in range(0, input_mov.shape[2]):
					tmp_im = input_mov[0, 0, j, :, :]
					cells_list.append(np.sum(tmp_im[mask]))

				# append 'cells_list' to list of all clusters
				clusters_list.append(cells_list)		

		else:
			raise ValueError("Specify a valid method! ('mean', 'sum')")

		# return mean pixel values per cell in a list
		return(np.array(clusters_list))


	def NormalizeCellTraces(self, cell_traces, start, stop):
		'''
		Normalized calcium imaging data in form of an array. The mean of timepoints 'start' until 'stop' per row is used for 
		normalizing the rest of the respective row. Outputs an array as well.
		'''

		# create a new array of correct dimensions to store results in
		output_array = np.zeros(shape=cell_traces.shape, dtype=np.float)

		for i in range(cell_traces.shape[0]):
			output_array[i, :] = np.divide(cell_traces[i, :], np.mean(cell_traces[i, start:stop]))

		return(output_array)

	def PlotCellTraces(self, cell_traces, legend):
		'''
		Takes a np.array with one or multiple rows and plots it as a time course. Use normalized data with this function!
		'''
		# create a time scale for x axis
		time_scale = np.arange(1, (cell_traces.shape[1]+1))

		# set up a figure and a list to save legend labels to
		fig = plt.figure(figsize=(10,10))	
		legend_labels = list()

		# loop over rows in input np.array to plot all traces
		for i in range(cell_traces.shape[0]):
			plt.plot(time_scale, cell_traces[i, :]) 
			legend_labels.append("cell_{number}".format(number=i))

		# add a legend and return figure
		if legend:
			plt.legend(legend_labels, loc="upper left")
		plt.title("Single Cell Traces")
		plt.ylabel("F / F0 (Relative Fluorescence)")
		plt.xlabel("Time (Secs)")
		return(fig)

############################
#### Analysis 4 - Class ####
############################
class TransformAndFilter():
	'''
	This class implements methods for filtering and transforming time series data. It requires a time series object as an input.
	The class methods perform Fourier transform, Kalman filtering, and XXXX.
	'''
	def __init__(self, *args, **kwargs):
		pass








