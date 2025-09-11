"""Provide a class for project collection management dialog.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from tkinter import filedialog
from tkinter import ttk

from nvcollection.collection import Collection
from nvcollection.nvcollection_globals import BOOK_PREFIX
from nvcollection.nvcollection_globals import FEATURE
from nvcollection.nvcollection_globals import SERIES_PREFIX
from nvcollection.nvcollection_help import NvcollectionHelp
from nvcollection.nvcollection_locale import _
from nvcollection.platform.platform_settings import KEYS
from nvcollection.platform.platform_settings import MOUSE
from nvcollection.platform.platform_settings import PLATFORM
from nvlib.controller.sub_controller import SubController
from nvlib.gui.widgets.index_card import IndexCard
from nvlib.novx_globals import Error
from nvlib.novx_globals import norm_path
import tkinter as tk


class CollectionView(tk.Toplevel, SubController):
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
        self.geometry(self.prefs['window_geometry'])
        self.update_idletasks()
        # this is necessary to preserve the window size

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
            fg=prefs['color_text_fg'],
            bg=prefs['color_text_bg'],
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

    def _add_current_project(self, event=None):
        self._apply_changes()
        try:
            selection = self._collection.tree.selection()[0]
        except:
            selection = ''
        book = self._mdl.prjFile
        if not self._mdl.prjFile.novel.title:
            self._set_status(f'!{_("This project has no title")}.')
            return

        parent = ''
        if selection.startswith(BOOK_PREFIX):
            parent = self._collection.tree.parent(selection)
            index = self._collection.tree.index(selection) + 1
        elif selection.startswith(SERIES_PREFIX):
            parent = selection
            index = 'end'
        else:
            parent = ''
            index = 0
        if book is not None:
            try:
                bkId = self._collection.add_book(book, parent, index)
                self.isModified = True
            except Error as ex:
                self._set_status(f'!{str(ex)}')
            else:
                if bkId is not None:
                    self._set_status(
                        (
                            f'{_("Book added to the collection")}: '
                            f'"{book.novel.title}".'
                        )
                    )
                else:
                    self._set_status(
                        f'!{_("Book already exists")}: "{book.novel.title}".'
                    )

    def _add_series(self, event=None):
        self._apply_changes()
        try:
            selection = self._collection.tree.selection()[0]
        except:
            selection = ''
        title = _('New Series')
        index = 0
        if selection.startswith(SERIES_PREFIX):
            index = self._collection.tree.index(selection) + 1
        try:
            self._collection.add_series(title, index)
            self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

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

    def _close_collection(self, event=None):
        # Close the collection without saving and reset the user interface.
        if self.isModified and self._ui.ask_yes_no(
            message=_('Save changes?'),
            detail=_('There are unsaved changes'),
            title=FEATURE,
            parent=self,
        ):
            self._save_collection()
        self._apply_changes()
        self._indexCard.title.set('')
        self._indexCard.bodyBox.clear()
        self._collection.reset_tree()
        self._collection = None
        self.title('')
        self._show_status('')
        self._show_path('')
        self._fileMenu.entryconfig(_('Save'), state='disabled')
        self._fileMenu.entryconfig(_('Close'), state='disabled')
        self.lift()
        self.focus()

    def _create_new_collection(self, event=None):
        # Create a collection.
        # Display collection title and file path.
        # Return True on success, otherwise return False.
        self._apply_changes()
        fileTypes = [
            (_('novelibre collection'), Collection.EXTENSION),
        ]
        fileName = filedialog.asksaveasfilename(
            filetypes=fileTypes,
            defaultextension=fileTypes[0][1],
        )
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self._collection is not None:
            self._close_collection()

        self._collection = Collection(fileName, self._treeView)
        self.prefs['last_open'] = fileName
        self._show_path(f'{norm_path(self._collection.filePath)}')
        self._set_title()
        self._fileMenu.entryconfig(_('Save'), state='normal')
        self._fileMenu.entryconfig(_('Close'), state='normal')
        return True

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

    def _open_book(self, event=None):
        """Make the application open the selected book's project."""
        self._apply_changes()
        try:
            nodeId = self._collection.tree.selection()[0]
            if nodeId.startswith(BOOK_PREFIX):
                self._ctrl.open_project(
                    filePath=self._collection.books[nodeId].filePath,
                )
        except IndexError:
            pass
        self.focus_set()

    def _open_collection(self, fileName='', event=None):
        """Create a Collection instance and read the file.

        Optional arguments:
            fileName: str -- collection file path.
            
        Display collection title and file path.
        Return True on success, otherwise return False.
        """
        self._apply_changes()
        self._show_status(self.statusText)
        fileName = self._select_collection(fileName)
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self._collection is not None:
            self._close_collection()

        self.isModified = False
        self.prefs['last_open'] = fileName
        self._collection = Collection(fileName, self._treeView)
        try:
            self._collection.read()
        except Error as ex:
            self._close_collection()
            self._set_status(f'!{str(ex)}')
            return False

        self._show_path(f'{norm_path(self._collection.filePath)}')
        self._set_title()
        self._fileMenu.entryconfig(_('Save'), state='normal')
        self._fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def _open_help(self, event=None):
        self._apply_changes()
        NvcollectionHelp.open_help_page()

    def _open_last_collection(self):
        if self._open_collection(fileName=self.prefs['last_open']):
            self.isOpen = True

    def _remove_book(self, event=None):
        self._apply_changes()
        try:
            nodeId = self._collection.tree.selection()[0]
        except IndexError:
            return

        try:
            if nodeId.startswith(BOOK_PREFIX):
                if self._ui.ask_yes_no(
                    message=_('Remove selected book from the collection?'),
                    detail=self._collection.books[nodeId].title,
                    title=FEATURE,
                    parent=self,
                ):
                    if self._collection.tree.prev(nodeId):
                        self._collection.tree.selection_set(
                            self._collection.tree.prev(nodeId)
                        )
                    elif self._collection.tree.parent(nodeId):
                        self._collection.tree.selection_set(
                            self._collection.tree.parent(nodeId)
                        )
                    self._set_status(self._collection.remove_book(nodeId))
                    self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def _remove_node(self, event=None):
        self._apply_changes()
        try:
            nodeId = self._collection.tree.selection()[0]
            if nodeId.startswith(SERIES_PREFIX):
                self._remove_series()
            elif nodeId.startswith(BOOK_PREFIX):
                self._remove_book()
        except IndexError:
            pass

    def _remove_series(self, event=None):
        self._apply_changes()
        try:
            nodeId = self._collection.tree.selection()[0]

        except IndexError:
            return

        try:
            if nodeId.startswith(SERIES_PREFIX):
                if self._ui.ask_yes_no(
                    message=_('Remove selected series but keep the books?'),
                    detail=self._collection.series[nodeId].title,
                    title=FEATURE,
                    parent=self,
                ):
                    if self._collection.tree.prev(nodeId):
                        self._collection.tree.selection_set(
                            self._collection.tree.prev(nodeId)
                        )
                    elif self._collection.tree.parent(nodeId):
                        self._collection.tree.selection_set(
                            self._collection.tree.parent(nodeId)
                        )
                    self._set_status(self._collection.remove_series(nodeId))
                    self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def _remove_series_with_books(self, event=None):
        self._apply_changes()
        try:
            nodeId = self._collection.tree.selection()[0]
        except IndexError:
            return

        try:
            if nodeId.startswith(SERIES_PREFIX):
                if self._ui.ask_yes_no(
                    message=_('Remove selected series and books?'),
                    detail=self._collection.series[nodeId].title,
                    title=FEATURE,
                    parent=self,
                ):
                    if self._collection.tree.prev(nodeId):
                        self._collection.tree.selection_set(
                            self._collection.tree.prev(nodeId)
                        )
                    elif self._collection.tree.parent(nodeId):
                        self._collection.tree.selection_set(
                            self._collection.tree.parent(nodeId)
                        )
                    self._set_status(
                        self._collection.remove_series_with_books(nodeId)
                    )
                    self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def _restore_status(self, event=None):
        # Overwrite error message with the status before."""
        self._show_status(self.statusText)

    def _save_collection(self, event=None):
        """Save the collection."""
        if self._collection is None:
            return

        if not self.isModified:
            self._set_status(f"{_('No changes to save')}.")
            return

        self._apply_changes()
        try:
            self._collection.write()
        except Exception as ex:
            self._show_cannot_save_error(str(ex))
        else:
            self.isModified = False
            self._set_status(f"{_('Collection saved')}.")

    def _select_collection(self, fileName):
        # Return a collection file path.
        #    fileName: str -- collection file path.
        # Priority:
        # 1. use file name argument
        # 2. open file select dialog
        # On error, return an empty string.
        initDir = os.path.dirname(self.prefs['last_open'])
        if not initDir:
            initDir = './'
        if not fileName or not os.path.isfile(fileName):
            fileTypes = [
                (_('novelibre collection'), Collection.EXTENSION),
            ]
            fileName = filedialog.askopenfilename(
                filetypes=fileTypes,
                defaultextension=fileTypes[0][1],
                initialdir=initDir,
                parent=self,
            )
        if not fileName:
            return ''

        return fileName

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

    def _update_collection(self, event=None):
        self._apply_changes()
        if self._mdl.novel is None:
            return

        if self.nodeId is None:
            return

        if (self._collection.books[self.nodeId].filePath
            != self._mdl.prjFile.filePath
        ):
            return

        self._ui.refresh()
        if self._collection.books[self.nodeId].pull_metadata(self._mdl.novel):
            self.isModified = True
            self._set_element_view()

    def _update_project(self, event=None):
        self._apply_changes()
        if self._mdl.novel is None:
            return

        if self.nodeId is None:
            return

        if (self._collection.books[self.nodeId].filePath
            != self._mdl.prjFile.filePath
        ):
            return

        self._apply_changes()
        self._collection.books[self.nodeId].push_metadata(self._mdl.novel)

