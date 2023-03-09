" A helper module for calculating drought indices and extracting drought characteristics."
import os
from dateutil.relativedelta import relativedelta
import datetime
import re

import numpy as np
from xarray import DataArray
from rioxarray import open_rasterio

class RasterReader:
    """ A class to read raster data and numpy array inherited from rioxarray"""

    def read_raster(self, file_path, **kwargs):
        """ Read all files that are readable from open_raserio

            Args:
                file_path (str): The path string
                kwargs (dict-like): See more from kwargs from open_rasterio.

            Returns:
                xarray.core.dataarray.DataArray: The data xarray.
        """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} is not found!")
        try:
            data=open_rasterio(file_path,**kwargs)
        except Exception as e:
            raise ValueError("Failed to read the input dataset.")
            data=None
        return data

    def read_from_numpy(self, file_path,x=None,y=None, **kwargs):
        """ Convert numpy array to DataArray

            Args:
                file_path (str): The path string.
                x (list|optional): The list of x coordinates.
                y (list|optional): The list of y cooridnates.
                kwargs (dict-like): See more from kwargs from numpy.load.

            Returns:
                DataArray: The xarray.DataArray
        """

        if os.path.exists(file_path):
            if file_path.endswith(".txt"):
                np_data=np.loadtxt(file_path,**kwargs)
            elif file_path.endswith(".npy"):
                np_data=np.load(file_path,**kwargs)
            elif file_path.endswith(".csv"):
                np_data=np.genfromtxt(file_path,**kwargs)
            else:
                raise TypeError("The input path must be strings of the folliwing extension (.txt, .npy, and .csv)")
        else:
            raise FileNotFoundError ("The input file is not found!")
        band=np_data.shape

        if not (x is None or y is None):
            x=np.array(list(x))
            y=np.array(list(y))
            if len(band)<3:
                data=DataArray(np_data, dims=("y","x"), coords={"y":y,"x":x})
            else:
                data=DataArray(np_data, dims=("band","y","x"),
                               coords={"y":y,"x":x,"band":np.arange(band[0])})
        else:
            data=DataArray(np_data)
            if len(band)<3:
                data=data[0]

        return data

class TimeDimension:
    """ Add a datetime dimension to the time-series DataArray"""

    def add_time_dim(self, data, date_str=None):
        """ Add time dimension (monthly) to the DataArray. Currently supported only monthly interval.

            Args:
                data (xarray.core.dataarray.DataArray): The input DataArray.
                date_str (str|optional): The input datetime string. Defaults to None.

            Returns:
                xarray.core.dataaray.DataArray: The DataArray with time dimension.
        """
        if date_str is None:
            date_str="2000-02-01"

        date_formatted=self._datestring_format(date_str)
        month_list=self._monthly_date(data,date_formatted)
        if month_list:
            time_dim=data.dims[0]
            data[time_dim]=month_list
            data=data.rename({time_dim:"time"})
            return data
        return data

    def threshold_mask(self,data, threshold):
        """ Mask out data given a threshold

            Args:
                data (xarray.core.datarray.DataArray): The input DataArray.
                threshold (int|float): The threshold for values masking.

            Returns:
                xarray.core.dataarray.DataArray: The masked DataArray.

        """
        data=xarray.where(data<=threshold,1,np.nan)
        return data

    def _datestring_format(self,date_str):
        """ Format datet string to the format "yyyy-mm-dd".

            Args:
                date_str (str): Date in string format.

            Returns:
                str: The date string with '-' format.
        """
        import re

        if isinstance(date_str,str):
            string="".join([i.strip() for i in date_str.split()])
        else:
            raise ValueError("Unsupported data type.")
        string_date="-".join(re.split('[^\d]+',string))
        return string_date

    def _monthly_date(self,data,date_str):
        """ Create a monthly datetime list"""
        if self._shape_check(data):
            date_format = "%Y-%m-%d"
            start_date=datetime.strptime(self._datestring_format(date_str), date_format)
            month_list=[start_date+relativedelta(months=i) for i in range(data.shape[0])]
        else:
            month_list=None
        return month_list

    def _shape_check(self,data):
        if len(data.shape)==3:
            return True
        return False
