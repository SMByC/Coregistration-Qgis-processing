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
import importlib
import os
import site

from qgis.PyQt.QtWidgets import QMessageBox

from Coregistration.utils import extralibs


def check_dependencies():
    try:
        import sklearn  # noqa: F401
        import arosics
        importlib.reload(arosics)

        # Use packaging.version when available, otherwise fall back to a
        # tuple comparison so this works on minimal Python environments.
        try:
            from packaging import version as _pkg_version
            if _pkg_version.parse(arosics.version.__version__) < _pkg_version.parse("1.12"):
                return False
        except ImportError:
            parts = arosics.version.__version__.split(".")
            try:
                major, minor = int(parts[0]), int(parts[1])
            except (ValueError, IndexError):
                return True  # if we can't parse, assume OK
            if (major, minor) < (1, 12):
                return False

        return True
    except ImportError:
        return False


def pre_init_plugin():

    extra_libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'extlibs'))

    if os.path.isdir(extra_libs_path):
        # add to python path so subsequent imports (and importlib.metadata
        # in modern Python) can discover the bundled distributions
        site.addsitedir(extra_libs_path)


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
            QMessageBox.critical(None, 'Coregistration Plugin: Error loading', msg, QMessageBox.StandardButton.Ok)

    return CoregistrationPlugin()
