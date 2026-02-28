"""Provide a class with mouse operation definitions for the Mac OS.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvcollection.platform.generic_mouse import GenericMouse


class MacMouse(GenericMouse):

    MOVE_NODE = '<Option-B1-Motion>'
