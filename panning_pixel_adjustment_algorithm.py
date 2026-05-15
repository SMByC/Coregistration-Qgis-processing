"""
/***************************************************************************
 Coregistration
                          A QGIS plugin processing
 Image co-registration, projection and pixel alignment based on a target image
                              -------------------
        copyright            : (C) 2021-2026 by Xavier Corredor Llano, SMByC
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
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from Coregistration.utils.system_utils import get_raster_driver_name_by_extension


class PanningPixelAdjustmentAlgorithm(QgsProcessingAlgorithm):
    """
    Manually shifts an image's geotransform by a user-specified X/Y offset
    in pixel units without resampling pixel values.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = "INPUT"
    SHIFT_IN_X = "SHIFT_IN_X"
    SHIFT_IN_Y = "SHIFT_IN_Y"
    OUTPUT = "OUTPUT"

    def __init__(self):
        super().__init__()

    def tr(self, string, context=""):
        if context == "":
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it.
        """
        html_help = (
            "<p>Provides a simple way to manually shift an image in the X (longitude) and Y (latitude) "
            "directions. The shift values are expressed in pixel units and can be fractional.</p>"
            "<p>This algorithm is not automatic — the user must specify the pixel shift in X and Y. "
            "Skipping the output will overwrite and update the georeferencing of the input file in place.</p>"
        )
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
        return "Panning pixel adjustment"

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
                self.tr("The TARGET image"),
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SHIFT_IN_X,
                self.tr("Shift in X (in pixel units, where + is to the right and - is to the left)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SHIFT_IN_Y,
                self.tr("Shift in Y (in pixel units, where + is to the top and - is to the bottom)"),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Output raster file (Warning: leave empty to overwrite and update the input file in place)"),
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
        if os.path.isfile(file_in_path + ".aux.xml"):
            os.remove(file_in_path + ".aux.xml")

        skip_output = output_file == ""

        if skip_output:
            # Overwrite in place: only update the geotransform tag in the
            # existing file. We avoid CreateCopy here because it rewrites the
            # whole file (write temp → delete original → rename), which fails on
            # Windows when QGIS holds an open handle on the loaded layer
            # ("Permission denied" on the delete step). Updating the geotransform
            # via GA_Update touches only the header, so the existing file handle
            # does not block it.
            update_ds = gdal.Open(file_in_path, gdal.GA_Update)
            gt = update_ds.GetGeoTransform()
            pixel_size_x = abs(gt[1])
            pixel_size_y = abs(gt[5])
            gtl = list(gt)
            gtl[0] = gtl[0] + pixel_size_x * shift_in_x  # Move horizontal
            gtl[3] = gtl[3] + pixel_size_y * shift_in_y  # Move vertical
            update_ds.SetGeoTransform(tuple(gtl))
            update_ds.FlushCache()
            update_ds = None

            output_file = file_in_path

            # remove .aux.xml output file
            if os.path.isfile(output_file + ".aux.xml"):
                os.remove(output_file + ".aux.xml")

            # Re-bind the layer to its source so QGIS fully rebuilds its
            # internal state (data provider, extent, renderer/symbology caches).
            # Just calling reload() / reloadData() is not enough: the renderer
            # holds per-pixel transforms cached from the OLD geotransform, so
            # the shifted edges render as blank until the layer is closed and
            # reopened. setDataSource() is the API equivalent of "close and
            # reopen", and loadDefaultStyleFlag=False preserves the user's
            # current style/symbology.
            file_in.dataProvider().reloadData()
            file_in.setDataSource(file_in.source(), file_in.name(), file_in.providerType(), False)
            file_in.triggerRepaint()
        else:
            input_ds = gdal.Open(file_in_path, gdal.GA_ReadOnly)
            gt = input_ds.GetGeoTransform()
            pixel_size_x = abs(gt[1])
            pixel_size_y = abs(gt[5])
            gtl = list(gt)
            gtl[0] = gtl[0] + pixel_size_x * shift_in_x  # Move horizontal
            gtl[3] = gtl[3] + pixel_size_y * shift_in_y  # Move vertical
            input_ds.SetGeoTransform(tuple(gtl))

            output_driver_name = get_raster_driver_name_by_extension(output_file)

            # fix save and load ENVI files
            if output_driver_name == "ENVI":
                output_file_envi = output_file.replace(".hdr", ".dat")
                if context.willLoadLayerOnCompletion(output_file):
                    layer_detail = context.LayerDetails(
                        os.path.basename(output_file_envi),
                        context.project(),
                        os.path.basename(output_file_envi),
                        QgsProcessingUtils.LayerHint.Raster,
                    )
                    context.setLayersToLoadOnCompletion({output_file_envi: layer_detail})
                output_file = output_file_envi

            gdal_driver = gdal.GetDriverByName(output_driver_name)
            gdal_driver.CreateCopy(output_file, input_ds)
            input_ds = None

            # remove .aux.xml output file
            if os.path.isfile(output_file + ".aux.xml"):
                os.remove(output_file + ".aux.xml")

        feedback.pushInfo("--> done\n")

        return {self.OUTPUT: output_file}
