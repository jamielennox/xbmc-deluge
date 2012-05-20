import sys
import time

from control import Control
from client import Client

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467
KEY_MENU_ID = 92

EXIT_SCRIPT = ( 6, 10, 247, 275, 61467, 216, 257, 61448, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )

import xbmc
import xbmcgui
import details
import Queue
import threading
import traceback

from strings import *

_ = sys.modules["__main__"].__language__
__settings__ = sys.modules["__main__"].__settings__

class MessageType:
    METHOD = 1
    EXIT = 2

class DelugeGui(xbmcgui.WindowXML):

    status_icons = {
        'Paused' : 'paused.png',
        'Seeding' : 'seeding.png',
        'Downloading' : 'down.png'
    }

    def onInit(self):
        xbmcgui.WindowXML.onInit(self)
        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self.update)

        self.items = []
        self.client = Client()
        self.doConnect()

    def doConnect(self):
        def loginFailed():
            if xbmcgui.Dialog().yesno('Deluge Error', 'Unable to Connect', 'Open Settings'):
                __settings__.openSettings()
                self.doConnect()

        host = __settings__.getSetting('host')
        p = xbmcgui.DialogProgress()
        p.create('Deluge', "Connecting to Deluge on %s" % host)

        try:
            if not self.client.connect(host,
                    int(__settings__.getSetting('port')),
                    __settings__.getSetting('user'),
                    __settings__.getSetting('password')):
                loginFailed()
                return

        except:
            p.close()
            self.close()

            (type, e, traceback) = sys.exc_info()

            print "Connect Error", type, e, traceback
            loginFailed()

        else:
            if p.iscanceled():
                print "LOGIN CANCELLED"
                p.close()
                self.close()
            else:
                p.close()
                self.thread.start()

    def update(self):
        def torr_cmp(_a, _b):
            a = torrents[_a]['queue']
            b = torrents[_b]['queue']

            if a == b: return 0
            if a < 0: return 1
            if b < 0: return -1

            return -1 if a < b else 1

        running = True

        while running:
            try:
                msg_type, msg_args = self.queue.get(True, 1.0)
            except Queue.Empty:
                pass
            else:
                if msg_type == MessageType.METHOD:
                    try:
                        method, args, kwargs = msg_args
                        method(*args, **kwargs)
                    except Exception, e:
                        xbmc.log("Deluge: Failed to run client method: %s" % e.message,
                                xbmc.LOGWARNING)
                        traceback.print_exc()

                elif msg_type == MessageType.EXIT:
                    running = False
                    break

            torrents = self.client.update()
            torrent_keys = sorted(torrents, torr_cmp)
            tor_list = self.getControl(Control.TorrentList)

            count = len(torrent_keys)
            if count != len(self.items):
                tor_list.reset()
                self.items = [ xbmcgui.ListItem() for u in range(count) ]
                tor_list.addItems(self.items)

            for key, item in zip(torrent_keys, self.items):
                torrent = torrents[key]

                item.setLabel(torrent['name'])
                item.setProperty('TorrentID', key)
                item.setProperty('TorrentStatusIcon',
                        DelugeGui.status_icons.get(torrent['state'], 'default.png'))
                item.setProperty('TorrentProgress', "%.2f" % torrent['progress'])

            tor_list.setEnabled(count > 0)

    def enqueue(self, method, *args, **kwargs):
        self.queue.put((MessageType.METHOD, (method, args, kwargs)))

    def close(self):
        self.queue.put((MessageType.EXIT, None))
        self.thread.join()

        xbmcgui.WindowXML.close(self)

    def onClick(self, controlID):
        selected_torrent = self.getControl(Control.TorrentList).getSelectedItem()

        if controlID == Control.Add:
            filename = xbmcgui.Dialog().browse(1, 'Find Torrent', 'files', '.torrent')
            if not filename in (None, ''):
                self.enqueue(self.client.add_torrent, filename)

        elif controlID == Control.Remove:
            if not selected_torrent:
                return

            torrent_id = selected_torrent.getProperty('TorrentID')
            if xbmcgui.Dialog().yesno("Remove", "Do you really want to remove %s" % self.client.torrents[torrent_id]['name']):
                remove_data = xbmcgui.Dialog().yesno("Remove Data", "Remove data as well?")
                self.enqueue(self.client.remove_torrent, torrent_id, remove_data)

        elif controlID == Control.Play:
            torrent_id = selected_torrent.getProperty('TorrentID')
            self.enqueue(self.client.resume_torrent, torrent_id)

        elif controlID == Control.Pause:
            torrent_id = selected_torrent.getProperty('TorrentID')
            self.enqueue(self.client.pause_torrent, torrent_id)

        elif controlID == Control.TorrentList:
            torrent_id = selected_torrent.getProperty('TorrentID')

            w = details.DelugeDetailsGui("script-deluge-details.xml",
                    __settings__.getAddonInfo('path') , "Default")
            w.set_torrent(self.client, torrent_id)
            #w.setTorrent(self.transmission, int(item.getProperty('TorrentID')))
            w.doModal()
            del w

        else:
            print "Unhandled control", controlID

    def onFocus(self, controlID):
        pass

    def onAction(self, action):
        if (action.getButtonCode() in CANCEL_DIALOG) or (action.getId() == KEY_MENU_ID):
            self.close()


