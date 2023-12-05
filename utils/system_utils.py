# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Coregistration
                          A QGIS plugin processing
 Image co-registration, projection and pixel alignment based on a target image
                              -------------------
        copyright            : (C) 2023 by Xavier Corredor Llano, SMByC
        email                : xavier.corredor.llano@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from osgeo import gdal


def get_raster_driver_by_extension(file_extension):
    file_extension = file_extension.lower()
    # fix tiff
    if file_extension == 'tiff':
        file_extension = 'tif'
    # Get the list of all GDAL raster drivers
    driver_list = gdal.GetDriverCount()

    # Loop through the drivers and find the one associated with the given file extension
    for i in range(driver_list):
        driver = gdal.GetDriver(i)
        extensions = driver.GetMetadataItem("DMD_EXTENSION")

        if extensions:
            extensions = extensions.split()
            if file_extension in extensions:
                return driver.ShortName

    return None  # Return None if no matching driver is found
