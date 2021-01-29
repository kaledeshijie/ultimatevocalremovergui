"""
Main Application
"""
# pylint: disable=no-name-in-module, import-error
# -GUI-
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6.QtGui import Qt
# -Root imports-
from .resources.resources_manager import ResourcePaths
from .windows import (mainwindow, settingswindow)
# -Other-
import os
import sys
# Code annotation
from typing import (Dict, List, Optional)

# Change the current working directory to the directory
# this file sits in
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
print(base_path)

os.chdir(base_path)  # Change the current working directory to the base path


class CustomApplication(QtWidgets.QApplication):
    def __init__(self):
        # -Init Application-
        # Suppress QT Warnings
        os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1"
        # ...Application settings here...
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)
        super(CustomApplication, self).__init__(sys.argv)

        # -Create Managers-
        self.settings = QtCore.QSettings('UVR', 'Ultimate Vocal Remover')
        self.resources = ResourcePaths()
        self.translator = Translator(self)
        self.threadpool = QtCore.QThreadPool(self)
        # -Load Windows-
        # Collection of windows
        self.windows = {
            'main': MainWindow(self),
            'settings': SettingsWindow(self),
        }
        self.setup_late_widgets()

        self.windows['main'].show()

    def setup_late_widgets(self):
        """
        Set up binds and images for widgets that interact
        with widgets/methods from other windows

        (Binds cannot be set to widgets/methods that have not been initialized yet)
        """
        export_button = self.windows['settings'].ui.pushButton_exportDirectory
        export_button.clicked.connect(lambda: self.windows['main'].write_to_command('AYAAYAYA'))


class Translator:
    def __init__(self, app: CustomApplication):
        self.app = app
        self._translator = QtCore.QTranslator(self.app)
        # Load language -> if not specified, try loading system language
        self.load_language(self.app.settings.value('language',
                                                   QtCore.QLocale.English))

    def load_language(self, language: QtCore.QLocale.Language = QtCore.QLocale.English):
        """
        Load specified language by file name

        Default is english
        """
        if language == QtCore.QLocale.English:
            # Language is either not specified or english
            self.app.removeTranslator(self._translator)
        else:
            # Language was specified
            language_str = QtCore.QLocale.languageToString(language).lower()
            translation_path = os.path.join(self.app.resources.localizationDir, f'{language_str}.qm')
            if not os.path.isfile(translation_path):
                # Translation does not exist
                # Load default language (english)
                self.load_language()
                return
            # Load language
            self._translator.load(translation_path)
            self.app.installTranslator(self._translator)

        if hasattr(self.app, 'windows'):
            # -Application already initialized windows-
            # Update translation on all windows
            for window in self.app.windows.values():
                window.update_translation()
            # Update checked language buttons
            for button in self.app.windows['settings'].ui.frame_languages.findChildren(QtWidgets.QPushButton):
                language_str = QtCore.QLocale.languageToString(language).lower()
                button_name = f'pushButton_{language_str}'
                if button.objectName() == button_name:
                    # Language found
                    button.setChecked(True)
                else:
                    # Not selected language
                    button.setChecked(False)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, app: CustomApplication):
        super(MainWindow, self).__init__()
        self.ui = mainwindow.Ui_MainWindow()
        self.ui.setupUi(self)
        self.app = app

        self.setup_widgets()
        self.load_settings()

    def setup_widgets(self):
        """
        Set up binds and images for this window's widgets
        (Only run on window initialization)
        """
        # -Override Events-
        # Music file drag & drop
        self.ui.label_musicFiles.dragEnterEvent = self.label_musicFiles_dragEnterEvent
        self.ui.label_musicFiles.dropEvent = self.label_musicFiles_dropEvent

        # -Bind Widgets-
        self.ui.pushButton_settings.clicked.connect(self.pushButton_settings_clicked)

        # -Load Images-
        # Settings button
        icon = QtGui.QPixmap(ResourcePaths.images.settings)
        self.ui.pushButton_settings.setIcon(icon)
        self.ui.pushButton_settings.setIconSize(QtCore.QSize(25, 25))

    def write_to_command(self, text: str):
        """
        Write to the command line
        """
        self.ui.textBrowser_command.append(text)
        if hasattr(self.app, 'windows'):
            self.app.windows['settings'].ui.pushButton_clearCommand.setVisible(True)

    # -Widgets-
    def pushButton_settings_clicked(self):
        """
        Open the settings window
        """
        # Reshow window
        self.app.windows['settings'].show()
        # Focus window
        self.app.windows['settings'].activateWindow()
        self.app.windows['settings'].raise_()

    def label_musicFiles_dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        """
        Check whether the files the user is dragging over the widget
        is valid or not
        """
        if event.mimeData().urls():
            # URLs dragged
            event.accept()
        else:
            event.ignore()

    def label_musicFiles_dropEvent(self, event: QtGui.QDropEvent):
        """
        Assign dropped paths to list
        """
        input_paths = []
        for url in event.mimeData().urls():
            input_paths.append(url.toLocalFile())
        self.app.settings.setValue('seperation/input_paths', input_paths)
        self.ui.label_musicFiles.setText(f'Total Music File/s: {len(input_paths)}')

    def load_settings(self):
        """
        Load the saved settings for this window
        """
        # -Default Settings-
        # Window is centered on primary window
        default_geometry = self.geometry()
        point = QtCore.QPoint()
        point.setX(self.app.primaryScreen().size().width() / 2)
        point.setY(self.app.primaryScreen().size().height() / 2)
        default_geometry.moveCenter(point)

        # -Load Settings-
        self.app.settings.beginGroup('mainwindow')
        geometry = self.app.settings.value('geometry',
                                           default_geometry)
        self.app.settings.endGroup()

        # -Apply Settings-
        self.setGeometry(geometry)

    def save_settings(self):
        """
        Save the settings for this window
        """
        # -Save Settings-
        self.app.settings.beginGroup('mainwindow')
        self.app.settings.setValue('geometry',
                                   self.geometry())
        self.app.settings.endGroup()
        # Commit Save
        self.app.settings.sync()

    def closeEvent(self, event: QtCore.QEvent):
        """
        Catch close event of this window to save data
        """
        self.save_settings()

        event.accept()

    def update_translation(self):
        """
        Update translation of this window
        """
        self.ui.retranslateUi(self)


