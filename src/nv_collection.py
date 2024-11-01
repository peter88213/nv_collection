"""A project collection manager plugin for novelibre.

Requires Python 3.6+
Copyright (c) 2024 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""
import os
from pathlib import Path
import sys

from nvcollectionlib.nvcollection_globals import _
from nvcollectionlib.collection_manager import CollectionManager
from nvcollectionlib.nvcollection_globals import FEATURE
from nvcollectionlib.nvcollection_globals import open_help
from nvlib.plugin.plugin_base import PluginBase
import tkinter as tk


class Plugin(PluginBase):
    """novelibre collection manager plugin class."""
    VERSION = '@release'
    API_VERSION = '4.3'
    DESCRIPTION = 'A book/series collection manager'
    URL = 'https://github.com/peter88213/nv_collection'
    ICON = 'cLogo32'

    INI_FILEPATH = '.novx/config'

    def install(self, model, view, controller, prefs=None):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            model -- reference to the main model instance of the application.
            view -- reference to the main view instance of the application.
            controller -- reference to the main controller instance of the application.

        Optional arguments:
            prefs -- deprecated. Please use controller.get_preferences() instead.
        
        Overrides the superclass method.
        """
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        self._collectionManager = None

        # Create a submenu.
        self._ui.fileMenu.insert_command(0, label=FEATURE, command=self._start_manager)
        self._ui.fileMenu.insert_separator(1)
        self._ui.fileMenu.entryconfig(FEATURE, state='normal')

        # Add an entry to the Help menu.
        self._ui.helpMenu.add_command(label=_('Collection plugin Online help'), command=open_help)

        # Set window icon.
        self.sectionEditors = {}
        try:
            path = os.path.dirname(sys.argv[0])
            if not path:
                path = '.'
            self._icon = tk.PhotoImage(file=f'{path}/icons/{self.ICON}.png')
        except:
            self._icon = None

    def on_quit(self):
        """Write back the configuration file.
        
        Overrides the superclass method.
        """
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.on_quit()

    def _start_manager(self):
        if self._collectionManager:
            if self._collectionManager.isOpen:
                if self._collectionManager.state() == 'iconic':
                    self._collectionManager.state('normal')
                self._collectionManager.lift()
                self._collectionManager.focus()
                return

        __, x, y = self._ui.root.geometry().split('+')
        offset = 300
        windowGeometry = f'+{int(x)+offset}+{int(y)+offset}'
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            configDir = f'{homeDir}/{self.INI_FILEPATH}'
        except:
            configDir = '.'
        self._collectionManager = CollectionManager(self._mdl, self._ui, self._ctrl, windowGeometry, configDir)
        self._collectionManager.iconphoto(False, self._icon)

