# import matplotlib.pyplot as plt
# import matplotlib as mpl
# mpl.rcParams['figure.dpi'] = 150

import watershed_workflow
import watershed_workflow.ui
import logging
watershed_workflow.ui.setup_logging(1,None)

import numpy as np
import rasterio
import fiona
import watershed_workflow.daymet

import os,sys
import numpy as np
import pandas
from matplotlib import pyplot as plt
from matplotlib import cm as pcm
import logging
import pandas as pd
import geopandas as gpd
# import seaborn as sns
import shapely
import copy
import scipy
import datetime
import netCDF4 as nc

import watershed_workflow 
import watershed_workflow.source_list
import watershed_workflow.ui
import watershed_workflow.utils
import watershed_workflow.plot
import watershed_workflow.mesh
import watershed_workflow.condition
# import watershed_workflow.densify_rivers_hucs
# import watershed_workflow.create_river_mesh
watershed_workflow.ui.setup_logging(1,None)

# import pygeoutils as geoutils
# from pynhd import NLDI
import ipympl


sources = watershed_workflow.source_list.get_default_sources()
name = 'Neches' # name the domain, used in filenames, etc
hucs = ['1202'] # a list of HUCs to run
huc_level = None # if provided, an int setting the level at which to include HUC boundaries
crs = watershed_workflow.crs.daymet_crs()

# Get watershed boundary. This was defined from mesh_Neches_nhd.ipynb

path_watershed = '../data-processed/basin/complete_watershed_domain.shp'

watershed_neches = gpd.read_file(path_watershed)
_, watershed_neches=watershed_workflow.get_shapes(path_watershed,in_crs = watershed_neches.crs,out_crs = watershed_workflow.crs.daymet_crs())
# Get watershed in the right format
watershed = watershed_workflow.split_hucs.SplitHUCs(watershed_neches)
bounds = watershed.exterior().bounds


## Download data for 20 years of simulation
start = "1-2000"
end = "365-2020"
outputs = {}
outputs['daymet_filename'] = f'../../../global_data/rainfall_input_ATS/{name}/{name}_DayMet_2000_2020.h5'
dat, x, y = watershed_workflow.daymet.collectDaymet(bounds, crs, start, end)

# Save data into HD5 format
ats = watershed_workflow.daymet.daymetToATS(dat)
attrs = watershed_workflow.daymet.getAttrs(bounds, start, end)
watershed_workflow.daymet.writeHDF5(ats, x, y, attrs, outputs['daymet_filename'])

## Data for Spinup
# 1980-2020
start = "1-1980"
end = "365-2020"
outputs = {}
outputs['daymet_filename'] = f'../../../global_data/rainfall_input_ATS/{name}/{name}_DayMet_1980_2020.h5'
dat, x, y = watershed_workflow.daymet.collectDaymet(bounds, crs, start, end)

# Save data into HD5 format
ats = watershed_workflow.daymet.daymetToATS(dat)
attrs = watershed_workflow.daymet.getAttrs(bounds, start, end)
watershed_workflow.daymet.writeHDF5(ats, x, y, attrs, outputs['daymet_filename'])

# Daymet data for spinup

outputs['daymet_spinup_filename'] = f'../../../global_data/rainfall_input_ATS/{name}/{name}_DayMet_typical_1980_2020.h5'
ats_typ = watershed_workflow.daymet.daymetToATS(dat, smooth=True, smooth_filter=True, nyears=40)
watershed_workflow.daymet.writeHDF5(ats_typ, x, y, attrs, outputs['daymet_spinup_filename'])

# calculate the basin-averaged, annual-averaged precip rate
precip_total = ats_typ['precipitation rain [m s^-1]'] + ats_typ['precipitation snow [m SWE s^-1]']
mean_precip = precip_total.mean()
print(f'Mean annual precip rate [m s^-1] = {mean_precip}')
logging.info(f'Mean annual precip rate [m s^-1] = {mean_precip}')

# Convert Daymet data to the new format