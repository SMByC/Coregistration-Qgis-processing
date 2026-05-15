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
import sys
import warnings
from contextlib import contextmanager


class _FeedbackStream:
    """File-like object that forwards writes to a QgsProcessingFeedback, line by line."""

    def __init__(self, feedback, is_error=False):
        self._feedback = feedback
        self._is_error = is_error
        self._buffer = ""

    def write(self, text):
        if not text:
            return
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._emit(line)

    def flush(self):
        if self._buffer:
            self._emit(self._buffer)
            self._buffer = ""

    def _emit(self, line):
        if not line.strip():
            return
        if self._is_error:
            self._feedback.reportError(line, fatalError=False)
        else:
            self._feedback.pushInfo(line)

    def isatty(self):
        return False


@contextmanager
def redirect_output_to_feedback(feedback):
    """Redirect stdout, stderr and Python warnings to a QgsProcessingFeedback."""

    stdout_stream = _FeedbackStream(feedback)
    stderr_stream = _FeedbackStream(feedback, is_error=True)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    old_showwarning = warnings.showwarning

    def _showwarning(message, category, filename, lineno, file=None, line=None):
        feedback.reportError(f"{category.__name__}: {message}", fatalError=False)

    sys.stdout = stdout_stream
    sys.stderr = stderr_stream
    warnings.showwarning = _showwarning
    try:
        yield
    finally:
        try:
            stdout_stream.flush()
            stderr_stream.flush()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            warnings.showwarning = old_showwarning


def get_raster_driver_name_by_extension(file_path):
    file_extension = os.path.splitext(file_path)[1]
    ext = file_extension.lower().lstrip(".")

    # Dictionary mapping file extensions to GDAL driver names
    driver_map = {
        # Raster Formats
        "tif": "GTiff",
        "tiff": "GTiff",
        "geotiff": "GTiff",
        "img": "HFA",
        "hdr": "ENVI",
        "dat": "ENVI",
        "jp2": "JPEG2000",
        "png": "PNG",
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "bmp": "BMP",
        "gif": "GIF",
        "asc": "AAIGrid",
        "bil": "EHdr",
        "nc": "netCDF",
        "hdf": "HDF4",
        "grd": "surfer",
        "ecw": "ECW",
        "sid": "MrSID",
    }

    # Return the driver name or None if not found
    return driver_map.get(ext)
