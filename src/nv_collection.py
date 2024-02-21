"""A project collection manager plugin for novelyst.

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
import webbrowser

from nvcollectionlib.collection_manager import CollectionManager
from nvcollectionlib.nvcollection_globals import APPLICATION
from nvcollectionlib.nvcollection_globals import _
import tkinter as tk

DEFAULT_FILE = 'collection.pwc'


class Plugin:
    """novelyst collection manager plugin class."""
    VERSION = '@release'
    API_VERSION = '2.1'
    DESCRIPTION = 'A book/series collection manager'
    URL = 'https://github.com/peter88213/nv_collection'
    _HELP_URL = f'https://peter88213.github.io/{_("nvhelp-en")}/nv_collection/'
    ICON = 'cLogo32'

    def install(self, model, view, controller, prefs):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            controller -- reference to the main controller instance of the application.
            view -- reference to the main view instance of the application.
        """
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        self._collectionManager = None

        # Create a submenu.
        self._ui.fileMenu.insert_command(0, label=APPLICATION, command=self._start_manager)
        self._ui.fileMenu.insert_separator(1)
        self._ui.fileMenu.entryconfig(APPLICATION, state='normal')

        # Add an entry to the Help menu.
        self._ui.helpMenu.add_command(label=_('Collection plugin Online help'), command=lambda: webbrowser.open(self._HELP_URL))

        # Set window icon.
        self.sectionEditors = {}
        try:
            path = os.path.dirname(sys.argv[0])
            if not path:
                path = '.'
            self._icon = tk.PhotoImage(file=f'{path}/icons/{self.ICON}.png')
        except:
            self._icon = None

    def _start_manager(self):
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.lift()
                self._collectionManager.focus()
                return

        __, x, y = self._ui.root.geometry().split('+')
        offset = 300
        windowGeometry = f'+{int(x)+offset}+{int(y)+offset}'
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            configDir = f'{homeDir}/.novx/config'
        except:
            configDir = '.'
        self._collectionManager = CollectionManager(self._mdl, self._ui, self._ctrl, windowGeometry, configDir)
        self._collectionManager.iconphoto(False, self._icon)

    def on_quit(self):
        """Write back the configuration file."""
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.on_quit()
