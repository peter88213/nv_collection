"""Build the nv_collection novelibre plugin package.
        
Note: VERSION must be updated manually before starting this script.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from shutil import copy2
import sys

sys.path.insert(0, f'{os.getcwd()}/../../novelibre/tools')
from package_builder import PackageBuilder

VERSION = '5.5.1'


class PluginBuilder(PackageBuilder):

    PRJ_NAME = 'nv_collection'
    LOCAL_LIB = 'nvcollection'
    GERMAN_TRANSLATION = True

    def __init__(self, version):
        super().__init__(version)

    def add_extras(self):
        self.add_icons()

    def add_icons(self):
        super().add_icons()
        copy2('../icons/collection.png', f'{self.buildDir}/icons')


def main():
    pb = PluginBuilder(VERSION)
    pb.run()


if __name__ == '__main__':
    main()
