"""Provide a mixin class with nv_collection commands.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from tkinter import filedialog

from nvcollection.collection import Collection
from nvcollection.nvcollection_globals import BOOK_PREFIX
from nvcollection.nvcollection_globals import FEATURE
from nvcollection.nvcollection_globals import SERIES_PREFIX
from nvcollection.nvcollection_help import NvcollectionHelp
from nvcollection.nvcollection_locale import _
from nvlib.novx_globals import Error
from nvlib.novx_globals import norm_path


class Commands:

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

