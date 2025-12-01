"""A project collection manager plugin for novelibre.

Requires Python 3.7+
Copyright (c) 2025 Peter Triesberger
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
from nvcollection.nvcollection_locale import _
from nvcollection.nvcollection_globals import FEATURE
from nvcollection.nvcollection_help import NvcollectionHelp
from nvlib.controller.plugin.plugin_base import PluginBase
from nvcollection.collection_service import CollectionService


class Plugin(PluginBase):
    """novelibre collection manager plugin class."""
    VERSION = '@release'
    API_VERSION = '5.43'
    DESCRIPTION = 'A book/series collection manager'
    URL = 'https://github.com/peter88213/nv_collection'

    def install(self, model, view, controller):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            model -- reference to the novelibre main model instance.
            view -- reference to the novelibre main view instance.
            controller -- reference to the novelibre main controller instance.

        Extends the superclass method.
        """
        super().install(model, view, controller)
        self.collectionService = CollectionService(model, view, controller)
        self._icon = self._get_icon('collection.png')

        #--- Configure the main menu.

        # Create a submenu.
        label = FEATURE
        self._ui.fileMenu.insert_command(
            0,
            label=label,
            image=self._icon,
            compound='left',
            command=self.start_manager,
            state='normal',
        )
        self._ui.fileMenu.insert_separator(1)

        # Add an entry to the Help menu.
        label = _('Collection plugin Online help')
        self._ui.helpMenu.add_command(
            label=label,
            image=self._icon,
            compound='left',
            command=self.open_help
        )

    def on_quit(self):
        self.collectionService.on_quit()

    def open_help(self, event=None):
        NvcollectionHelp.open_help_page()

    def start_manager(self):
        self.collectionService.start_manager()

