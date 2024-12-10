"""Provide a class for novelibre book series representation.

Copyright (c) 2024 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""


class Series:
    """Book series representation for the collection.
    
    A series has a title and a description. 
    """

    def __init__(self):
        self.title = None
        self.desc = None
