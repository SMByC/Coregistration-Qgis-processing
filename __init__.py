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
import ctypes
import importlib
import os
import platform
import shutil
import site
import pkg_resources

from qgis.PyQt.QtWidgets import QMessageBox

from Coregistration.utils import extralibs


def unload_all_dlls(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".dll"):
                dll_path = os.path.join(root, file)
                try:
                    # Load the DLL
                    dll = ctypes.windll.LoadLibrary(dll_path)
                    # Unload the DLL
                    ctypes.windll.kernel32.FreeLibrary(dll._handle)
                except Exception as e:
                    print(f"Error removing {file}: {e}")


def check_dependencies():
    try:
        import arosics
        importlib.reload(arosics)

        # update the extlibs if using an old version
        if arosics.version.__version__ != "1.9.3":
            extra_libs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'extlibs'))
            # remove the extra libs ignoring the errors
            if platform.system() == "Windows":
                unload_all_dlls(extra_libs_path)
            shutil.rmtree(extra_libs_path, ignore_errors=True)
            # show a message to the user to restart QGIS
            msg = "The Co-registration Plugin requires restarting QGIS to load the update after installing it."
            QMessageBox.information(None, 'Co-registration Plugin: Restart QGIS', msg, QMessageBox.Ok)

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
    # load extra python dependencies
    pre_init_plugin()

    if not check_dependencies():
        # install extra python dependencies
        extralibs.install()
        # load extra python dependencies
        pre_init_plugin()

        if not check_dependencies():
            msg = "Error loading libraries for Co-registration Plugin. " \
                  "Read the install instructions here:\n\n" \
                  "https://github.com/SMByC/Coregistration-Qgis-processing#installation"
            QMessageBox.critical(None, 'Coregistration Plugin: Error loading', msg, QMessageBox.Ok)

    from Coregistration.coregistration_plugin import CoregistrationPlugin
    return CoregistrationPlugin()
