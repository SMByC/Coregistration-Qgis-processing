# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Coregistration
                          A QGIS plugin processing
 Image co-registration, projection and pixel alignment based on a target image
                              -------------------
        copyright            : (C) 2021 by Xavier Corredor Llano, SMByC
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
import tempfile
from osgeo import gdal

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterRasterDestination, QgsProcessingParameterRasterLayer)


class CoregistrationAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm compute a specific statistic using the time
    series of all pixels across (the time) all raster in the specific band
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    IMG_REF = 'IMG_REF'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def tr(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def shortHelpString(self):
        return None

    def createInstance(self):
        return CoregistrationAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Image to image Co-Registration'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return None

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return None

    def icon(self):
        return QIcon(":/plugins/Coregistration/icons/coregistration.svg")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Raster input'),
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.IMG_REF,
                self.tr('The reference image to use as based to co-register the input images')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output raster file co-registered')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        def get_inputfilepath(layer):
            return os.path.realpath(layer.source().split("|layername")[0])

        img_ref = get_inputfilepath(self.parameterAsRasterLayer(parameters, self.IMG_REF, context))
        file_in = get_inputfilepath(self.parameterAsRasterLayer(parameters, self.INPUT, context))
        output_file = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        feedback.pushInfo("Image to image Co-Registration:")
        feedback.pushInfo("\nProcessing file: " + file_in)

        # extract some info from IMG_REF
        gdal_img_ref = gdal.Open(img_ref, gdal.GA_ReadOnly)
        min_x, x_res, x_skew, max_y, y_skew, y_res = gdal_img_ref.GetGeoTransform()
        max_x = min_x + (gdal_img_ref.RasterXSize * x_res)
        min_y = max_y + (gdal_img_ref.RasterYSize * y_res)
        x_res = abs(float(x_res))
        y_res = abs(float(y_res))
        # projection
        dst_crs = gdal_img_ref.GetProjection()
        #
        nodata = gdal_img_ref.GetRasterBand(1).GetNoDataValue()

        # extract some info from INPUT
        gdal_input = gdal.Open(file_in, gdal.GA_ReadOnly)
        src_crs = gdal_input.GetProjection()

        gdal.Warp(output_file, file_in, srcSRS=src_crs, dstSRS=dst_crs, xRes=x_res, yRes=y_res, resampleAlg=gdal.GRA_NearestNeighbour,
                  outputBounds=(min_x, min_y, max_x, max_y), targetAlignedPixels=False)

        feedback.pushInfo("--> done\n")

        del gdal_img_ref, gdal_input

        return {self.OUTPUT: output_file}

    def processAlgorithmRasterio(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        import rasterio
        from osgeo import gdal
        from rasterio import shutil as rio_shutil
        from rasterio.vrt import WarpedVRT

        def get_inputfilepath(layer):
            return os.path.realpath(layer.source().split("|layername")[0])

        img_ref = get_inputfilepath(self.parameterAsRasterLayer(parameters, self.IMG_REF, context))
        file_in = get_inputfilepath(self.parameterAsRasterLayer(parameters, self.INPUT, context))
        output_file = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        feedback.pushInfo("Co-registration:")
        feedback.pushInfo("\nProcessing file: " + file_in)

        # extract some info
        with rasterio.open(img_ref) as target:
            dst_crs = target.crs
            x_res, y_res = target.res
            vrt_options = {
                'crs': target.crs,
                'transform': target.transform,
                'height': target.height,
                'width': target.width,
                'nodata': target.nodata
            }
        with rasterio.open(file_in) as src:
            src_crs = src.crs

        # ----- reprojection
        if src_crs != dst_crs:
            feedback.pushInfo("--> reprojection is required, to CRS: {}".format(dst_crs))
            # reproject
            reprj_file_tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=True)
            reprj_file = reprj_file_tmp.name
            resample = gdal.GRA_NearestNeighbour
            gdal.Warp(reprj_file, file_in, srcSRS=src_crs, dstSRS=dst_crs, xRes=x_res, yRes=y_res, resampleAlg=resample)
        else:
            reprj_file_tmp = False
            reprj_file = file_in

        # ----- set extent and align pixels based on PU
        feedback.pushInfo("--> set extent and align pixels")
        if target.nodata is not None:
            feedback.pushInfo("--> nodata as: {}".format(target.nodata))

        with rasterio.open(reprj_file) as src:
            with WarpedVRT(src, **vrt_options) as vrt:
                rio_shutil.copy(vrt, output_file, driver='GTiff')

        feedback.pushInfo("--> done\n")

        if reprj_file_tmp:
            reprj_file_tmp.close()

        return {self.OUTPUT: output_file}
