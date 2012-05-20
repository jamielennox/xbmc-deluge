
import xbmc
import xbmcgui
import threading

from control import Control

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467
KEY_MENU_ID = 92

EXIT_SCRIPT = ( 6, 10, 247, 275, 61467, 216, 257, 61448, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )

class DelugeDetailsGui(xbmcgui.WindowXML):

    def onInit(self):
        xbmcgui.WindowXML.onInit(self)
        self.thread = threading.Thread(target=self.update)
        self.close_event = threading.Event()
        self.thread.start()

    def set_torrent(self, client, torrent_id):
        self.client = client
        self.torrent_id = torrent_id

    def update(self):
        first = True

        progress_bar = self.getControl(Control.Progress)
        name = self.getControl(Control.Name)
        status = self.getControl(Control.Status)
        file_list = self.getControl(Control.FileList)

        while first or not self.close_event.wait(1.0):
            torrent = self.client.update()[self.torrent_id]

            name.setLabel(torrent['name'])
            status.setLabel("%.2f" % torrent['progress'])

            if first:
                for i in torrent['files']:
                    l = xbmcgui.ListItem(label=i['path'])
                    file_list.addItem(l)

            first = False

    def close(self):
        self.close_event.set()
        self.thread.join()
        xbmcgui.WindowXML.close(self)

    def onAction(self, action):
        if (action.getButtonCode() in CANCEL_DIALOG) or (action.getId() == KEY_MENU_ID):
            self.close()
            pass

    def onClick(self, controlID):
        pass

    def onFocus(self, controlID):
        pass
