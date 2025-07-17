"""Provide a class for project collection management dialog.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from tkinter import ttk

from nvcollection.nvcollection_globals import BOOK_PREFIX
from nvcollection.nvcollection_globals import FEATURE
from nvcollection.nvcollection_globals import SERIES_PREFIX
from nvcollection.nvcollection_locale import _
from nvcollection.commands import Commands
from nvcollection.platform.platform_settings import KEYS
from nvcollection.platform.platform_settings import MOUSE
from nvcollection.platform.platform_settings import PLATFORM
from nvlib.gui.widgets.index_card import IndexCard
import tkinter as tk


class CollectionView(tk.Toplevel, Commands):
    HEIGHT_BIAS = 20

    def __init__(self, model, view, controller, prefs):
        super().__init__()
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        self.prefs = prefs
        self.isModified = False
        self.element = None
        self.nodeId = None
        self.geometry(f"{self.prefs['window_geometry']}")

        self.title(FEATURE)
        self.statusText = ''

        self.lift()
        self.focus()

        #--- Main menu.
        self._mainMenu = tk.Menu(self)
        self.config(menu=self._mainMenu)

        #--- Path bar.
        self._pathBar = tk.Label(
            self,
            text='',
            anchor='w',
            padx=5,
            pady=3,
        )
        self._pathBar.pack(expand=False, fill='both', side='bottom')

        #--- Status bar.
        self._statusBar = tk.Label(
            self,
            text='',
            anchor='w',
            padx=5,
            pady=2,
        )
        self._statusBar.pack(expand=False, fill='both', side='bottom')
        self._statusBar.bind(MOUSE.LEFT_CLICK, self._restore_status)

        #--- Main window.
        self._mainWindow = ttk.Frame(self)
        self._mainWindow.pack(
            fill='both',
            padx=2,
            pady=2,
            expand=True,
        )

        #--- The collection itself.
        self._collection = None

        #--- Tree for book selection.
        self._treeView = ttk.Treeview(
            self._mainWindow,
            selectmode='browse',
        )
        scrollY = ttk.Scrollbar(
            self._treeView,
            orient='vertical',
            command=self._treeView.yview,
        )
        self._treeView.configure(yscrollcommand=scrollY.set)
        scrollY.pack(side='right', fill='y')
        self._treeView.pack(
            side='left',
            expand=True,
            fill='both',
        )
        self._treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self._treeView.bind('<Double-1>', self._open_book)
        self._treeView.bind('<Return>', self._open_book)
        self._treeView.bind('<Delete>', self._remove_node)
        self._treeView.bind('<Shift-Delete>', self._remove_series_with_books)
        self._treeView.bind(MOUSE.MOVE_NODE, self._move_node)

        #--- "Index card" in the right frame.
        self._indexCard = IndexCard(self._mainWindow,
            bd=2,
            relief='ridge',
            width=prefs['right_frame_width'],
        )
        self._indexCard.pack(
            side='right',
            expand=False,
            fill='both',
        )
        self._indexCard.pack_propagate(0)
        self._indexCard.titleEntry.bind('<Return>', self._apply_changes)
        self._indexCard.titleEntry.bind('<FocusOut>', self._apply_changes)

        #--- Add menu entries.
        # File menu.
        self._fileMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('File'),
            menu=self._fileMenu,
        )
        self._fileMenu.add_command(
            label=_('New'),
            command=self._create_new_collection,
        )
        self._fileMenu.add_command(
            label=_('Open...'),
            command=self._open_collection,
        )
        self._fileMenu.add_command(
            label=_('Save'),
            state='disabled',
            command=self._save_collection,
        )
        self._fileMenu.add_command(
            label=_('Close'),
            state='disabled',
            command=self._close_collection,
            )
        if PLATFORM == 'win':
            self._fileMenu.add_command(
                label=_('Exit'),
                accelerator=KEYS.QUIT_PROGRAM[1],
                command=self.on_quit,
            )
        else:
            self._fileMenu.add_command(
                label=_('Quit'),
                accelerator=KEYS.QUIT_PROGRAM[1],
                command=self.on_quit,
            )

        # Series menu.
        self._seriesMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('Series'),
            menu=self._seriesMenu,
        )
        self._seriesMenu.add_command(
            label=_('Add'),
            command=self._add_series,
        )
        self._seriesMenu.add_command(
            label=_('Remove selected series but keep the books'),
            command=self._remove_series,
        )
        self._seriesMenu.add_command(
            label=_('Remove selected series and books'),
            command=self._remove_series_with_books,
        )

        # Book menu.
        self._bookMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('Book'),
            menu=self._bookMenu,
        )
        self._bookMenu.add_command(
            label=_('Add current project to the collection'),
            command=self._add_current_project,
        )
        self._bookMenu.add_command(
            label=_('Remove selected book from the collection'),
            command=self._remove_book,
        )
        self._bookMenu.add_command(
            label=_('Update book data from the current project'),
            command=self._update_collection,
        )
        self._bookMenu.add_command(
            label=_('Update project data from the selected book'),
            command=self._update_project,
        )

        # Help
        self._helpMenu = tk.Menu(self._mainMenu, tearoff=0)
        self._mainMenu.add_cascade(
            label=_('Help'),
            menu=self._helpMenu,
        )
        self._helpMenu.add_command(
            label=_('Online help'),
            accelerator='F1',
            command=self._open_help,
        )

        #--- Event bindings.
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        if PLATFORM != 'win':
            self.bind(KEYS.QUIT_PROGRAM[0], self.on_quit)
        self.bind(KEYS.OPEN_HELP[0], self._open_help)
        self.bind('<Escape>', self._restore_status)
        self._open_last_collection()

    def on_quit(self, event=None):
        self._apply_changes()
        self.update_idletasks()
        self.prefs['window_geometry'] = self.winfo_geometry()
        try:
            if self._collection is not None and self.isModified:
                if self._ui.ask_yes_no(
                    message=_('Save changes?'),
                    detail=_('There are unsaved changes'),
                    title=FEATURE,
                    parent=self,
                ):
                    self._save_collection()
        except Exception as ex:
            self._show_cannot_save_error(str(ex))
        finally:
            self.destroy()
            self.isOpen = False

    def _apply_changes(self, event=None):
        try:
            title = self._indexCard.title.get()
            if title or self.element.title:
                if self.element.title != title:
                    self.element.title = title.strip()
                    self._collection.tree.item(
                        self.nodeId,
                        text=self.element.title,
                    )
                    self.isModified = True
            if self._indexCard.bodyBox.hasChanged:
                self.element.desc = self._indexCard.bodyBox.get_text()
                self.isModified = True
        except AttributeError:
            pass

    def _move_node(self, event):
        # Move a selected node in the collection tree.
        tv = event.widget
        node = tv.selection()[0]
        targetNode = tv.identify_row(event.y)
        if node[:2] == targetNode[:2]:
            tv.move(node, tv.parent(targetNode), tv.index(targetNode))
            self.isModified = True
        elif (node.startswith(BOOK_PREFIX)
              and targetNode.startswith(SERIES_PREFIX)
        ):
            if tv.get_children(targetNode):
                tv.move(node, tv.parent(targetNode), tv.index(targetNode))
            else:
                tv.move(node, targetNode, 0)
            self.isModified = True

    def _on_select_node(self, event=None):
        self._apply_changes()
        try:
            self.nodeId = self._collection.tree.selection()[0]
            if self.nodeId.startswith(BOOK_PREFIX):
                self.element = self._collection.books[self.nodeId]
            elif self.nodeId.startswith(SERIES_PREFIX):
                self.element = self._collection.series[self.nodeId]
        except IndexError:
            pass
        except AttributeError:
            pass
        else:
            self._set_element_view()

    def _restore_status(self, event=None):
        # Overwrite error message with the status before."""
        self._show_status(self.statusText)

    def _set_element_view(self, event=None):
        # View the selected element's title and description.
        self._indexCard.bodyBox.clear()
        if self.element.desc:
            self._indexCard.bodyBox.set_text(self.element.desc)
        if self.element.title:
            self._indexCard.title.set(self.element.title)

    def _set_status(self, statusMsg):
        # Display the status message at the status bar.
        if statusMsg.startswith('!'):
            self._statusBar.config(bg='red')
            self._statusBar.config(fg='white')
            self.infoHowText = statusMsg.split('!', maxsplit=1)[1].strip()
        else:
            self._statusBar.config(bg='green')
            self._statusBar.config(fg='white')
            self.infoHowText = statusMsg
        self._statusBar.config(text=self.infoHowText)

    def _set_title(self):
        if self._collection.title:
            collectionTitle = self._collection.title
        else:
            collectionTitle = _('Untitled collection')
        self.title(f'{collectionTitle} - {FEATURE}')

    def _show_cannot_save_error(self, errorMsg):
        self._ui.show_error(
            message=_('Cannot save the collection'),
            detail=errorMsg,
            parent=self,
        )
        self.lift()
        self.focus()

    def _show_path(self, pathStr):
        # Put text on the path bar.
        self._pathBar.config(text=pathStr)

    def _show_status(self, statusMsg):
        # Put text on the status bar.
        self.statusText = statusMsg
        self._statusBar.config(bg=self.cget('background'))
        self._statusBar.config(fg='black')
        self._statusBar.config(text=statusMsg)

