"""Provide a class for project collection management dialog.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from tkinter import ttk

from mvclib.widgets.index_card import IndexCard
from nvcollection.collection_view_ctrl import CollectionViewCtrl
from nvcollection.nvcollection_globals import FEATURE
from nvcollection.nvcollection_locale import _
from nvcollection.platform.platform_settings import KEYS
from nvcollection.platform.platform_settings import MOUSE
from nvcollection.platform.platform_settings import PLATFORM
import tkinter as tk


class CollectionView(tk.Toplevel, CollectionViewCtrl):

    def __init__(self, model, view, controller, windowPosition, prefs):
        super().__init__()
        self.initialize_controller(model, view, controller, prefs)

        self.title(FEATURE)
        self.statusText = ''

        self.geometry(f"{self.prefs['window_size']}{windowPosition}")
        self.lift()
        self.focus()

        #--- Main menu.
        self.mainMenu = tk.Menu(self)
        self.config(menu=self.mainMenu)

        #--- Main window.
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill='both', padx=2, pady=2, expand=True)

        #--- Paned window displaying the tree and an "index card".
        self.treeWindow = ttk.Panedwindow(self.mainWindow, orient='horizontal')
        self.treeWindow.pack(fill='both', expand=True)

        #--- The collection itself.
        self.collection = None

        #--- Tree for book selection.
        self.treeView = ttk.Treeview(self.treeWindow, selectmode='browse')
        scrollY = ttk.Scrollbar(self.treeView, orient='vertical', command=self.treeView.yview)
        self.treeView.configure(yscrollcommand=scrollY.set)
        scrollY.pack(side='right', fill='y')
        self.treeView.pack(side='left')
        self.treeWindow.add(self.treeView)
        self.treeView.bind('<<TreeviewSelect>>', self.on_select_node)
        self.treeView.bind('<<TreeviewSelect>>', self.on_select_node)
        self.treeView.bind('<Double-1>', self.open_book)
        self.treeView.bind('<Return>', self.open_book)
        self.treeView.bind('<Delete>', self.remove_node)
        self.treeView.bind('<Shift-Delete>', self.remove_series_with_books)
        self.treeView.bind(MOUSE.MOVE_NODE, self.move_node)

        #--- "Index card" in the right frame.
        self.indexCard = IndexCard(self.treeWindow, bd=2, relief='ridge')
        self.indexCard.pack(side='right')
        self.treeWindow.add(self.indexCard)
        self.indexCard.titleEntry.bind('<Return>', self.apply_changes)
        self.indexCard.titleEntry.bind('<FocusOut>', self.apply_changes)

        # Adjust the tree width.
        self.treeWindow.update()
        self.treeWindow.sashpos(0, self.prefs['tree_width'])

        # Status bar.
        self.statusBar = tk.Label(self, text='', anchor='w', padx=5, pady=2)
        self.statusBar.pack(expand=False, fill='both')
        self.statusBar.bind(MOUSE.LEFT_CLICK, self.restore_status)

        # Path bar.
        self.pathBar = tk.Label(self, text='', anchor='w', padx=5, pady=3)
        self.pathBar.pack(expand=False, fill='both')

        #--- Add menu entries.
        # File menu.
        self.fileMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('File'), menu=self.fileMenu)
        self.fileMenu.add_command(label=_('New'), command=self.new_collection)
        self.fileMenu.add_command(label=_('Open...'), command=self.open_collection)
        self.fileMenu.add_command(label=_('Save'), state='disabled', command=self.save_collection)
        self.fileMenu.add_command(label=_('Close'), state='disabled', command=self.close_collection)
        if PLATFORM == 'win':
            self.fileMenu.add_command(label=_('Exit'), accelerator=KEYS.QUIT_PROGRAM[1], command=self.on_quit)
        else:
            self.fileMenu.add_command(label=_('Quit'), accelerator=KEYS.QUIT_PROGRAM[1], command=self.on_quit)

        # Series menu.
        self.seriesMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Series'), menu=self.seriesMenu)
        self.seriesMenu.add_command(label=_('Add'), command=self.add_series)
        self.seriesMenu.add_command(label=_('Remove selected series but keep the books'), command=self.remove_series)
        self.seriesMenu.add_command(label=_('Remove selected series and books'), command=self.remove_series_with_books)

        # Book menu.
        self.bookMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Book'), menu=self.bookMenu)
        self.bookMenu.add_command(label=_('Add current project to the collection'), command=self.add_current_project)
        self.bookMenu.add_command(label=_('Remove selected book from the collection'), command=self.remove_book)
        self.bookMenu.add_command(label=_('Update book data from the current project'), command=self.update_collection)
        self.bookMenu.add_command(label=_('Update project data from the selected book'), command=self.update_project)

        # Help
        self.helpMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Help'), menu=self.helpMenu)
        self.helpMenu.add_command(label=_('Online help'), accelerator='F1', command=self.open_help)

        #--- Event bindings.
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        if PLATFORM != 'win':
            self.bind(KEYS.QUIT_PROGRAM[0], self.on_quit)
        self.bind(KEYS.OPEN_HELP[0], self.open_help)
        self.bind('<Escape>', self.restore_status)

        self.open_last_collection()
