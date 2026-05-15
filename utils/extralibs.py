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

import configparser
import os
import platform
import shutil
import ssl
import tempfile
import urllib.request
import zipfile

from qgis.core import Qgis, QgsApplication, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

# ---------------------------------------------------------------------------
# Extra-libs download configuration
# ---------------------------------------------------------------------------
# The bundled ``extlibs`` ZIP assets (Arosics + its dependencies) are
# attached to the GitHub Release whose tag matches the plugin ``version=``
# field in ``metadata.txt``. So every time the plugin version is bumped, a
# matching set of ``extlibs_<os>_py<ver>.zip`` files must be uploaded to the
# corresponding release.
#
# Python versions for which a pre-built extlibs ZIP exists. Keep this in sync
# with the ``python-version`` matrix of
# ``.github/workflows/ccd-plugin-package.yml``.
SUPPORTED_PY_VERSIONS: tuple[str, ...] = ("3.12", "3.13", "3.14")


def _get_plugin_version() -> str:
    """Read the plugin version from ``metadata.txt`` (the QGIS-side source of truth)."""
    metadata_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "metadata.txt",
    )
    config = configparser.ConfigParser()
    config.read(metadata_path, encoding="utf-8")
    return config["general"]["version"]


def _log(msg: str, level: str = "Info") -> None:
    """Write *msg* to the QGIS message log (stdout as fallback)."""
    try:
        qgis_level = getattr(getattr(Qgis, "MessageLevel", Qgis), level)
        QgsMessageLog.logMessage(msg, tag="Coregistration", level=qgis_level)
    except Exception:
        print(f"[Coregistration] {msg}")


def _get_extlibs_url() -> str:
    """Build the platform- and Python-version-specific extlibs download URL.

    If the running Python's version is not in ``SUPPORTED_PY_VERSIONS``, the
    URL falls back to the highest published version. A warning is logged so
    the user knows the bundled libs might not be a perfect match.
    """
    major, minor = platform.python_version_tuple()[:2]
    py = f"{major}.{minor}"
    if py not in SUPPORTED_PY_VERSIONS:
        fallback = SUPPORTED_PY_VERSIONS[-1]
        _log(
            f"No pre-built extlibs for Python {py}; falling back to py{fallback}. "
            "Install dependencies manually if loading fails (see README).",
            level="Warning",
        )
        py = fallback
    py_version = f"py{py}"

    base = f"https://github.com/SMByC/Coregistration-Qgis-processing/releases/download/{_get_plugin_version()}/"
    system = platform.system()
    if system == "Windows":
        return base + f"extlibs_windows_{py_version}.zip"
    if system == "Darwin":
        return base + f"extlibs_macos_{py_version}.zip"
    # Linux (and any other Unix-like system as a best-effort fallback)
    return base + f"extlibs_linux_{py_version}.zip"


