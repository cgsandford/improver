# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017-2018 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
""" Utilites to find the relative position of the sun."""

import numpy as np
import datetime as dt

from improver.utilities.temporal import iris_time_to_datetime
from improver.utilities.spatial import (
    lat_lon_determine, transform_grid_to_lat_lon)


def solar_declination(day_of_year):
    """
    Calculate the Declination for the day of the year.

    Calculation equivalent to the calculation defined in
    NOAA Earth System Reseach Lab Low Accuracy Equations
    https://www.esrl.noaa.gov/gmd/grad/solcalc/sollinks.html

    Args:
        day_of_year (int):
            Day of the year 0 to 365, 0 = 1st January

    Returns:
        declination (float):
            Declination in degrees.North-South
    """
    # Declination (degrees):
    # = -(axial_tilt)*cos(360./orbital_year * day_of_year - solstice_offset)
    declination = -23.5 * np.cos(np.radians(0.9856 * day_of_year + 9.3))
    return declination


def solar_hour_angle(longitudes, day_of_year, utc_hour):
    """
    Calculate the Solar Hour angle for an array of longitudes.

    Calculation equivalent to the calculation defined in
    NOAA Earth System Reseach Lab Low Accuracy Equations
    https://www.esrl.noaa.gov/gmd/grad/solcalc/sollinks.html

    Args:
        longitudes (float or numpy.array):
            A single Longitude or array of Longitudes
            longitudes needs to be between 180.0 and -180.0 degrees
        day_of_year (int):
            Day of the year 0 to 365, 0 = 1st January
        utc_hour (float):
            Hour of the day in UTC

    Returns:
        solar_hour_angle (numpy.array)
            Hour angle in degrees East-West
    """
    if np.min(longitudes) < -180.0 or np.max(longitudes) > 180.0:
        msg = ('Longitudes must be between -180.0 and 180.0')
        raise ValueError(msg)
    thetao = 2*np.pi*day_of_year/365.0
    eqt = (0.000075 + 0.001868 * np.cos(thetao) -
           0.032077 * np.sin(thetao) - 0.014615 * np.cos(2*thetao) -
           0.040849 * np.sin(2*thetao))

    # Longitudinal Correction from the Grenwich Meridian
    lon_correction = 24.0*longitudes/360.0
    # Solar time (hours):
    solar_time = utc_hour + lon_correction + eqt*12/np.pi
    # Hour angle (degrees):
    solar_hour_angle = (solar_time - 12.0) * 15.0

    return solar_hour_angle


def solar_elevation(latitudes, longitudes, day_of_year, utc_hour):
    """
    Calculate the Solar elevation.

    Args:
        latitudes (float or numpy.array):
            A single Latitude or array of Latitudes
            latitudes needs to be between -90.0 and 90.0
        longitudes (float or numpy.array):
            A single Longitude or array of Longitudes
            longitudes needs to be between 180.0 and -180.0
        day_of_year (int):
            Day of the year 0 to 365, 0 = 1st January
        utc_hour (float):
            Hour of the day in UTC in hours

    Returns:
        solar_elevation (numpy.array):
            Solar elevation in degrees
    """
    if np.min(longitudes) < -180.0 or np.max(longitudes) > 180.0:
        msg = ('Longitudes must be between -180.0 and 180.0')
        raise ValueError(msg)
    if np.min(latitudes) < -90.0 or np.max(latitudes) > 90.0:
        msg = ('Latitudes must be between -90.0 and 90.0')
        raise ValueError(msg)
    declination = solar_declination(day_of_year)
    decl = np.radians(declination)
    hour_angle = solar_hour_angle(longitudes, day_of_year, utc_hour)
    rad_hours = np.radians(hour_angle)
    lats = np.radians(latitudes)
    # Calculate solar position:

    solar_elevation = (np.arcsin(np.sin(decl) * np.sin(lats) +
                                 np.cos(decl) * np.cos(lats) *
                                 np.cos(rad_hours)))

    solar_elevation = np.degrees(solar_elevation)

    return solar_elevation


