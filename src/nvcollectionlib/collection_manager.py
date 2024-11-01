"""Provide a tkinter widget for project collection management.

Copyright (c) 2024 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

from apptk.widgets.index_card import IndexCard
from nvcollectionlib.collection import Collection
from nvcollectionlib.configuration import Configuration
from nvcollectionlib.nvcollection_globals import FEATURE
from nvcollectionlib.nvcollection_globals import BOOK_PREFIX
from nvcollectionlib.nvcollection_globals import Error
from nvcollectionlib.nvcollection_globals import SERIES_PREFIX
from nvcollectionlib.nvcollection_globals import _
from nvcollectionlib.nvcollection_globals import norm_path
from nvcollectionlib.nvcollection_globals import open_help
from nvcollectionlib.platform.platform_settings import KEYS
from nvcollectionlib.platform.platform_settings import MOUSE
from nvcollectionlib.platform.platform_settings import PLATFORM
import tkinter as tk


class CollectionManager(tk.Toplevel):

    INI_FILENAME = 'collection.ini'
    SETTINGS = dict(
        last_open='',
        tree_width='300',
    )
    OPTIONS = {}

    def __init__(self, model, view, controller, position, configDir):
        self._mdl = model
        self._ui = view
        self._ctrl = controller
        super().__init__()

        #--- Load configuration.
        self.iniFile = f'{configDir}/{self.INI_FILENAME}'
        self.configuration = Configuration(self.SETTINGS, self.OPTIONS)
        self.configuration.read(self.iniFile)
        self.kwargs = {}
        self.kwargs.update(self.configuration.settings)
        # Read the file path from the configuration file.

        self.title(FEATURE)
        self._statusText = ''

        self.geometry(position)
        self.lift()
        self.focus()

        #--- Event bindings.
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        if PLATFORM != 'win':
            self.bind(KEYS.QUIT_PROGRAM[0], self.on_quit)

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
        self._fileTypes = [(_('novelibre collection'), Collection.EXTENSION)]

        #--- Tree for book selection.
        self.treeView = ttk.Treeview(self.treeWindow, selectmode='browse')
        scrollY = ttk.Scrollbar(self.treeView, orient='vertical', command=self.treeView.yview)
        self.treeView.configure(yscrollcommand=scrollY.set)
        scrollY.pack(side='right', fill='y')
        self.treeView.pack(side='left')
        self.treeWindow.add(self.treeView)
        self.treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self.treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self.treeView.bind('<Double-1>', self._open_book)
        self.treeView.bind('<Return>', self._open_book)
        self.treeView.bind('<Delete>', self._remove_node)
        self.treeView.bind('<Shift-Delete>', self._remove_series_with_books)
        self.treeView.bind(MOUSE.MOVE_NODE, self._move_node)

        #--- "Index card" in the right frame.
        self.indexCard = IndexCard(self.treeWindow, bd=2, relief='ridge')
        self.indexCard.pack(side='right')
        self.treeWindow.add(self.indexCard)

        # Adjust the tree width.
        self.treeWindow.update()
        self.treeWindow.sashpos(0, self.kwargs['tree_width'])

        # Status bar.
        self.statusBar = tk.Label(self, text='', anchor='w', padx=5, pady=2)
        self.statusBar.pack(expand=False, fill='both')
        self.statusBar.bind(MOUSE.LEFT_CLICK, self._restore_status)

        # Path bar.
        self.pathBar = tk.Label(self, text='', anchor='w', padx=5, pady=3)
        self.pathBar.pack(expand=False, fill='both')

        #--- Add menu entries.
        # File menu.
        self.fileMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('File'), menu=self.fileMenu)
        self.fileMenu.add_command(label=_('New'), command=self._new_collection)
        self.fileMenu.add_command(label=_('Open...'), command=lambda: self._open_collection(''))
        self.fileMenu.add_command(label=_('Save'), state='disabled', command=self._save_collection)
        self.fileMenu.add_command(label=_('Close'), state='disabled', command=self._close_collection)
        if PLATFORM == 'win':
            self.fileMenu.add_command(label=_('Exit'), accelerator=KEYS.QUIT_PROGRAM[1], command=self.on_quit)
        else:
            self.fileMenu.add_command(label=_('Quit'), accelerator=KEYS.QUIT_PROGRAM[1], command=self.on_quit)

        # Series menu.
        self.seriesMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Series'), menu=self.seriesMenu)
        self.seriesMenu.add_command(label=_('Add'), command=self._add_series)
        self.seriesMenu.add_command(label=_('Remove selected series but keep the books'), command=self._remove_series)
        self.seriesMenu.add_command(label=_('Remove selected series and books'), command=self._remove_series_with_books)

        # Book menu.
        self.bookMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Book'), menu=self.bookMenu)
        self.bookMenu.add_command(label=_('Add current project to the collection'), command=self._add_current_project)
        self.bookMenu.add_command(label=_('Remove selected book from the collection'), command=self._remove_book)
        self.bookMenu.add_command(label=_('Update book data from the current project'), command=self._update_collection)
        self.bookMenu.add_command(label=_('Update project data from the selected book'), command=self._update_project)

        # Help
        self.helpMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Help'), menu=self.helpMenu)
        self.helpMenu.add_command(label=_('Online help'), accelerator='F1', command=open_help)

        #--- Event bindings.
        self.bind(KEYS.OPEN_HELP[0], open_help)
        self.bind('<Escape>', self._restore_status)

        self.isModified = False
        self._element = None
        self._nodeId = None
        if self._open_collection(self.kwargs['last_open']):
            self.isOpen = True

    #--- Application related methods.

    def on_quit(self, event=None):
        self._get_element_view()
        self.kwargs['tree_width'] = self.treeWindow.sashpos(0)

        #--- Save project specific configuration
        for keyword in self.kwargs:
            if keyword in self.configuration.options:
                self.configuration.options[keyword] = self.kwargs[keyword]
            elif keyword in self.configuration.settings:
                self.configuration.settings[keyword] = self.kwargs[keyword]
        self.configuration.write(self.iniFile)
        try:
            if self.collection is not None:
                if self.isModified:
                    self.collection.write()
        except Exception as ex:
            self._show_info(str(ex))
        finally:
            self.destroy()
            self.isOpen = False

    def _on_select_node(self, event=None):
        self._get_element_view()
        try:
            self._nodeId = self.collection.tree.selection()[0]
            if self._nodeId.startswith(BOOK_PREFIX):
                self._element = self.collection.books[self._nodeId]
            elif self._nodeId.startswith(SERIES_PREFIX):
                self._element = self.collection.series[self._nodeId]
        except IndexError:
            pass
        except AttributeError:
            pass
        else:
            self._set_element_view()

    def _set_element_view(self, event=None):
        """View the selected element's title and description."""
        self.indexCard.bodyBox.clear()
        if self._element.desc:
            self.indexCard.bodyBox.set_text(self._element.desc)
        if self._element.title:
            self.indexCard.title.set(self._element.title)

    def _get_element_view(self, event=None):
        """Apply changes."""
        try:
            title = self.indexCard.title.get()
            if title or self._element.title:
                if self._element.title != title:
                    self._element.title = title.strip()
                    self.collection.tree.item(self._nodeId, text=self._element.title)
                    self.isModified = True
            if self.indexCard.bodyBox.hasChanged:
                self._element.desc = self.indexCard.bodyBox.get_text()
                self.isModified = True
        except AttributeError:
            pass

    def _show_info(self, message):
        if message.startswith('!'):
            message = message.split('!', maxsplit=1)[1].strip()
            messagebox.showerror(FEATURE, message=message, parent=self)
        else:
            messagebox.showinfo(FEATURE, message=message, parent=self)
        self.lift()
        self.focus()

    def _set_status(self, message):
        """Show how the converter is doing.
        
        Positional arguments:
            message -- message to be displayed. 
            
        Display the message at the status bar.
        Overrides the superclass method.
        """
        if message.startswith('!'):
            self.statusBar.config(bg='red')
            self.statusBar.config(fg='white')
            self.infoHowText = message.split('!', maxsplit=1)[1].strip()
        else:
            self.statusBar.config(bg='green')
            self.statusBar.config(fg='white')
            self.infoHowText = message
        self.statusBar.config(text=self.infoHowText)

    def _show_path(self, message):
        """Put text on the path bar."""
        self.pathBar.config(text=message)

    def _show_status(self, message):
        """Put text on the status bar."""
        self._statusText = message
        self.statusBar.config(bg=self.cget('background'))
        self.statusBar.config(fg='black')
        self.statusBar.config(text=message)

    def _restore_status(self, event=None):
        """Overwrite error message with the status before."""
        self._show_status(self._statusText)

    def _move_node(self, event):
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

    #--- Project related methods.

    def _open_book(self, event=None):
        """Make the application open the selected book's project."""
        try:
            nodeId = self.collection.tree.selection()[0]
            if nodeId.startswith(BOOK_PREFIX):
                self._ctrl.open_project(filePath=self.collection.books[nodeId].filePath)
        except IndexError:
            pass
        self.focus_set()

    def _add_current_project(self, event=None):
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

    def _update_collection(self, event=None):
        if self._mdl.novel is None:
            return

        if self._nodeId is None:
            return

        if self.collection.books[self._nodeId].filePath != self._mdl.prjFile.filePath:
            return

        self._ui.refresh()
        if self.collection.books[self._nodeId].pull_metadata(self._mdl.novel):
            self.isModified = True
            self._set_element_view()

    def _update_project(self, event=None):
        if self._mdl.novel is None:
            return

        if self._nodeId is None:
            return

        if self.collection.books[self._nodeId].filePath != self._mdl.prjFile.filePath:
            return

        self._get_element_view()
        self.collection.books[self._nodeId].push_metadata(self._mdl.novel)

    def _remove_book(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(BOOK_PREFIX):
                    if messagebox.askyesno(FEATURE, message=f'{_("Remove selected book from the collection")}?', parent=self):
                        if self.collection.tree.prev(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                        elif self.collection.tree.parent(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                        message = self.collection.remove_book(nodeId)
                        self.isModified = True
                        self.lift()
                        self.focus()
            except Error as ex:
                self._set_status(str(ex))
            else:
                if message:
                    self._set_status(message)
        except IndexError:
            pass

    def _add_series(self, event=None):
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

    def _remove_series(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(SERIES_PREFIX):
                    if messagebox.askyesno(FEATURE, message=f'{_("Remove selected series but keep the books")}?', parent=self):
                        if self.collection.tree.prev(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                        elif self.collection.tree.parent(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                        message = self.collection.remove_series(nodeId)
                        self.isModified = True
                        self.lift()
                        self.focus()
            except Error as ex:
                self._set_status(str(ex))
            else:
                if message:
                    self._set_status(message)
        except IndexError:
            pass

    def _remove_series_with_books(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(SERIES_PREFIX):
                    if messagebox.askyesno(FEATURE, message=f'{_("Remove selected series and books")}?', parent=self):
                        if self.collection.tree.prev(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                        elif self.collection.tree.parent(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                        message = self.collection.remove_series_with_books(nodeId)
                        self.isModified = True
                        self.lift()
                        self.focus()
            except Error as ex:
                self._set_status(str(ex))
            else:
                if message:
                    self._set_status(message)
        except IndexError:
            pass

    def _remove_node(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            if nodeId.startswith(SERIES_PREFIX):
                self._remove_series()
            elif nodeId.startswith(BOOK_PREFIX):
                self._remove_book()
            self.isModified = True
        except IndexError:
            pass

    #--- Collection related methods.

    def _select_collection(self, fileName):
        """Return a collection file path.

        Positional arguments:
            fileName: str -- collection file path.
            
        Optional arguments:
            fileTypes -- list of tuples for file selection (display text, extension).

        Priority:
        1. use file name argument
        2. open file select dialog

        On error, return an empty string.
        """
        initDir = os.path.dirname(self.kwargs['last_open'])
        if not initDir:
            initDir = './'
        if not fileName or not os.path.isfile(fileName):
            fileName = filedialog.askopenfilename(filetypes=self._fileTypes, defaultextension=self._fileTypes[0][1], initialdir=initDir, parent=self)
        if not fileName:
            return ''

        return fileName

    def _open_collection(self, fileName):
        """Create a Collection instance and read the file.

        Positional arguments:
            fileName: str -- collection file path.
            
        Display collection title and file path.
        Return True on success, otherwise return False.
        """
        self._show_status(self._statusText)
        fileName = self._select_collection(fileName)
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self.collection is not None:
            self._close_collection()

        self.kwargs['last_open'] = fileName
        self.collection = Collection(fileName, self.treeView)
        try:
            self.collection.read()
        except Error as ex:
            self._close_collection()
            self._set_status(f'!{str(ex)}')
            return False

        self._show_path(f'{norm_path(self.collection.filePath)}')
        self._set_title()
        self.fileMenu.entryconfig(_('Save'), state='normal')
        self.fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def _new_collection(self, event=None):
        """Create a collection.

        Display collection title and file path.
        Return True on success, otherwise return False.
        """
        fileName = filedialog.asksaveasfilename(filetypes=self._fileTypes, defaultextension=self._fileTypes[0][1])
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self.collection is not None:
            self._close_collection()

        self.collection = Collection(fileName, self.treeView)
        self.kwargs['last_open'] = fileName
        self._show_path(f'{norm_path(self.collection.filePath)}')
        self._set_title()
        self.fileMenu.entryconfig(_('Save'), state='normal')
        self.fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def _save_collection(self, event=None):
        """Save the collection."""
        try:
            if self.collection is not None:
                if self.isModified:
                    self.collection.write()
        except Exception as ex:
            self._show_info(str(ex))
            return

        self.isModified = False
        self._set_status(_('Collection saved.'))

    def _close_collection(self, event=None):
        """Close the collection without saving and reset the user interface.
        
        To be extended by subclasses.
        """
        if self.isModified and self._ui.ask_yes_no(_('Save changes?')):
            self._save_collection()
        self._get_element_view()
        self.indexCard.title.set('')
        self.indexCard.bodyBox.clear()
        self.collection.reset_tree()
        self.collection = None
        self.title('')
        self._show_status('')
        self._show_path('')
        self.fileMenu.entryconfig(_('Save'), state='disabled')
        self.fileMenu.entryconfig(_('Close'), state='disabled')
        self.lift()
        self.focus()

    def _set_title(self):
        """Set the main window title. 
        
        'Collection title - application'
        """
        if self.collection.title:
            collectionTitle = self.collection.title
        else:
            collectionTitle = _('Untitled collection')
        self.title(f'{collectionTitle} - {FEATURE}')

