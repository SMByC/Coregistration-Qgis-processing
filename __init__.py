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
import importlib
import os
import site
import pkg_resources
from packaging import version

from qgis.PyQt.QtWidgets import QMessageBox

from Coregistration.utils import extralibs


def check_dependencies():
    try:
        import arosics
        importlib.reload(arosics)

        if version.parse(arosics.version.__version__) < version.parse("1.9"):
            return False

        return True
    except ImportError:
        return False


def pre_init_plugin():

    extra_libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'extlibs'))

    if os.path.isdir(extra_libs_path):
        # add to python path
        site.addsitedir(extra_libs_path)
        # pkg_resources doesn't listen to changes on sys.path.
        pkg_resources.working_set.add_entry(extra_libs_path)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Coregistration class from file Coregistration.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from Coregistration.coregistration_plugin import CoregistrationPlugin
    # load extra python dependencies
    pre_init_plugin()

    if not check_dependencies():
        # clean the extra libs
        if not extralibs.clean():
            return CoregistrationPlugin()

        # install extra python dependencies
        extralibs.install()
        # load extra python dependencies
        pre_init_plugin()

        if not check_dependencies():
            msg = "Error loading libraries for Co-registration Plugin. " \
                  "Read the install instructions here:\n\n" \
                  "https://github.com/SMByC/Coregistration-Qgis-processing#installation"
            QMessageBox.critical(None, 'Coregistration Plugin: Error loading', msg, QMessageBox.Ok)

    return CoregistrationPlugin()
