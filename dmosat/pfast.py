"""This module aims to provide common customized functions to serve the PhD work.

Thus, it may or may not related to dmosat package, and it intended for personal use.

"""

import os
import datetime as dt

from osgeo import gdal
import pandas as pd
import numpy as np
import xarray as xr


def merge_tile(dir_path, out_path=None):
    """ Merge multiple tiles into one single tile/image. This often happens
    when large time-series data are downloaded from Google Earth Engine.

        Args:
            dir_path (str): A path to directory where stores all 'tif' tiles.
            out_path (str|optional): A file path to store the merged output. Default to None.

        Returns:
            A tif merged file contains all individual tiles.
    """
    if not isinstance(dir_path, str) or not isinstance(out_path, (str,type(None))):
        raise TypeError("dir_path or out_path are not string")

    # List all tiles
    tiles=[i for i in os.listdir(dir_path) if i.endswith(".tif")]
    if not tiles:
        raise ValueError(f"{dir_path} has no tiles to merge.")
    # Make file list
    flist=[os.path.join(dir_path,i) for i in tiles]
    # Merge using gdal
    if out_path is None:
        out_path=os.path.join(os.getcwd(),"merge_tile.tif")
        merge=gdal.Warp(out_path, flist, format="GTiff",
                  options=["COMPRESS=LZW", "TILED=YES"])
    else:
        merge=gdal.Warp(out_path, flist, format="GTiff",
                  options=["COMPRESS=LZW", "TILED=YES"])
    merge=None
    return None

def to_datetime(path):
    """ Given a list of datetime/date string. Convert them to a list of datetime object.

        Args:
            path (str): The text file path containing datetime/date string.

        Return:
            list: The list of datetime/date objects.
    """
    dlist=[]
    with open(path,"r") as file:
        text=file.readlines()
        for i in text[0].split(","):
            if i:
                datetime_fmt='%Y-%m-%d %H:%M:%S'
                dtime=dt.datetime.strptime(i, datetime_fmt)
                dlist.append(dtime)

    return dlist

# Convert date code from GEE to human readbale code
def time_convert(date_code):
    """ Convert GEE datetime code to Python datetime

        Args:
            date_code (int): The input datetime code from GEE.

        Returns:
            datetime: The Python datetime object.
    """
    # Initialize the start date since GEE started date from 1970-01-01
    start_date=dt.datetime(1970,1,1,0,0,0)
    # Convert time code to number of hours
    hour_number=date_code/(60000*60)
    # Increase dates from an initial date by number of hours
    delta=dt.timedelta(hours=hour_number)
    end_date=start_date+delta
    return end_date

def SWDI(soil,sand, clay, carbon):
    """ Calculate SWDI from soil moisture data, sand, clay and organic matter.
        Please see paper Mishra (2017) for more info.
        https://doi.org/10.1016/j.jhydrol.2017.07.033

    Args:
    - sand (np.array|xr.DataArray): A 2-d numpy sand data. It should be in proportion unit (sand %/100).
    - clay (np.array|xr.DataArray): A 2-d clay data. It should be in proportion unit (sand %/100).
    - carbon (np.array|xr.DataArray): A 2-d carbon organic matter. It should be divided by 0.58 (%/100/0.58)
    - soil (np.ndarray|xr.DataArray): A ndarray soil moisture content

    Return:
        xr.DataArray: The soil water deficit index (SWDI) output.
    """
    clay=clay.isel(band=0)/100
    sand=sand.isel(band=0)/100
    carbon=(carbon.isel(band=0)/100)/0.58 # Convert it to carbon organic matter
    # Equation
    theta_wp_=-0.024*sand+0.487*clay+0.006*carbon+0.005*(sand*carbon)-0.013*(clay*carbon)+0.068*(clay*sand)+0.031
    theta_wp=theta_wp_+(0.14*theta_wp_-0.02)
    theta_fc_=-0.251*sand+0.195*clay+0.011*carbon+0.006*(sand*carbon)-0.027*(clay*carbon)+0.452*(sand*clay)+0.299
    theta_fc=theta_fc_+(1.283*theta_fc_**2-0.374*theta_fc_-0.015)
    theta_awc=theta_fc-theta_wp
    # Compute SWDI
    swdiTem=(soil.values-theta_fc.values)*10/theta_awc.values
    swdi=xr.DataArray(swdiTem, dims=("time","y","x"), coords={"time":soil.time.values,
                                                             "y":soil.y.values,
                                                             "x":soil.x.values})
    return swdi