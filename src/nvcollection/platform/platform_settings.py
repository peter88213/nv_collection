"""Provide platform specific key definitions for the nv_collection plugin.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import platform

from nvcollection.platform.generic_keys import GenericKeys
from nvcollection.platform.generic_mouse import GenericMouse
from nvcollection.platform.mac_keys import MacKeys
from nvcollection.platform.windows_keys import WindowsKeys

if platform.system() == 'Windows':
    PLATFORM = 'win'
    KEYS = WindowsKeys()
    MOUSE = GenericMouse
elif platform.system() in ('Linux', 'FreeBSD'):
    PLATFORM = 'ix'
    KEYS = GenericKeys()
    MOUSE = GenericMouse
elif platform.system() == 'Darwin':
    PLATFORM = 'mac'
    KEYS = MacKeys()
    MOUSE = GenericMouse
else:
    PLATFORM = ''
    KEYS = GenericKeys()
    MOUSE = GenericMouse

