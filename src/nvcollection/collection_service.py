"""Provide a service class for the collection management.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from pathlib import Path
import sys

from nvcollection.collection_view import CollectionView
from nvlib.controller.sub_controller import SubController
import tkinter as tk


class CollectionService(SubController):
    INI_FILENAME = 'collection.ini'
    INI_FILEPATH = '.novx/config'
    SETTINGS = dict(
        last_open='',
        window_geometry='600x300',
        right_frame_width=350,
    )
    OPTIONS = {}
    ICON = 'collection'

    def __init__(self, model, view, controller):
        self._mdl = model
        self._ui = view
        self._ctrl = controller

        #--- Load configuration.
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            configDir = f'{homeDir}/{self.INI_FILEPATH}'
        except:
            configDir = '.'
        self.configuration = self._mdl.nvService.new_configuration(
            settings=self.SETTINGS,
            options=self.OPTIONS,
            filePath=f'{configDir}/{self.INI_FILENAME}',
        )
        self.configuration.read()
        self.prefs = {}
        self.prefs.update(self.configuration.settings)
        self.prefs.update(self.configuration.options)
        globalPrefs = self._ctrl.get_preferences()
        self.prefs['color_text_fg'] = globalPrefs['color_text_fg']
        self.prefs['color_text_bg'] = globalPrefs['color_text_bg']

        # Set window icon.
        try:
            path = os.path.dirname(sys.argv[0])
            if not path:
                path = '.'
            self.icon = tk.PhotoImage(file=f'{path}/icons/{self.ICON}.png')
        except:
            self.icon = None

        self.collectionView = None

    def on_quit(self):
        """Write back the configuration file.
        
        Overrides the superclass method.
        """
        if self.collectionView:
            if self.collectionView.isOpen:
                self.collectionView.on_quit()

        #--- Save configuration
        for keyword in self.prefs:
            if keyword in self.configuration.options:
                self.configuration.options[keyword] = self.prefs[keyword]
            elif keyword in self.configuration.settings:
                self.configuration.settings[keyword] = self.prefs[keyword]
        self.configuration.write()

    def start_manager(self):
        if self.collectionView:
            if self.collectionView.isOpen:
                if self.collectionView.state() == 'iconic':
                    self.collectionView.state('normal')
                self.collectionView.lift()
                self.collectionView.focus()
                return

        self.collectionView = CollectionView(
            self._mdl,
            self._ui,
            self._ctrl,
            self.prefs,
        )
        if self.icon:
            self.collectionView.iconphoto(False, self.icon)

