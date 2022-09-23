"""Wrapper for importing Qt.

Flattens all Qt imports into a single package, so we can avoid *
imports without excessive verbosity.
"""

from Qt.QtCore import *  # noqa
from Qt.QtGui import *  # noqa
from Qt.QtWidgets import *  # noqa
