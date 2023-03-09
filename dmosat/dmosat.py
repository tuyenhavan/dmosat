"""A module for calculating drought indices and
extracting its drought characteristics from remote sensing vegetation"""

import xarray
import numpy as np
import re

from utils import RasterReader
from utils import TimeDimension

class VegetationDroughtIndices:
    " A class to compute common vegetation remote sensing drought indices"

    def AVI(self,data):
        """Compute anomaly vegetation index (AVI) from time-series NDVI"""
        monthly_mean=data.groupby("time.month").mean("time")
        monthly_avi=data.groupby("time.month")-monthly_mean
        return monthly_avi

    def VCI(self,data):
        """ Compute the vegetation condition index (VCI) from time-series NDVI"""
        monthly_min=data.groupby("time.month").min("time")
        monthly_max=data.groupby("time.month").max("time")
        max_min=monthly_max-monthly_min
        nominator=data.groupby("time.month")-monthly_min
        monthly_vci=nominator.groupby("time.month")/max_min*100
        return monthly_vci

    def TCI(self,data):
        """ Compute the temperature condition index (TCI) from time-series LST"""
        monthly_min=data.groupby("time.month").min("time")
        monthly_max=data.groupby("time.month").max("time")
        max_min=monthly_max-monthly_min
        nominator=data.groupby("time.month")-monthly_min
        monthly_tci=nominator.groupby("time.month")/max_min*100
        return monthly_tci

class DroughtCharacteristics:
    """ Extract some common drought characteristics, for example drought frequency,
    latest drought years, drought duration, drought events with three consecutive time periods."""

    def drought_frequency(self,data, threshold=None):
        """ Calculate drought frequency

            Args:
                data (xarray.core.dataarray.DataArray): The input DataArray with time dimension.
                threshold (int|float): The threshold for identifying a drought event.

            Returns:
                xarray.core.dataaray.DataArray: The drought frequency.
        """
        if not threshold is None:
            mask=self._mask_data(data)
            mask_sum=mask.sum("time")
            dc=mask_sum/self._size(data)*100
            dc=xarray.where(dc<=0,np.nan,dc)
            return dc
        return data

    def drought_duration(self,data, threshold=None):
        """ Calculate the mean drought duration

            Args:
                data (xarray.DataArray): The input DataArray.
                threshold (int|float|optional): The threshold for defining a drought event.

            Returns:
                xarray.DataArray: The mean drought duration at each pixel.
        """

        if not threshold is None:
            dd=xarray.apply_ufunc(self._mean_duration, self._mask_data(data,threshold),
            input_core_dims=[["time"]], vectorize=True)
            return dd

        return data

    def _mean_duration(self,a):
        if np.isnan(a).all():
            return np.nan
        else:
            text=np.where(np.isnan(a),"1","a")
            text="".join(text)
            text=[(i.end(0)-i.start(0)) for i in re.finditer("[a]+",text)]
            ket=np.nanmean(text)
            return ket

    def drought_trend(self):
        pass

    def _size(self,data):
        temp_size=data.shape
        if len(temp_size)<2:
            return 1

        return temp_size[0]

    def _mask_data(self,data, threshold=None):
        if not threshold is None:
            mask=xarray.where(data<=threshold, 1, np.nan)
            return mask
        return data

# Count the number of drought events with at least 3 consecutive months
def drought_event(data, event=None):
    """ Calculate the total number of drought events with a given pre-defined thresholds.

        Args:
            data (xarray.DataArray): The input binary data.
            event (int|optional): The pre-defined threshold for a drought event.

        Returns:
            xarray.DataArray: The number of drought events.
    """
    if event is None:
        event=3
    def _total_event(a):
        if np.isnan(a).all():
            return np.nan
        else:
            text=np.where(np.isnan(a),"1","a")
            text="".join(text)
            count=[(i.end(0)-i.start(0)) for i in re.finditer("[a]+",text)]
            count=[i for i in count if i>=event]
            if count:
                return len(count)
            else:
                return 0.
    total_number=xarray.apply_ufunc(_total_event, data,input_core_dims=[["time"]], vectorize=True)
    return total_number
"Create instances and make it as available"

RasterRead=RasterReader()
read_from_numpy=RasterRead.read_from_numpy
read_raster=RasterRead.read_raster

TimeDimension=TimeDimension()
add_time_dim=TimeDimension.add_time_dim
datestring_format=TimeDimension._datestring_format
threshold_mask=TimeDimension.threshold_mask

VegetationDroughtIndices=VegetationDroughtIndices()
AVI=VegetationDroughtIndices.AVI
VCI=VegetationDroughtIndices.VCI
TCI=VegetationDroughtIndices.TCI

DroughtCharacteristics=DroughtCharacteristics()
drought_frequency=DroughtCharacteristics.drought_frequency
drought_duration=DroughtCharacteristics.drought_duration
