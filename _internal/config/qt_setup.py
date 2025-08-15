# qt_setup.py - Qt application initialization and configuration

import os
import sys

def setup_qt_environment():
    """Set up Qt environment variables for high-DPI scaling."""
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

def create_application():
    """Create and configure the Qt application."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    
    setup_qt_environment()
    
    # Set high DPI policy before creating application - this MUST be called first
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv if len(sys.argv) > 1 else [])
    
    # Additional application setup can go here
    return app
