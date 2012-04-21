import sys

from repeater import Repeater 
from client import Client 

standalone = __name__ == '__main__'

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467
KEY_MENU_ID = 92

EXIT_SCRIPT = ( 6, 10, 247, 275, 61467, 216, 257, 61448, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )

if standalone:
    import pprint
    class FakeList(object): 
        def __init__(self): 
            self.reset()

        def reset(self): 
            self.items = []

        def addItem(self, item): 
            self.items.append(item)

        def addItems(self, items): 
            self.items.extend(items)

        def setEnabled(self, v): 
            pprint.pprint(self.items)

    class FakeListItem(object): 
        def __init__(self): 
            self.properties = {} 
        
        def setProperty(self, k, v): 
            self.properties[k] = v 

        def getControl(self, item): 
            return None

        def __repr__(self): 
            return self.properties.__repr__()
            
        def setLabel(self, v):
            self.properties['label'] = v

    class FakeWindow(object): 
        def onInit(self): 
            self.tor_list = FakeList() 

        def close(self):
            pass
        
        def getControl(self, item): 
            if item == 120: 
                return self.tor_list
            else:
                return None

    gui_base = FakeWindow
    list_item = FakeListItem
else:
    import xbmc 
    import xbmcgui 
    from strings import * 

    _ = sys.modules[ "__main__" ].__language__
    __settings__ = sys.modules[ "__main__" ].__settings__

    gui_base = xbmcgui.WindowXML
    list_item = xbmcgui.ListItem

class DelugeGui(gui_base):

    status_icons = {
        'Paused' : 'paused.png', 
        'Seeding' : 'seeding.png', 
        'Downloading' : 'down.png'
    } 

    def onInit(self):
        gui_base.onInit(self)
        self.items = []
        self.repeater = Repeater(1.0, self.update)
        
        p = xbmcgui.DialogProgress()
        p.create('Deluge', 'Connecting to Deluge')
        #self.client = Client("192.168.1.2", 58846, "jamie", "55588688")
        
        #try:
        self.client = Client(__settings__.getSetting('host'),
                int(__settings__.getSetting('port')),
                __settings__.getSetting('user'),
                __settings__.getSetting('password'))
        #except:
        p.close()
        #    self.close()

        #    (type, e, traceback) = sys.exc_info()

        #    print "Connect Error", type, e, traceback

        #    if xbmcgui.Dialog().yesno('Deluge Error', 'Unable to Connect', 'Open Settings'):
        #        __settings__.openSettings()
        #else:
        self.repeater.start(daemon = True)

    def start(self):
        self.update()

    def update(self): 
        
        def torr_cmp(_a, _b): 
            a = torrents[_a]['queue']
            b = torrents[_b]['queue']

            if a == b: return 0
            if a < 0: return 1
            if b < 0: return -1

            return -1 if a < b else 1

        self.client.update()
        torrents = self.client.torrents
        torrent_keys = sorted(torrents, torr_cmp)
        tor_list = self.getControl(120)

        count = len(torrent_keys)
        if count != len(self.items): 
            tor_list.reset()
            self.items = [ list_item() for u in range(count) ]
            tor_list.addItems(self.items)

        for key, item in zip(torrent_keys, self.items): 
            torrent = torrents[key]

            item.setLabel(torrent['name'])
            item.setProperty('TorrentID', key)
            item.setProperty('TorrentStatusIcon', 
                    DelugeGui.status_icons.get(torrent['state'], 'default.png'))
            item.setProperty('TorrentProgress', "%.2f" % torrent['progress'])

            if standalone: 
                item.setProperty('raw', torrent)
        
        tor_list.setEnabled(count > 0) 
        
    def close(self): 
        self.repeater.stop() 
        gui_base.close(self) 

    def onClick(self, controlID): 
        pass

    def onFocus(self, controlID): 
        pass

    def onAction(self, action): 
        if (action.getButtonCode() in CANCEL_DIALOG) or (action.getId() == KEY_MENU_ID):
            self.close()

if standalone:
    import time 

    gui = DelugeGui()
    gui.onInit()
    time.sleep(5)
    gui.close()

    
