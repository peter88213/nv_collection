"""Provide a class for opening and preprocessing nvcx XML files.

Copyright (c) 2025 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvlib.novx_globals import norm_path
from nvlib.nv_locale import _
import xml.etree.ElementTree as ET


class NvcxOpener:
    """nvcx XML data reader, verifier, and preprocessor."""

    @classmethod
    def get_xml_root(cls, filePath, majorVersion, minorVersion):
        """Return a reference to the XML root of the nvcx file at filePath.
        
        majorVersion and minorVersion are integers.
        Check the file version and preprocess the data, if applicable.
        """
        try:
            xmlTree = ET.parse(filePath)
        except Exception as ex:
            raise RuntimeError(
                f'{_("Cannot process file")}: '
                f'"{norm_path(filePath)}" - {str(ex)}'
            )

        xmlRoot = xmlTree.getroot()
        if not xmlRoot.tag in ('nvcx', 'COLLECTION'):
            msg = _("No valid xml root element found in file")
            raise RuntimeError(f'{msg}: "{norm_path(filePath)}".')

        fileMajorVersion, fileMinorVersion = cls._get_file_version(
            xmlRoot,
            filePath,
        )
        fileMajorVersion, fileMinorVersion = cls._upgrade_file_version(
            xmlRoot,
            fileMajorVersion,
            fileMinorVersion,
        )
        cls._check_version(
            fileMajorVersion,
            fileMinorVersion,
            filePath,
            majorVersion,
            minorVersion,
        )
        return xmlRoot

    @classmethod
    def _check_version(
            cls,
            fileMajorVersion,
            fileMinorVersion,
            filePath,
            majorVersion,
            minorVersion,
    ):
        # Raise an exception if the file
        # is not compatible with the supported DTD.
        if fileMajorVersion > majorVersion:
            msg = _('The collection "{}" was created with a newer plugin version.')
            raise RuntimeError(msg.format(norm_path(filePath)))

        if fileMajorVersion < majorVersion:
            msg = _('The collection "{}" was created with an outdated plugin version.')
            raise RuntimeError(msg.format(norm_path(filePath)))

        if fileMinorVersion > minorVersion:
            msg = _('The collection "{}" was created with a newer plugin version.')
            raise RuntimeError(msg.format(norm_path(filePath)))

    @classmethod
    def _upgrade_file_version(
            cls,
            xmlRoot,
            fileMajorVersion,
            fileMinorVersion,
    ):
        # Convert the data from legacy files
        # Return the version number adjusted, if applicable.
        return fileMajorVersion, fileMinorVersion

    @classmethod
    def _get_file_version(cls, xmlRoot, filePath):
        # Return the major and minor file version as integers.
        # Raise an exception if there is none.
        # Update xmlRoot.
        try:
            (
                fileMajorVersionStr,
                fileMinorVersionStr
            ) = xmlRoot.attrib['version'].split('.')
            fileMajorVersion = int(fileMajorVersionStr)
            fileMinorVersion = int(fileMinorVersionStr)
        except (KeyError, ValueError):
            msg = _("No valid version found in file")
            raise RuntimeError(msg.format(norm_path(filePath)))

        return fileMajorVersion, fileMinorVersion

