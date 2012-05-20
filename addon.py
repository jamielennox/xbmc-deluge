import sys
import os
import urllib

import xbmcaddon

__scriptname__ = "XBMC-Deluge"
__author__ = "Jamie Lennox <jamielennox@gmail.com>"
__version__ = "0.1"

__settings__ = xbmcaddon.Addon(id='script.deluge')
__language__ = __settings__.getLocalizedString

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __settings__.getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

from gui import DelugeGui
w = DelugeGui('script-deluge-main.xml', __settings__.getAddonInfo('path'), "Default")
w.doModal()
del w