def daynight_terminator(longitudes, day_of_year, utc_hour):
    """
    Calculate the Latitude values of the daynight terminator

    Args:
        longitudes (numpy.array):
            Array of longitudes.
            longitudes needs to be between 180.0 and -180.0 degrees
        day_of_year (int):
            Day of the year
        utc_hour (float):
            Hour of the day in UTC

    Returns:
        latitudes (numpy.array):
            latitudes of the daynight terminator
    """
    declination = solar_declination(day_of_year)
    decl = np.radians(declination)
    hour_angle = solar_hour_angle(longitudes, day_of_year, utc_hour)
    rad_hour = np.radians(hour_angle)
    lats = np.arctan(-np.cos(rad_hour)/np.tan(decl))
    lats = np.degrees(lats)
    return lats


class DayNightMask(object):
    """
    Generate a daynight mask for the provided cube
    """
    def __init__(self):
        """ Initial the DayNightMask Object """
        self.NIGHT = 0
        self.DAY = 1

    def __repr__(self):
        """Represent the configured plugin instance as a string."""
        result = ('<DayNightMask : '
                  'Day = {}, Night = {}>'.format(self.DAY, self.NIGHT))
        return result

    def _create_daynight_mask(self, cube):
        """
        Create blank daynight mask cube

        Args:
            cube (iris.cube.Cube):
                cube with the times and coordinates required for mask

        Returns:
            daynight_mask (iris.cube.Cube):
                Blank daynight mask cube. The resulting cube will be the
                same shape as the time, y, and x coordinate, other coordinates
                will be ignored although they might appear as attributes
                on the cube as it is extracted from the first slice.
        """
        daynight_mask = next(cube.slices([cube.coord('time'),
                                          cube.coord(axis='y'),
                                          cube.coord(axis='x')])).copy()
        daynight_mask.long_name = 'day_night_mask'
        daynight_mask.standard_name = None
        daynight_mask.var_name = None
        daynight_mask.units = 1
        daynight_mask.data = np.ones(daynight_mask.data.shape,
                                     dtype='int')*self.NIGHT
        return daynight_mask

    def _daynight_lat_lon_cube(self, mask_cube, day_of_year, utc_hour):
        """
        Calculate the daynight mask for the provided Lat Lon cube

        Args:
            mask_cube (iris.cube.Cube):
                daynight mask cube - data initially set to self.NIGHT
            day_of_year (int):
                day of the year
            utc_hour (float):
                Hour in UTC

        Returns:
            mask_cube (iris.cube.Cube):
                daynight mask cube - daytime set to self.DAY
        """
        lons = mask_cube.coord('longitude').points
        lats = mask_cube.coord('latitude').points
        terminator_lats = daynight_terminator(lons, day_of_year, utc_hour)
        lons_zeros = np.zeros_like(lons)
        lats_zeros = np.zeros_like(lats).reshape(len(lats), 1)
        lats_on_lon = lats.reshape(len(lats), 1) + lons_zeros
        terminator_on_lon = lats_zeros + terminator_lats
        dec = solar_declination(day_of_year)
        if dec > 0.0:
            index = np.where(lats_on_lon >= terminator_on_lon)
        else:
            index = np.where(lats_on_lon < terminator_on_lon)
        mask_cube.data[index] = self.DAY
        return mask_cube

    def process(self, cube):
        """
        Calculate the daynight mask for the provided cube

        Args:
            cube (iris.cube.Cube):
                input cube

        Returns:
            daynight_mask (iris.cube.Cube):
                daynight mask cube, daytime set to self.DAY
                nighttime set to self.NIGHT.
                The resulting cube will be the same shape as
                the time, y, and x coordinate, other coordinates
                will be ignored although they might appear as attributes
                on the cube as it is extracted from the first slice.
        """
        daynight_mask = self._create_daynight_mask(cube)
        dtvalues = iris_time_to_datetime(daynight_mask.coord('time'))
        for i in range(0, len(daynight_mask.coord('time').points)):
            mask_cube = daynight_mask[i]
            dtval = dtvalues[i]
            day_of_year = (dtval - dt.datetime(dtval.year, 1, 1)).days
            utc_hour = (dtval.hour * 60.0 + dtval.minute) / 60.0
            trg_crs = lat_lon_determine(mask_cube)
            # Grids that are not Lat Lon
            if trg_crs is not None:
                lats, lons = transform_grid_to_lat_lon(mask_cube)
                solar_el = solar_elevation(lats, lons, day_of_year, utc_hour)
                mask_cube.data[np.where(solar_el > 0.0)] = self.DAY
            else:
                mask_cube = self._daynight_lat_lon_cube(mask_cube,
                                                        day_of_year, utc_hour)
            daynight_mask.data[i, ::] = mask_cube.data

        return daynight_mask
