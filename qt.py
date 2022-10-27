"""Wrapper for importing Qt.

Flattens all Qt imports into a single package, so we can avoid *
imports without excessive verbosity.
"""

from qtpy.QtCore import *  # noqa
from qtpy.QtGui import *  # noqa
from qtpy.QtWidgets import *  # noqa
