# Coregistration

Image to image automatic co-registration processing Qgis plugin. This plugin use Arosics to perform automatic subpixel co-registration of image datasets based on an image matching approach working in the frequency domain.

![](docs/img/coregistration.png)

This plugin has three algorithms:

### Basic pixel alignment

This Qgis processing generates a new raster file base on the target image with all properties from the reference image. This process don't check the content of the pixel, this process adjusts the target image to the closest pixel alignment based on the reference image. The basic pixel alignment process include:

* Reprojection (only if needed)
* Resampling (only if pixel sizes are different)
* Extent/bounds adjustment

For a real image to image co-registration use the following two algorithms instead

### Automated global and local image to image co-registration

Detects and corrects global and local X/Y shifts misregistrations between two input images in the subpixel scale using the content of the pixels in the matching window. Perform automatic subpixel co-registration of image datasets based on an image matching approach working in the frequency domain, combined with a multistage workflow for effective detection of false-positives [1].
        
It is designed to robustly handle the typical difficulties of multi-sensoral/multi-temporal images. Clouds are automatically handled by the implemented outlier detection algorithms [1].

#### Global

This global algorithm is useful when the target image requires just one shifts in distance and direction in the whole image.

#### Local

This local algorithm is useful when the target image requires different pixel shifts in distances and directions. The precision of this is based on mainly in two input parameters: tie point grid resolution and matching window size. This is significantly more comprehensive and slower than global algorithm.

*[1] These algorithms use Arosics software developed by Daniel Scheffler, for more info <a href="https://danschef.git-pages.gfz-potsdam.de/arosics/doc/">url</a> and <a href="https://doi.org/10.3390/rs9070676">paper</a>.

## Installation

The plugin can be installed using the QGIS Plugin Manager, go into Qgis to `Plugins` menu and `Manage and install plugins`, in `All` section search for `Coregistration`.

The plugin will be available in the `Processing Toolbox` or you can search and open it directly from the `Statusbar`.

> *Dependencies:* 
    This plugin requires additional Python packages (`Arosics` and its depends), that are generally not part of QGIS's Python. For Windows users download and reinstall the plugin with all the libs inside from [here](https://bit.ly/3FwGWS2), for Linux/Mac users the plugin try to install all the dependencies for you in a local folder automatically in the installation process.

### Alternative installation

If you have problems with the dependencies, the best options to solve it is use [conda](https://docs.conda.io/en/latest/miniconda.html) and install Arosics and Qgis (from the conda shell):

```bash
conda install -c conda-forge arosics qgis
```

After that open Qgis from the shell with `qgis` command.

## Source code

The official version control system repository of the plugin:
[https://github.com/SMByC/Coregistration-Qgis-processing](https://github.com/SMByC/Coregistration-Qgis-processing)

## Issue Tracker

Issues, ideas and enhancements: [https://github.com/SMByC/Coregistration-Qgis-processing/issues](https://github.com/SMByC/Coregistration-Qgis-processing/issues)

## License

This plugin is a free/libre software and is licensed under the GNU General Public License.
