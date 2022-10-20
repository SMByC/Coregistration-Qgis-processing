# Coregistration

Image to image automatic co-registration processing Qgis plugin. This plugin uses AROSICS to perform automatic subpixel co-registration of image datasets based on an image matching approach working in the frequency domain.

![](docs/img/coregistration.png)

_This plugin has three algorithms:_

### (1) Basic pixel alignment

This Qgis processing generates a new raster file base on the target image with all properties from the reference image. This process don't check the content of the pixel, this process adjusts the target image to the closest pixel alignment based on the reference image. The basic pixel alignment process include:

* Reprojection (only if needed)
* Resampling (only if pixel sizes are different)
* Extent/bounds adjustment

For a real image to image co-registration use the following two algorithms instead

## Automated global and local image to image co-registration

Detects and corrects global and local X/Y shifts misregistrations between two input images in the subpixel scale using the content of the pixels in the matching window. Perform automatic subpixel co-registration of image datasets based on an image matching approach working in the frequency domain, combined with a multistage workflow for effective detection of false-positives [1].
        
It is designed to robustly handle the typical difficulties of multi-sensoral/multi-temporal images. Clouds are automatically handled by the implemented outlier detection algorithms [1].

### (2) Global

This global algorithm is useful when the target image requires just one shifts in distance and direction in the whole image.

### (3) Local

This local algorithm is useful when the target image requires different pixel shifts in distances and directions. The precision of this is based on mainly in two input parameters: tie point grid resolution and matching window size. This is significantly more comprehensive and slower than global algorithm.

*[1] These algorithms use AROSICS software developed by Daniel Scheffler, for more info <a href="https://danschef.git-pages.gfz-potsdam.de/arosics/doc/">url</a> and <a href="https://doi.org/10.3390/rs9070676">paper</a>.

## Installation

The plugin can be installed using the QGIS Plugin Manager, go into Qgis to `Plugins` menu and `Manage and install plugins`, in `All` section search for `Coregistration`.

The plugin will be available in the `Processing Toolbox` or you can search and open it directly from the `Statusbar`.

> *Dependencies:* 
    This plugin requires additional Python packages (`AROSICS` and its dependencies), that are generally not part of QGIS's Python. 

#### Windows
For Windows users download and install the plugin using the zip `Coregistration_all_in_one_win.zip` in [releases](https://github.com/SMByC/Coregistration-Qgis-processing/releases) (alternative [link](https://drive.google.com/uc?export=download&confirm=gzst&id=1RdtkZnxR53xFpvgdssampyvSiANwiZdZ)) with all the libs and dependencies inside. This should work directly without any additional steps with a Qgis version >= 3.18 on a 64bit Windows system, if you have issues with this try with the alternative installation below.

> *Note:* For uninstall/update this plugin using this all-in-one in Windows, you must first deactivate, restart Qgis, uninstall/update it and finally activate it again.

#### Linux/Mac 
The plugin try to install all the dependencies for you in a local folder automatically in the installation process. If you want to minimize the local installation of dependencies of this plugin or fix dependency issues, a good idea is before install the plugin, install the following packages in your system: `matplotlib`, `cartopy`, `geopandas`, `plotly`, `scikit-image`

### Alternative installation

If you have problems with the dependencies, the best options to solve it is use [conda](https://docs.conda.io/en/latest/miniconda.html) and install AROSICS and Qgis (from the conda shell):

```bash
conda install -c conda-forge arosics qgis
```

After that open Qgis from the shell with `qgis` command. Then install the plugin.

## Source code

The official version control system repository of the plugin:
[https://github.com/SMByC/Coregistration-Qgis-processing](https://github.com/SMByC/Coregistration-Qgis-processing)

## Issue Tracker

Issues, ideas and enhancements: [https://github.com/SMByC/Coregistration-Qgis-processing/issues](https://github.com/SMByC/Coregistration-Qgis-processing/issues)

## License

This plugin is a free/libre software and is licensed under the GNU General Public License.
