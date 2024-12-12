"""Provide a service class for the collection management.

Copyright (c) 2024 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from pathlib import Path
import sys

from mvclib.controller.sub_controller import SubController
from nvcollection.collection_view import CollectionView
import tkinter as tk


class CollectionService(SubController):
    INI_FILENAME = 'collection.ini'
    INI_FILEPATH = '.novx/config'
    SETTINGS = dict(
        last_open='',
        tree_width='260',
        window_size='600x300',
    )
    OPTIONS = {}
    ICON = 'cLogo32'

    def __init__(self, model, view, controller):
        super().initialize_controller(model, view, controller)

        #--- Load configuration.
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            configDir = f'{homeDir}/{self.INI_FILEPATH}'
        except:
            configDir = '.'
        self.iniFile = f'{configDir}/{self.INI_FILENAME}'
        self.configuration = self._mdl.nvService.new_configuration(
            settings=self.SETTINGS,
            options=self.OPTIONS
            )
        self.configuration.read(self.iniFile)
        self.prefs = {}
        self.prefs.update(self.configuration.settings)
        self.prefs.update(self.configuration.options)

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
        self.configuration.write(self.iniFile)

    def start_manager(self):
        if self.collectionView:
            if self.collectionView.isOpen:
                if self.collectionView.state() == 'iconic':
                    self.collectionView.state('normal')
                self.collectionView.lift()
                self.collectionView.focus()
                return

        __, x, y = self._ui.root.geometry().split('+')
        offset = 100
        windowPosition = f'+{int(x)+offset}+{int(y)+offset}'
        self.collectionView = CollectionView(
            self._mdl,
            self._ui,
            self._ctrl,
            windowPosition,
            self.prefs
            )
        self.collectionView.iconphoto(False, self.icon)

