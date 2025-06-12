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

    def __init__(self, model, view, controller, windowPosition, prefs):
        super().__init__()
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        self.prefs = prefs
        self.isModified = False
        self.element = None
        self.nodeId = None
        windowSize = self.prefs['window_size'].split('+')[0]
        self.geometry(f"{windowSize}{windowPosition}")

        self.title(FEATURE)
        self.statusText = ''

        self.lift()
        self.focus()

        #--- Main menu.
        self.mainMenu = tk.Menu(self)
        self.config(menu=self.mainMenu)

        #--- Path bar.
        self.pathBar = tk.Label(self, text='', anchor='w', padx=5, pady=3)
        self.pathBar.pack(expand=False, fill='both', side='bottom')

        #--- Status bar.
        self.statusBar = tk.Label(self, text='', anchor='w', padx=5, pady=2)
        self.statusBar.pack(expand=False, fill='both', side='bottom')
        self.statusBar.bind(MOUSE.LEFT_CLICK, self.restore_status)

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
        self._indexCard = IndexCard(self.treeWindow, bd=2, relief='ridge')
        self._indexCard.pack(side='right')
        self.treeWindow.add(self._indexCard)
        self._indexCard.titleEntry.bind('<Return>', self.apply_changes)
        self._indexCard.titleEntry.bind('<FocusOut>', self.apply_changes)

        # Adjust the tree width.
        self.treeWindow.update()
        self.treeWindow.sashpos(0, self.prefs['tree_width'])

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

        # Restore last window size.
        self.update_idletasks()
        self.geometry(f"{windowSize}{windowPosition}")

        self.open_last_collection()

    def add_current_project(self, event=None):
        self.apply_changes()
        try:
            selection = self.collection.tree.selection()[0]
        except:
            selection = ''
        book = self._mdl.prjFile
        if not self._mdl.prjFile.novel.title:
            self._set_status(f'!{_("This project has no title")}.')
            return

        parent = ''
        if selection.startswith(BOOK_PREFIX):
            parent = self.collection.tree.parent(selection)
            index = self.collection.tree.index(selection) + 1
        elif selection.startswith(SERIES_PREFIX):
            parent = selection
            index = 'end'
        else:
            parent = ''
            index = 0
        if book is not None:
            try:
                bkId = self.collection.add_book(book, parent, index)
                self.isModified = True
            except Error as ex:
                self._set_status(f'!{str(ex)}')
            else:
                if bkId is not None:
                    self._set_status(f'{_("Book added to the collection")}: "{book.novel.title}".')
                else:
                    self._set_status(f'!{_("Book already exists")}: "{book.novel.title}".')

    def add_series(self, event=None):
        self.apply_changes()
        try:
            selection = self.collection.tree.selection()[0]
        except:
            selection = ''
        title = _('New Series')
        index = 0
        if selection.startswith(SERIES_PREFIX):
            index = self.collection.tree.index(selection) + 1
        try:
            self.collection.add_series(title, index)
            self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def apply_changes(self, event=None):
        """Apply changes."""
        try:
            title = self._indexCard.title.get()
            if title or self.element.title:
                if self.element.title != title:
                    self.element.title = title.strip()
                    self.collection.tree.item(self.nodeId, text=self.element.title)
                    self.isModified = True
            if self._indexCard.bodyBox.hasChanged:
                self.element.desc = self._indexCard.bodyBox.get_text()
                self.isModified = True
        except AttributeError:
            pass

    def close_collection(self, event=None):
        """Close the collection without saving and reset the user interface.
        
        To be extended by subclasses.
        """
        if self.isModified and self._ui.ask_yes_no(
            message=_('Save changes?'),
            detail=_('There are unsaved changes'),
            title=FEATURE,
            parent=self
            ):
            self.save_collection()
        self.apply_changes()
        self._indexCard.title.set('')
        self._indexCard.bodyBox.clear()
        self.collection.reset_tree()
        self.collection = None
        self.title('')
        self._show_status('')
        self._show_path('')
        self.fileMenu.entryconfig(_('Save'), state='disabled')
        self.fileMenu.entryconfig(_('Close'), state='disabled')
        self.lift()
        self.focus()

    def move_node(self, event):
        """Move a selected node in the collection tree."""
        tv = event.widget
        node = tv.selection()[0]
        targetNode = tv.identify_row(event.y)
        if node[:2] == targetNode[:2]:
            tv.move(node, tv.parent(targetNode), tv.index(targetNode))
            self.isModified = True
        elif node.startswith(BOOK_PREFIX) and targetNode.startswith(SERIES_PREFIX):
            if tv.get_children(targetNode):
                tv.move(node, tv.parent(targetNode), tv.index(targetNode))
            else:
                tv.move(node, targetNode, 0)
            self.isModified = True

    def new_collection(self, event=None):
        """Create a collection.

        Display collection title and file path.
        Return True on success, otherwise return False.
        """
        self.apply_changes()
        fileTypes = [(_('novelibre collection'), Collection.EXTENSION)]
        fileName = filedialog.asksaveasfilename(
            filetypes=fileTypes,
            defaultextension=fileTypes[0][1]
            )
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self.collection is not None:
            self.close_collection()

        self.collection = Collection(fileName, self.treeView)
        self.prefs['last_open'] = fileName
        self._show_path(f'{norm_path(self.collection.filePath)}')
        self._set_title()
        self.fileMenu.entryconfig(_('Save'), state='normal')
        self.fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def on_quit(self, event=None):
        self.apply_changes()
        self.prefs['tree_width'] = self.treeWindow.sashpos(0)
        self.prefs['window_size'] = self.winfo_geometry().split('+')[0]
        try:
            if self.collection is not None and self.isModified:
                if self._ui.ask_yes_no(
                    message=_('Save changes?'),
                    detail=_('There are unsaved changes'),
                    title=FEATURE,
                    parent=self
                    ):
                    self.save_collection()
        except Exception as ex:
            self._show_cannot_save_error(str(ex))
        finally:
            self.destroy()
            self.isOpen = False

    def on_select_node(self, event=None):
        self.apply_changes()
        try:
            self.nodeId = self.collection.tree.selection()[0]
            if self.nodeId.startswith(BOOK_PREFIX):
                self.element = self.collection.books[self.nodeId]
            elif self.nodeId.startswith(SERIES_PREFIX):
                self.element = self.collection.series[self.nodeId]
        except IndexError:
            pass
        except AttributeError:
            pass
        else:
            self._set_element_view()

    def open_book(self, event=None):
        """Make the application open the selected book's project."""
        self.apply_changes()
        try:
            nodeId = self.collection.tree.selection()[0]
            if nodeId.startswith(BOOK_PREFIX):
                self._ctrl.open_project(filePath=self.collection.books[nodeId].filePath)
        except IndexError:
            pass
        self.focus_set()

    def open_collection(self, fileName='', event=None):
        """Create a Collection instance and read the file.

        Optional arguments:
            fileName: str -- collection file path.
            
        Display collection title and file path.
        Return True on success, otherwise return False.
        """
        self.apply_changes()
        self._show_status(self.statusText)
        fileName = self._select_collection(fileName)
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self.collection is not None:
            self.close_collection()

        self.isModified = False
        self.prefs['last_open'] = fileName
        self.collection = Collection(fileName, self.treeView)
        try:
            self.collection.read()
        except Error as ex:
            self.close_collection()
            self._set_status(f'!{str(ex)}')
            return False

        self._show_path(f'{norm_path(self.collection.filePath)}')
        self._set_title()
        self.fileMenu.entryconfig(_('Save'), state='normal')
        self.fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def open_help(self, event=None):
        self.apply_changes()
        NvcollectionHelp.open_help_page()

    def open_last_collection(self):
        if self.open_collection(fileName=self.prefs['last_open']):
            self.isOpen = True

    def remove_book(self, event=None):
        self.apply_changes()
        try:
            nodeId = self.collection.tree.selection()[0]
        except IndexError:
            return

        try:
            if nodeId.startswith(BOOK_PREFIX):
                if self._ui.ask_yes_no(
                    message=_('Remove selected book from the collection?'),
                    detail=self.collection.books[nodeId].title,
                    title=FEATURE,
                    parent=self
                    ):
                    if self.collection.tree.prev(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                    elif self.collection.tree.parent(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                    self._set_status(self.collection.remove_book(nodeId))
                    self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def remove_node(self, event=None):
        self.apply_changes()
        try:
            nodeId = self.collection.tree.selection()[0]
            if nodeId.startswith(SERIES_PREFIX):
                self.remove_series()
            elif nodeId.startswith(BOOK_PREFIX):
                self.remove_book()
        except IndexError:
            pass

    def remove_series(self, event=None):
        self.apply_changes()
        try:
            nodeId = self.collection.tree.selection()[0]

        except IndexError:
            return

        try:
            if nodeId.startswith(SERIES_PREFIX):
                if self._ui.ask_yes_no(
                    message=_('Remove selected series but keep the books?'),
                    detail=self.collection.series[nodeId].title,
                    title=FEATURE,
                    parent=self
                    ):
                    if self.collection.tree.prev(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                    elif self.collection.tree.parent(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                    self._set_status(self.collection.remove_series(nodeId))
                    self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def remove_series_with_books(self, event=None):
        self.apply_changes()
        try:
            nodeId = self.collection.tree.selection()[0]
        except IndexError:
            return

        try:
            if nodeId.startswith(SERIES_PREFIX):
                if self._ui.ask_yes_no(
                    message=_('Remove selected series and books?'),
                    detail=self.collection.series[nodeId].title,
                    title=FEATURE,
                    parent=self
                    ):
                    if self.collection.tree.prev(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                    elif self.collection.tree.parent(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                    self._set_status(self.collection.remove_series_with_books(nodeId))
                    self.isModified = True
        except Error as ex:
            self._set_status(str(ex))

    def restore_status(self, event=None):
        """Overwrite error message with the status before."""
        self._show_status(self.statusText)

    def save_collection(self, event=None):
        """Save the collection."""
        self.apply_changes()
        try:
            if self.collection is not None:
                if self.isModified:
                    self.collection.write()
        except Exception as ex:
            self._show_cannot_save_error(str(ex))
            return

        self.isModified = False
        self._set_status(_('Collection saved.'))

    def update_collection(self, event=None):
        self.apply_changes()
        if self._mdl.novel is None:
            return

        if self.nodeId is None:
            return

        if self.collection.books[self.nodeId].filePath != self._mdl.prjFile.filePath:
            return

        self._ui.refresh()
        if self.collection.books[self.nodeId].pull_metadata(self._mdl.novel):
            self.isModified = True
            self._set_element_view()

    def update_project(self, event=None):
        self.apply_changes()
        if self._mdl.novel is None:
            return

        if self.nodeId is None:
            return

        if self.collection.books[self.nodeId].filePath != self._mdl.prjFile.filePath:
            return

        self.apply_changes()
        self.collection.books[self.nodeId].push_metadata(self._mdl.novel)

    def _select_collection(self, fileName):
        """Return a collection file path.

        Positional arguments:
            fileName: str -- collection file path.
            
        Priority:
        1. use file name argument
        2. open file select dialog

        On error, return an empty string.
        """
        initDir = os.path.dirname(self.prefs['last_open'])
        if not initDir:
            initDir = './'
        if not fileName or not os.path.isfile(fileName):
            fileTypes = [(_('novelibre collection'), Collection.EXTENSION)]
            fileName = filedialog.askopenfilename(
                filetypes=fileTypes,
                defaultextension=fileTypes[0][1],
                initialdir=initDir, parent=self
                )
        if not fileName:
            return ''

        return fileName

    def _set_element_view(self, event=None):
        """View the selected element's title and description."""
        self._indexCard.bodyBox.clear()
        if self.element.desc:
            self._indexCard.bodyBox.set_text(self.element.desc)
        if self.element.title:
            self._indexCard.title.set(self.element.title)

    def _set_status(self, statusMsg):
        """Show how the converter is doing.
        
        Positional arguments:
            statusMsg -- Status message to be displayed. 
            
        Display the status message at the status bar.
        Overrides the superclass method.
        """
        if statusMsg.startswith('!'):
            self.statusBar.config(bg='red')
            self.statusBar.config(fg='white')
            self.infoHowText = statusMsg.split('!', maxsplit=1)[1].strip()
        else:
            self.statusBar.config(bg='green')
            self.statusBar.config(fg='white')
            self.infoHowText = statusMsg
        self.statusBar.config(text=self.infoHowText)

    def _set_title(self):
        """Set the main window title. 
        
        'Collection title - application'
        """
        if self.collection.title:
            collectionTitle = self.collection.title
        else:
            collectionTitle = _('Untitled collection')
        self.title(f'{collectionTitle} - {FEATURE}')

    def _show_cannot_save_error(self, errorMsg):
        self._ui.show_error(
            message=_('Cannot save the collection'),
            detail=errorMsg,
            parent=self
            )
        self.lift()
        self.focus()

    def _show_path(self, pathStr):
        """Put text on the path bar."""
        self.pathBar.config(text=pathStr)

    def _show_status(self, statusMsg):
        """Put text on the status bar."""
        self.statusText = statusMsg
        self.statusBar.config(bg=self.cget('background'))
        self.statusBar.config(fg='black')
        self.statusBar.config(text=statusMsg)

