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
import os
import platform
import shutil
import tempfile
import urllib.request
import zipfile

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication, QDialog, QProgressBar, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox


class DownloadAndUnzip(QDialog):
    def __init__(self, url, output_path):
        super().__init__()
        self.setWindowTitle("Image co-registration plugin Installation")
        self.setModal(True)
        self.setFixedSize(500, 200)

        self.url = url
        self.output_path = os.path.join(output_path, "Coregistration", "extlibs")
        os.makedirs(self.output_path, exist_ok=True)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.progress_label = QLabel("Downloading additional libraries...", self)
        self.progress_label.setAlignment(Qt.AlignCenter)

        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.close_dialog)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(progress_layout)
        main_layout.addLayout(button_layout)


        self.show()

        self.zip_file_handle, self.zip_file = tempfile.mkstemp(suffix=".zip")

        if self.download_file() and self.extract_zip():
            self.progress_label.setText("Done!")
            self.progress_bar.setValue(100)
        else:
            msg = "Error downloading and extracting additional Python packages required for Co-registration Plugin. " \
                  "Read the install instructions here:\n\n" \
                  "https://github.com/SMByC/Coregistration-Qgis-processing#installation"
            QMessageBox.critical(None, 'Co-registration Plugin: Error installing libs', msg, QMessageBox.Ok)

        self.close_dialog()

    def close_dialog(self):
        try:
            os.close(self.zip_file_handle)
            os.remove(self.zip_file)
            self.deleteLater()
            self.accept()
        except:
            pass

    def download_file(self):
        try:
            response = urllib.request.urlopen(self.url)
            total_length = int(response.getheader('Content-Length'))

            with open(self.zip_file, 'wb') as f:
                downloaded_bytes = 0
                while True:
                    buffer = response.read(1024)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded_bytes += len(buffer)

                    progress = int(downloaded_bytes * 100 / total_length)
                    self.progress_bar.setValue(progress)
                    QApplication.processEvents()
            return True
        except Exception as e:
            print("Error downloading: ", e)
            return False

    def extract_zip(self):
        try:
            self.progress_label.setText("Extracting libraries...")
            QApplication.processEvents()
            with zipfile.ZipFile(self.zip_file, 'r') as zip_ref:
                zip_ref.extractall(self.output_path)
            return True
        except Exception as e:
            print("Error unzipping: ", e)
            return False


def clean():
    # cleanup old version of extra libs
    old_extra_libs_path_list = ["extlibs_linux", "extlibs_windows", "extlibs_macos"]
    for old_extra_libs_path in old_extra_libs_path_list:
        old_extra_libs_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), old_extra_libs_path))
        shutil.rmtree(old_extra_libs_path, ignore_errors=True)

    extra_libs_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "extlibs"))
    shutil.rmtree(extra_libs_path, ignore_errors=True)
    if os.path.isdir(extra_libs_path):
        # show a message to the user to restart QGIS
        msg = "To complete the installation of the Co-registration Plugin, please restart QGIS."
        QMessageBox.information(None, 'Co-registration Plugin', msg, QMessageBox.Ok)
        return False
    return True


def install():
    # define the Qgis plugins directory and url by OS
    url = "https://github.com/SMByC/Coregistration-Qgis-processing/releases/download/24.12/"
    py_version = 'py' + str(platform.python_version_tuple()[0]) + '.' + str(platform.python_version_tuple()[1])
    if platform.system() == "Windows":
        qgis_plugins_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'QGIS', 'QGIS3', 'profiles', 'default', 'python', 'plugins')
        url += "extlibs_windows_{}.zip".format(py_version)
    elif platform.system() == "Linux":
        qgis_plugins_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'QGIS', 'QGIS3', 'profiles', 'default', 'python', 'plugins')
        url += "extlibs_linux_{}.zip".format(py_version)
    elif platform.system() == "Darwin":
        qgis_plugins_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'QGIS', 'QGIS3', 'profiles', 'default', 'python', 'plugins')
        url += "extlibs_macos_{}.zip".format(py_version)

    # install the extra libraries
    DownloadAndUnzip(url, qgis_plugins_dir)
