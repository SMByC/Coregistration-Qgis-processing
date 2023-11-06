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
import os
from osgeo import gdal

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessingAlgorithm, QgsProcessingParameterRasterDestination, QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber)

from Coregistration.utils.system_utils import get_raster_driver_by_extension


class PanningPixelAdjustmentAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm compute a specific statistic using the time
    series of all pixels across (the time) all raster in the specific band
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    SHIFT_IN_X = 'SHIFT_IN_X'
    SHIFT_IN_Y = 'SHIFT_IN_Y'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def tr(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        html_help = '''
        <p>The Pixel Panning Adjustment algorithm provides a simple way to manually shift pixels in the X (longitude) and Y \
        (latitude) directions in the whole image given by the user.</p>
        <p>The shift values is in pixel size of the image, but it could be a fractional value.</p>'''
        return html_help

    def createInstance(self):
        return PanningPixelAdjustmentAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Panning pixel adjustment'

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
                self.tr('The TARGET image'),
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SHIFT_IN_X,
                self.tr('Shift in X (in pixels units, where + is to the right and - is to the left)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SHIFT_IN_Y,
                self.tr('Shift in Y (in pixels units, where + is to the top and - is to the bottom)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output raster file (skip the output will overwrite and update the input file!)'),
                optional=True,
                defaultValue=None,
                createByDefault=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        def get_inputfilepath(layer):
            return os.path.realpath(layer.source().split("|layername")[0])

        file_in = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        file_in_path = get_inputfilepath(file_in)

        shift_in_x = self.parameterAsDouble(parameters, self.SHIFT_IN_X, context)
        shift_in_y = self.parameterAsDouble(parameters, self.SHIFT_IN_Y, context)

        output_file = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        feedback.pushInfo("Image panning adjustment:")
        feedback.pushInfo("\nProcessing file: " + file_in_path)

        # remove .aux.xml file
        if os.path.isfile(file_in_path + '.aux.xml'):
            os.remove(file_in_path + '.aux.xml')

        input_ds = gdal.Open(file_in_path, gdal.GA_ReadOnly)
        gt = input_ds.GetGeoTransform()
        # get the pixel size in x and y
        pixel_size_x = abs(gt[1])
        pixel_size_y = abs(gt[5])


        # Convert tuple to list, so we can modify it
        gtl = list(gt)
        gtl[0] = gtl[0] + pixel_size_x*shift_in_x  # Move horizontal
        gtl[3] = gtl[3] + pixel_size_y*shift_in_y  # Move vertical
        # Save the geotransform to the raster
        input_ds.SetGeoTransform(tuple(gtl))
        # save the raster to a new file

        skip_output = output_file == ""
        if skip_output:
            output_file = file_in_path

        # gdal driver based on the output file
        gdal_driver = gdal.GetDriverByName(get_raster_driver_by_extension(output_file.split(".")[-1]).lower())
        gdal_driver.CreateCopy(output_file, input_ds)
        input_ds = None

        # remove .aux.xml output file
        if os.path.isfile(output_file + '.aux.xml'):
            os.remove(output_file + '.aux.xml')

        # repainting the layer in the canvas
        if skip_output:
            file_in.reload()
            file_in.triggerRepaint()

        feedback.pushInfo("--> done\n")

        return {self.OUTPUT: output_file}
