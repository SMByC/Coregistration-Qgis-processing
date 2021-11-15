from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox

from Coregistration.utils.extra_deps import load_install_extra_deps, WaitDialog


def init_dependencies():
    app = QCoreApplication.instance()
    dialog = None
    log = ''
    try:
        for msg_type, msg_val in load_install_extra_deps():
            app.processEvents()
            if msg_type == 'log':
                log += msg_val
            elif msg_type == 'needs_install':
                dialog = WaitDialog(None, 'Co-Registration - installing dependencies')
            elif msg_type == 'install_done':
                dialog.accept()
    except Exception as e:
        if dialog:
            dialog.accept()
        msg = "Error loading Arosics, this plugin requires additional Python packages to work. " \
              "<a href='https://github.com/SMByC/Coregistration-Qgis-processing#installation'>" \
              "See more</a>.<br/><br/>"
        QMessageBox.critical(None, 'Co-Registration - Missing dependencies', msg, QMessageBox.Ok)
        raise RuntimeError('\nCo-Registration: Error installing Python packages. Read install instruction: '
                           'https://github.com/SMByC/Coregistration-Qgis-processing\nLog:\n' + log) from e