class SettingsWindow(QtWidgets.QWidget):
    def __init__(self, app: CustomApplication):
        super(SettingsWindow, self).__init__()
        self.ui = settingswindow.Ui_SettingsWindow()
        self.ui.setupUi(self)
        self.app = app

        self.setup_widgets()
        self.load_settings()
        self.menu_loadPage(index=0)

    def setup_widgets(self):
        """
        Set up binds and images for this window's widgets
        (Only run on window initialization)
        """
        # -Load Images-
        # Flags
        for button in self.ui.frame_languages.findChildren(QtWidgets.QPushButton):
            language = button.objectName().split('_')[1]
            button.setText('')

            # -Prepare rounded image-
            # Load original image
            img_path = getattr(ResourcePaths.images.flags, language)
            origin_img = QtGui.QPixmap(img_path)
            origin_img = origin_img.scaled(button.width(), button.height(),
                                           mode=Qt.TransformationMode.SmoothTransformation)
            # Create new image based on origins size
            rounded = QtGui.QPixmap(origin_img.size())
            rounded.fill(Qt.transparent)
            # Add rounded clip area
            path = QtGui.QPainterPath()
            path.addRoundedRect(2.75, 2.75, rounded.width() - 5.5, rounded.height() - 5.5, 8, 8)
            # Paint original image on new image
            painter = QtGui.QPainter(rounded)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, origin_img.width(), origin_img.height(), origin_img)
            painter.end()

            # Set new image to icon
            button.setIcon(QtGui.QIcon(rounded))
            button.setIconSize(rounded.size())
        # Icons
        folder_img = QtGui.QPixmap(ResourcePaths.images.folder)
        self.ui.pushButton_exportDirectory.setIcon(folder_img)
        self.ui.pushButton_exportDirectory.setIconSize(QtCore.QSize(18, 18))

        # -Bing Widgets-
        # Menu
        self.menu_group = QtWidgets.QButtonGroup(self)  # Menu group
        self.menu_group.addButton(self.ui.radioButton_seperationSettings,
                                  id=0)
        self.menu_group.addButton(self.ui.radioButton_shortcuts,
                                  id=1)
        self.menu_group.addButton(self.ui.radioButton_customization,
                                  id=2)
        self.menu_group.addButton(self.ui.radioButton_preferences,
                                  id=3)
        self.menu_group.buttonClicked.connect(lambda btn:
                                              self.menu_loadPage(index=self.menu_group.id(btn)))
        # Flags
        self.ui.pushButton_english.clicked.connect(lambda: self.app.translator.load_language(QtCore.QLocale.English))
        self.ui.pushButton_german.clicked.connect(lambda: self.app.translator.load_language(QtCore.QLocale.German))
        self.ui.pushButton_japanese.clicked.connect(lambda: self.app.translator.load_language(QtCore.QLocale.Japanese))
        self.ui.pushButton_filipino.clicked.connect(lambda: self.app.translator.load_language(QtCore.QLocale.Filipino))
        # Buttons
        self.ui.pushButton_clearCommand.clicked.connect(self.pushButton_clearCommand_clicked)

    def menu_loadPage(self, index: int):
        """
        Load the given menu page by index

        Also adjust minimum size of window
        """
        # Load Page
        stackedWidget = self.ui.stackedWidget_11
        stackedWidget.setCurrentIndex(index)
        # Check Radiobutton
        self.menu_group.button(index).setChecked(True)

        # Find Frame which specifies the minimum width
        page = stackedWidget.currentWidget()
        min_width = page.property('minimumFrameWidth')
        stackedWidget.setMinimumWidth(min_width)

    def pushButton_clearCommand_clicked(self):
        """
        Clear the command line
        """
        self.app.windows['main'].ui.textBrowser_command.clear()
        self.ui.pushButton_clearCommand.setVisible(False)

    def load_settings(self):
        """
        Load the saved settings for this window
        """
        # -Default Settings-
        # Window is centered on primary window
        default_geometry = self.geometry()
        point = QtCore.QPoint()
        point.setX(self.app.primaryScreen().size().width() / 2)
        point.setY(self.app.primaryScreen().size().height() / 2)
        default_geometry.moveCenter(point)

        # -Load Settings-
        self.app.settings.beginGroup('settingswindow')
        geometry = self.app.settings.value('geometry',
                                           default_geometry)
        self.app.settings.endGroup()

        # -Apply Settings-
        self.setGeometry(geometry)

    def save_settings(self):
        """
        Save the settings for this window
        """
        # -Save Settings-
        self.app.settings.beginGroup('settingswindow')
        self.app.settings.setValue('geometry',
                                   self.geometry())
        self.app.settings.endGroup()
        # Commit Save
        self.app.settings.sync()

    def closeEvent(self, event: QtCore.QEvent):
        """
        Catch close event of this window to save data
        """
        self.save_settings()

        event.accept()

    def update_translation(self):
        """
        Update translation of this window
        """
        self.ui.retranslateUi(self)


def run():
    """Start the application\n
    Run 'sys.exit(app.exec_())' after this method has been called
    """
    app = CustomApplication()

    sys.exit(app.exec_())
    # Create Manager

    # winManager = WindowManager(windows)


# def load_settings(self):
#     """
#     Load the saved settings for this window
#     """
#     # -Default Settings-
#     # Window is centered on primary window
#     default_geometry = self.geometry()
#     point = QtCore.QPoint()
#     point.setX(self.app.primaryScreen().size().width() / 2)
#     point.setY(self.app.primaryScreen().size().height() / 2)
#     default_geometry.moveCenter(point)

#     # -Load Settings-
#     self.app.settings.beginGroup('settingswindow')
#     geometry = self.app.settings.value('geometry',
#                                         default_geometry)
#     self.app.settings.endGroup()

#     # -Apply Settings-
#     self.setGeometry(geometry)

# def save_settings(self):
#     """
#     Save the settings for this window
#     """
#     # -Save Settings-
#     self.app.settings.beginGroup('settingswindow')
#     self.app.settings.setValue('geometry',
#                                 self.geometry())
#     self.app.settings.endGroup()
#     # Commit Save
#     self.app.settings.sync()
