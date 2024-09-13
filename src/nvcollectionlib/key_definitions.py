"""Provide platform specific key definitions for the nv_collection plugin.

Copyright (c) 2024 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvcollectionlib.nvcollection_globals import PLATFORM
from nvcollectionlib.generic_keys import GenericKeys
from nvcollectionlib.mac_keys import MacKeys
from nvcollectionlib.windows_keys import WindowsKeys

if PLATFORM == 'win':
    KEYS = WindowsKeys()
elif PLATFORM == 'ix':
    KEYS = GenericKeys()
elif PLATFORM == 'mac':
    KEYS = MacKeys()
else:
    KEYS = GenericKeys()
