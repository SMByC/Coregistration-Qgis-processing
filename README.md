# Coregistration

Image to image co-registration processing Qgis plugin, converting the target image using a pixel alignment process based on a reference image.

![](docs/img/coregistration.png)

> This is an early version that includes the most basic type of co-registration, new methods for co-registration are coming.

It generates a new raster file base on the target image with all properties from the reference image in order to have an image to image co-registration. The pixel alignment process include:

* Reprojection (only if needed)
* Resampling (only if pixel sizes are different)
* Extent/bounds adjustment
* Apply a mask as an area of interest (optional)

## Installation

The plugin can be installed using the QGIS Plugin Manager, go into Qgis to `Plugins` menu and `Manage and install plugins`, in `All` section search for `Coregistration`.

The plugin will be available in the `Processing Toolbox` or you can search and open it directly from the `Statusbar`.

### Basic demo

You can test it using a simple basic example in this [zip file](files_demo.zip?raw=true) with a reference file and two target images.

## Source code

The official version control system repository of the plugin:
[https://github.com/SMByC/Coregistration-Qgis-processing](https://github.com/SMByC/Coregistration-Qgis-processing)

## Issue Tracker

Issues, ideas and enhancements: [https://github.com/SMByC/Coregistration-Qgis-processing/issues](https://github.com/SMByC/Coregistration-Qgis-processing/issues)

## License

This plugin is a free/libre software and is licensed under the GNU General Public License.
