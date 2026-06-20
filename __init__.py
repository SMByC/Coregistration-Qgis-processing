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
 This script initializes the plugin, making it known to QGIS.
"""

import importlib
import os
import site

from qgis.PyQt.QtWidgets import QMessageBox

from Coregistration.utils import extralibs


def check_dependencies() -> bool:
    """Return ``True`` if all required extra libraries are importable and meet the
    minimum version requirement (arosics >= 1.13).
    """
    try:
        import arosics

        # Reload so that newly-added extlibs are picked up when this function
        # is called a second time after install().
        importlib.reload(arosics)

        try:
            from packaging import version as _v

            return _v.parse(arosics.version.__version__) >= _v.parse("1.13")
        except ImportError:
            parts = arosics.version.__version__.split(".")
            try:
                return (int(parts[0]), int(parts[1])) >= (1, 13)
            except (ValueError, IndexError):
                return True  # cannot parse → assume OK

    except ImportError:
        return False


def pre_init_plugin() -> None:
    """Add the bundled *extlibs* directory to ``sys.path`` so that the extra
    Python packages can be imported before the plugin body is loaded.
    """
    extra_libs_path = extralibs.get_extlibs_install_path()
    if os.path.isdir(extra_libs_path):
        site.addsitedir(extra_libs_path)
        # Register with pkg_resources when available (removed in Python 3.12+)
        try:
            import pkg_resources
            pkg_resources.working_set.add_entry(extra_libs_path)
        except:
            pass


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Coregistration class from file Coregistration.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    # Attempt to load bundled extra dependencies first
    pre_init_plugin()

    if not check_dependencies():
        # Extra libs missing or outdated - download and install them, then retry
        extralibs.install()
        pre_init_plugin()

        if not check_dependencies():
            msg = (
                "Error loading libraries for Co-registration Plugin.\n\n"
                "Read the install instructions here:\n"
                "https://github.com/SMByC/Coregistration-Qgis-processing#installation"
            )
            QMessageBox.critical(
                None,
                "Coregistration Plugin: Error loading",
                msg,
                QMessageBox.StandardButton.Ok,
            )

    # Register icons under :/plugins/Coregistration/ before the plugin class is imported
    from . import resources  # noqa: F401
    from Coregistration.coregistration_plugin import CoregistrationPlugin

    return CoregistrationPlugin()
