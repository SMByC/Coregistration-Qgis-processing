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
import platform

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
)
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from Coregistration.utils.system_utils import get_raster_driver_name_by_extension


class AutomatedLocalCoregistrationAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm compute a specific statistic using the time
    series of all pixels across (the time) all raster in the specific band
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    IMG_REF = "IMG_REF"
    INPUT = "INPUT"
    ALIGN_GRIDS = "ALIGN_GRIDS"
    MATCH_GSD = "MATCH_GSD"
    GRID_RES = "GRID_RES"
    WINDOW_SIZE = "WINDOW_SIZE"
    MAX_SHIFT = "MAX_SHIFT"
    RESAMPLING = "RESAMPLING"
    MASK = "MASK"
    OUTPUT = "OUTPUT"

    resampling_methods = (
        ("Nearest Neighbour", "nearest"),
        ("Bilinear", "bilinear"),
        ("Cubic", "cubic"),
        ("Cubic Spline", "cubic_spline"),
        ("Lanczos Windowed Sinc", "lanczos"),
        ("Average", "average"),
        ("Mode", "mode"),
        ("Maximum", "max"),
        ("Minimum", "min"),
        ("Median", "med"),
        ("First Quartile", "q1"),
        ("Third Quartile", "q3"),
    )

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
        parameters and outputs associated with it..
        """
        html_help = (
            "<p>Detects and corrects spatially variable X/Y shift misregistrations between two input images "
            "at subpixel precision. Performs automatic subpixel co-registration based on frequency-domain "
            "image matching (phase correlation), combined with a multistage workflow for effective detection "
            "of false-positives [1].</p>"
            "<p>Computes a dense tie point grid across the image overlap, validates each point through a "
            "multistage outlier detection workflow, and derives a spatially variable correction that is "
            "applied by warping the target image. Best used when the target image has spatially varying "
            "misregistration — i.e., different shifts in different areas. Clouds and outliers are "
            "automatically handled [1].</p>"
            "<p>It is designed to robustly handle the typical difficulties of multi-sensor/multi-temporal "
            "images. This algorithm is significantly more comprehensive and slower than the global algorithm.</p>"
            "<p>Key parameters: tie point grid resolution, matching window size, maximum shift distance.</p>"
            "<p>[1] This algorithm uses AROSICS software developed by Daniel Scheffler — "
            "<a href='https://danschef.git-pages.gfz-potsdam.de/arosics/doc/'>documentation</a> and "
            "<a href='https://doi.org/10.3390/rs9070676'>paper (Scheffler et al. 2017, Remote Sensing 9(7):676)</a>.</p>"
        )
        return html_help

    def createInstance(self):
        return AutomatedLocalCoregistrationAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "Automated local Co-Registration"

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
                self.IMG_REF, self.tr("The REFERENCE image to use as based to co-register the target image")
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr("The TARGET image for co-register"),
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ALIGN_GRIDS,
                self.tr("Align the input coordinate grid to the reference"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MATCH_GSD,
                self.tr("Match the input pixel size to the reference pixel size"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.GRID_RES,
                self.tr("Tie point grid resolution (pixel units of the target image)"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=200,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.WINDOW_SIZE,
                self.tr("Custom matching window size (width and height in pixel units)"),
                type=QgsProcessingParameterNumber.Type.Integer,
                defaultValue=256,
            )
        )

        parameter = QgsProcessingParameterNumber(
            self.MAX_SHIFT,
            self.tr("Maximum shift distance in reference image pixel units"),
            type=QgsProcessingParameterNumber.Type.Integer,
            defaultValue=5,
            optional=False,
        )
        parameter.setFlags(parameter.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(parameter)

        parameter = QgsProcessingParameterEnum(
            self.RESAMPLING,
            self.tr("The resampling algorithm to be used for shift correction (if necessary)"),
            options=[i[0] for i in self.resampling_methods],
            defaultValue=2,
            optional=False,
        )
        parameter.setFlags(parameter.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(parameter)

        self.addParameter(
            QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr("Output raster file co-registered"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        try:
            from arosics import COREG_LOCAL
        except Exception:
            msg = (
                "\nError loading Arosics, this plugin requires additional Python packages to work. "
                "Read the install instructions here:\n\n"
                "https://github.com/SMByC/Coregistration-Qgis-processing#installation\n\n"
            )
            feedback.reportError(msg, fatalError=True)
            return {}

        def get_inputfilepath(layer):
            return os.path.realpath(layer.source().split("|layername")[0])

        img_ref = get_inputfilepath(self.parameterAsRasterLayer(parameters, self.IMG_REF, context))
        img_tgt = get_inputfilepath(self.parameterAsRasterLayer(parameters, self.INPUT, context))

        align_grids = self.parameterAsBoolean(parameters, self.ALIGN_GRIDS, context)
        match_gsd = self.parameterAsBoolean(parameters, self.MATCH_GSD, context)

        grid_res = self.parameterAsInt(parameters, self.GRID_RES, context)

        window_size = self.parameterAsInt(parameters, self.WINDOW_SIZE, context)

        max_shift = self.parameterAsInt(parameters, self.MAX_SHIFT, context)
        resampling_method = self.resampling_methods[self.parameterAsEnum(parameters, self.RESAMPLING, context)][1]

        output_file = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
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

        feedback.pushInfo("Image to image Co-Registration:")
        feedback.pushInfo("\nProcessing file: " + img_tgt)

        feedback.pushInfo("\nPerform automatic subpixel co-registration with Arosics...")
        feedback.pushInfo("\n(To check the complete log of the process, open the Python Console)...")
        if platform.system() == "Windows":
            feedback.reportError(
                "\nWarning: in Windows due to restrictions to enable multiprocessing inside Qgis, "
                "the process could take longer. Continue with one core ...\n",
                fatalError=False,
            )
        CRL = COREG_LOCAL(
            img_ref,
            img_tgt,
            path_out=output_file,
            align_grids=align_grids,
            match_gsd=match_gsd,
            grid_res=grid_res,
            window_size=(window_size, window_size),
            resamp_alg_deshift=resampling_method,
            max_shift=max_shift,
            max_iter=15,
            fmt_out=output_driver_name,
            out_crea_options=["WRITE_METADATA=NO"],
            CPUs=1,
        )
        CRL.correct_shifts()

        feedback.pushInfo("DONE\n")

        return {self.OUTPUT: output_file}
