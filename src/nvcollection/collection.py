"""Provide a class representing a collection of novelibre projects.

Copyright (c) 2024 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os

from nvcollection.book import Book
from nvcollection.nvcollection_globals import BOOK_PREFIX
from nvcollection.nvcollection_globals import SERIES_PREFIX
from nvcollection.nvcollection_locale import _
from nvcollection.series import Series
from nvlib.model.data.id_generator import new_id
from nvlib.model.xml.xml_filter import strip_illegal_characters
from nvlib.model.xml.xml_indent import indent
from nvlib.model.xml.xml_open import get_xml_root
from nvlib.novx_globals import Error
from nvlib.novx_globals import norm_path
import tkinter.font as tkFont
import xml.etree.ElementTree as ET


class Collection:
    """Represent a collection of novelibre projects. 
    
    - A collection has books and series.
    - Books can be members of a series.
    
    The collection data is saved in an XML file.
    """
    MAJOR_VERSION = 1
    MINOR_VERSION = 0
    # DTD version.

    XML_HEADER = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE COLLECTION SYSTEM "nvcx_1_0.dtd">
<?xml-stylesheet href="collection.css" type="text/css"?>
'''

    EXTENSION = 'nvcx'

    def __init__(self, filePath, tree):
        """Initialize the instance variables.
        
        Positional arguments:
            filePath -- str: path to xml file.
            tree -- tree structure of series and book IDs.
        """
        self.title = None
        self.tree = tree
        fontSize = tkFont.nametofont('TkDefaultFont').actual()['size']
        self.tree.tag_configure('SERIES', font=('', fontSize, 'bold'))

        self.books = {}
        # Dictionary:
        #   keyword -- book ID
        #   value -- Book instance

        self.series = {}
        # Dictionary:
        #   keyword -- series ID
        #   value -- Series instance

        self._filePath = None
        # Location of the collection XML file.

        self.filePath = filePath

    @property
    def filePath(self):
        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """Accept only filenames with the right extension. """
        if filePath.lower().endswith(self.EXTENSION):
            self._filePath = filePath
            self.title, __ = os.path.splitext(os.path.basename(self.filePath))

    def add_book(self, book, parent='', index='end'):
        """Add an existing project file as book to the collection. 
        
        Return the book ID, if book is added to the collection.
        Return None, if novel is already a member.
        Raise the "Error" exception in case of error.
        """
        if book.filePath is None:
            raise Error(_('There is no file for the current project. Please save first.'))

        if not os.path.isfile(book.filePath):
            raise Error(f'"{norm_path(book.filePath)}" not found.')

        for bkId in self.books:
            if book.filePath == self.books[bkId].filePath:
                return None

        bkId = new_id(self.books, prefix=BOOK_PREFIX)
        self.books[bkId] = Book(book.filePath)
        self.books[bkId].pull_metadata(book.novel)
        self.tree.insert(parent, index, bkId, text=self.books[bkId].title, open=True)
        return bkId

    def add_series(self, seriesTitle, index='end'):
        """Instantiate a Series object.
        
        Return the series ID.
        """
        srId = new_id(self.series, prefix=SERIES_PREFIX)
        self.series[srId] = Series()
        self.series[srId].title = seriesTitle
        self.tree.insert('', index, srId, text=self.series[srId].title, tags='SERIES', open=True)
        return srId

    def read(self):
        """Parse the pwc XML file located at filePath, fetching the Collection attributes.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """

        def get_book(parent, xmlBook):
            bkId = xmlBook.attrib[('id')]
            xmlPath = xmlBook.find('Path')
            if xmlPath is not None:
                bookPath = xmlPath.text
                if bookPath and os.path.isfile(bookPath):
                    self.books[bkId] = Book(bookPath)
                    xmlTitle = xmlBook.find('Title')
                    if xmlTitle is not None and xmlTitle.text:
                        self.books[bkId].title = xmlTitle.text
                    else:
                        self.books[bkId].title = f"{_('Untitled')} ({bkId})"
                    xmlDesc = xmlBook.find('Desc')
                    if xmlDesc is not None:
                        paragraphs = []
                        for xmlParagraph in xmlDesc.iterfind('p'):
                            if xmlParagraph.text:
                                paragraphs.append(xmlParagraph.text)
                        self.books[bkId].desc = '\n'.join(paragraphs)
                    self.tree.insert(parent, 'end', bkId, text=self.books[bkId].title, open=True)

        xmlRoot = get_xml_root(self.filePath)
        if not xmlRoot.tag == 'COLLECTION':
            raise Error(f'{_("No collection found in file")}: "{norm_path(self.filePath)}".')

        try:
            majorVersionStr, minorVersionStr = xmlRoot.attrib['version'].split('.')
            majorVersion = int(majorVersionStr)
            minorVersion = int(minorVersionStr)
        except:
            raise Error(f'{_("No valid version found in file")}: "{norm_path(self.filePath)}".')

        if majorVersion > self.MAJOR_VERSION:
            raise Error(_('The collection was created with a newer plugin version.'))

        elif majorVersion < self.MAJOR_VERSION:
            raise Error(_('The collection was created with an outdated plugin version.'))

        elif minorVersion > self.MINOR_VERSION:
            raise Error(_('The collection was created with a newer plugin version.'))

        self.reset_tree()
        self.books = {}
        self.series = {}
        for xmlElement in xmlRoot:
            if xmlElement.tag == 'BOOK':
                get_book('', xmlElement)
            elif xmlElement.tag == 'SERIES':
                srId = xmlElement.attrib['id']
                self.series[srId] = Series()
                xmlTitle = xmlElement.find('Title')
                if xmlTitle is not None and xmlTitle.text:
                    self.series[srId].title = xmlTitle.text
                else:
                    self.series[srId].title = f"{_('Untitled')} ({srId})"
                xmlDesc = xmlElement.find('Desc')
                if xmlDesc is not None:
                    paragraphs = []
                    for xmlParagraph in xmlDesc.iterfind('p'):
                        if xmlParagraph.text:
                            paragraphs.append(xmlParagraph.text)
                    self.series[srId].desc = '\n'.join(paragraphs)
                self.tree.insert('', 'end', srId, text=self.series[srId].title, tags='SERIES', open=True)
                for xmlBook in xmlElement.iter('BOOK'):
                    get_book(srId, xmlBook)
        if not xmlRoot.attrib.get('version', None):
            self.write()
        return f'{len(self.books)} Books found in "{norm_path(self.filePath)}".'

    def remove_book(self, bkId):
        """Remove a book from the collection.

        Return a message.
        Raise the "Error" exception in case of error.
        """
        bookTitle = bkId
        try:
            bookTitle = self.books[bkId].title
            del self.books[bkId]
            self.tree.delete(bkId)
            message = f'{_("Book removed from the collection")}: "{bookTitle}".'
            return message
        except:
            raise Error(f'{_("Cannot remove book")}: "{bookTitle}".')

    def remove_series(self, srId):
        """Delete a Series object but keep the books.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        seriesTitle = self.series[srId].title
        for bookNode in self.tree.get_children(srId):
            self.tree.move(bookNode, '', 'end')
        del(self.series[srId])
        self.tree.delete(srId)
        return f'{_("Series removed from the collection")}: "{seriesTitle}".'

        raise Error(f'{_("Cannot remove series")}: "{seriesTitle}".')

    def remove_series_with_books(self, srId):
        """Delete a Series object with all its members.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        seriesTitle = self.series[srId].title
        for bkId in self.tree.get_children(srId):
            del self.books[bkId]
        del(self.series[srId])
        self.tree.delete(srId)
        return f'{_("Series removed from the collection")}: "{seriesTitle}".'

        raise Error(f'{_("Cannot remove series")}: "{seriesTitle}".')

    def reset_tree(self):
        """Clear the displayed tree."""
        for child in self.tree.get_children(''):
            self.tree.delete(child)

    def write(self):
        """Write the collection's attributes to a pwc XML file located at filePath. 
        
        Overwrite existing file without confirmation.
        Return a message.
        Raise the "Error" exception in case of error.
        """

        def walk_tree(node, xmlNode):
            """Transform the Treeview nodes to XML Elementtree nodes."""
            for elementId in self.tree.get_children(node):
                if elementId.startswith(BOOK_PREFIX):
                    xmlBook = ET.SubElement(xmlNode, 'BOOK')
                    xmlBook.set('id', elementId)
                    xmlBookTitle = ET.SubElement(xmlBook, 'Title')
                    if self.books[elementId].title:
                        xmlBookTitle.text = self.books[elementId].title
                    if self.books[elementId].desc:
                        xmlBookDesc = ET.SubElement(xmlBook, 'Desc')
                        for paragraph in self.books[elementId].desc.split('\n'):
                            ET.SubElement(xmlBookDesc, 'p').text = paragraph.strip()
                    xmlBookPath = ET.SubElement(xmlBook, 'Path')
                    xmlBookPath.text = self.books[elementId].filePath
                elif elementId.startswith(SERIES_PREFIX):
                    xmlSeries = ET.SubElement(xmlNode, 'SERIES')
                    xmlSeries.set('id', elementId)
                    xmlSeriesTitle = ET.SubElement(xmlSeries, 'Title')
                    if self.series[elementId].title:
                        xmlSeriesTitle.text = self.series[elementId].title
                    if self.series[elementId].desc:
                        xmlSeriesDesc = ET.SubElement(xmlSeries, 'Desc')
                        for paragraph in self.series[elementId].desc.split('\n'):
                            ET.SubElement(xmlSeriesDesc, 'p').text = paragraph.strip()
                    walk_tree(elementId, xmlSeries)

        xmlRoot = ET.Element('COLLECTION')
        xmlRoot.set('version', f'{self.MAJOR_VERSION}.{self.MINOR_VERSION}')
        walk_tree('', xmlRoot)

        indent(xmlRoot)
        xmlTree = ET.ElementTree(xmlRoot)
        backedUp = False
        if os.path.isfile(self.filePath):
            try:
                os.replace(self.filePath, f'{self.filePath}.bak')
            except:
                raise Error(f'{_("Cannot overwrite file")}: "{norm_path(self.filePath)}".')
            else:
                backedUp = True
        try:
            xmlTree.write(self.filePath, encoding='utf-8')

            # Postprocess the xml file created by ElementTree
            self._postprocess_xml_file(self.filePath)
        except:
            if backedUp:
                os.replace(f'{self.filePath}.bak', self.filePath)
            raise Error(f'{_("Cannot write file")}: "{norm_path(self.filePath)}".')

        return f'"{norm_path(self.filePath)}" written.'

    def _postprocess_xml_file(self, filePath):
        """Postprocess an xml file created by ElementTree.
        
        Positional argument:
            filePath -- str: path to xml file.
        
        Read the xml file, put a header on top. Overwrite the .nvcx xml file.
        Raise the "Error" exception in case of error. 
        
        Note: The path is given as an argument rather than using self.filePath. 
        So this routine can be used for novelibre-generated xml files other than .nvcx as well. 
        """
        with open(filePath, 'r', encoding='utf-8') as f:
            text = f.read()
            text = strip_illegal_characters(text)
        try:
            with open(filePath, 'w', encoding='utf-8') as f:
                f.write(f'{self.XML_HEADER}{text}')
        except:
            raise Error(f'{_("Cannot write file")}: "{norm_path(filePath)}".')

