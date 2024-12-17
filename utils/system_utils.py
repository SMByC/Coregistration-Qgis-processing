# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Coregistration
                          A QGIS plugin processing
 Image co-registration, projection and pixel alignment based on a target image
                              -------------------
        copyright            : (C) 2021-2024 by Xavier Corredor Llano, SMByC
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
import os


def get_raster_driver_name_by_extension(file_path):
    file_extension = os.path.splitext(file_path)[1]
    ext = file_extension.lower().lstrip('.')

    # Dictionary mapping file extensions to GDAL driver names
    driver_map = {
        # Raster Formats
        'tif': 'GTiff',
        'tiff': 'GTiff',
        'geotiff': 'GTiff',
        'img': 'HFA',
        'hdr': 'ENVI',
        'dat': 'ENVI',
        'jp2': 'JPEG2000',
        'png': 'PNG',
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'bmp': 'BMP',
        'gif': 'GIF',
        'asc': 'AAIGrid',
        'bil': 'EHdr',
        'nc': 'netCDF',
        'hdf': 'HDF4',
        'grd': 'surfer',
        'ecw': 'ECW',
        'sid': 'MrSID',
    }

    # Return the driver name or None if not found
    return driver_map.get(ext)