class DownloadAndUnzip(QDialog):
    """Modal dialog that downloads a ZIP from *url* and extracts it to *output_path*."""

    def __init__(self, url: str, output_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Co-registration Plugin Installation")
        self.setModal(True)
        self.setMinimumWidth(420)
        # Keep the dialog visible above the QGIS main window
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.url = url
        self.output_path = output_path
        self._zip_fd: int | None = None
        self._zip_path: str | None = None
        self._cancelled = False

        self.progress_label = QLabel("Downloading additional libraries...", self)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self._on_cancel)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(progress_layout)
        main_layout.addLayout(button_layout)
        self.adjustSize()

        self.show()
        QApplication.processEvents()

        self._zip_fd, self._zip_path = tempfile.mkstemp(suffix=".zip")

        downloaded_ok = self.download_file()
        extracted_ok = (not self._cancelled) and downloaded_ok and self.extract_zip()

        if extracted_ok:
            self.progress_label.setText("Done!")
            self.progress_bar.setValue(100)
        elif not self._cancelled:
            _log("Failed to download/extract extra libraries.", level="Critical")
            QMessageBox.critical(
                None,
                "Co-registration Plugin: Error installing libs",
                (
                    "Error downloading and extracting additional Python packages"
                    " required for Co-registration Plugin.\n\n"
                    "Read the install instructions here:\n"
                    "https://github.com/SMByC/Coregistration-Qgis-processing#installation"
                ),
                QMessageBox.StandardButton.Ok,
            )

        self._cleanup()

    def _on_cancel(self) -> None:
        self._cancelled = True
        self._cleanup()

    def _cleanup(self) -> None:
        """Release the temporary ZIP file and close the dialog."""
        if self._zip_fd is not None:
            try:
                os.close(self._zip_fd)
            except OSError:
                pass
            self._zip_fd = None

        if self._zip_path and os.path.exists(self._zip_path):
            try:
                os.remove(self._zip_path)
            except OSError:
                pass
            self._zip_path = None

        try:
            self.deleteLater()
            self.accept()
        except RuntimeError:
            pass

    def download_file(self) -> bool:
        """Download ``self.url`` into the temporary ZIP file.

        Returns ``True`` on success, ``False`` on error or cancellation.
        """
        if self._zip_path is None:
            return False
        try:
            req = urllib.request.Request(self.url, headers={"User-Agent": "Coregistration-Plugin"})
            with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as response:  # nosec B310
                raw_length = response.getheader("Content-Length")
                total_length: int | None = int(raw_length) if raw_length else None
                # Use indeterminate mode when Content-Length is not provided
                self.progress_bar.setRange(0, 100 if total_length else 0)

                with open(self._zip_path, "wb") as fh:
                    downloaded = 0
                    while not self._cancelled:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        fh.write(chunk)
                        downloaded += len(chunk)
                        if total_length:
                            self.progress_bar.setValue(int(downloaded * 100 / total_length))
                        QApplication.processEvents()

            self.progress_bar.setRange(0, 100)
            return not self._cancelled
        except Exception as exc:
            _log(f"Download error: {exc}", level="Critical")
            return False

    def extract_zip(self) -> bool:
        """Extract the downloaded ZIP to ``self.output_path``.

        All member paths are validated against *output_path* before any file
        is written (zip-slip attack prevention).
        """
        if self._zip_path is None:
            return False
        self.progress_label.setText("Extracting libraries...")
        QApplication.processEvents()
        try:
            real_output = os.path.realpath(self.output_path)
            with zipfile.ZipFile(self._zip_path, "r") as zf:
                for member in zf.infolist():
                    member_dest = os.path.realpath(os.path.join(real_output, member.filename))
                    if not (member_dest == real_output or member_dest.startswith(real_output + os.sep)):
                        raise ValueError(f"Zip-slip rejected for entry: {member.filename!r}")
                zf.extractall(real_output)
            return True
        except Exception as exc:
            _log(f"Extraction error: {exc}", level="Critical")
            return False


def get_extlibs_install_path() -> str:
    """Return the ``extlibs`` directory inside this plugin's QGIS profile folder."""
    return os.path.join(
        QgsApplication.qgisSettingsDirPath(),
        "python",
        "plugins",
        "Coregistration",
        "extlibs",
    )


def install() -> None:
    """Download and install the extra Python libraries required by this plugin."""
    # Remove legacy platform-specific extlibs directories from older versions
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for old_name in ("extlibs_linux", "extlibs_windows", "extlibs_macos"):
        shutil.rmtree(os.path.join(plugin_dir, old_name), ignore_errors=True)

    extlibs_dir = get_extlibs_install_path()
    if os.path.isdir(extlibs_dir):
        _log(f"Removing existing extlibs at: {extlibs_dir}")
        shutil.rmtree(extlibs_dir, ignore_errors=True)
    os.makedirs(extlibs_dir, exist_ok=True)

    url = _get_extlibs_url()
    _log(f"Installing extra libs to: {extlibs_dir}")
    _log(f"Download URL: {url}")
    DownloadAndUnzip(url, extlibs_dir)
