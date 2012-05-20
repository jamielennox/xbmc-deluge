from transport import Transport
import base64

import xbmc
import xbmcgui

class Client:

    def __init__(self):
        self.transport = None
        self.torrents = {}
        self.torrent_keys = [ 'queue', 'name', 'total_size',
                'state', 'progress', 'num_seeds' ]

    def connect(self, host="127.0.0.1", port=58846, username="", password=""):
        self.transport = Transport(host, port)

        try:
            r = self.transport.login(username, password)
        except Exception, e:
            print "login failed", e
            self.transport = None
            return False

        print "Protocol version", self.transport.daemon_info()

        for event, handler in [
                ('TorrentStateChangedEvent', self._on_torrent_state_changed),
                ('TorrentRemovedEvent', self._on_torrent_removed),
                ('TorrentAddedEvent', self._on_torrent_added) ]:

            if not self.transport.register_event_handler(event, handler):
                print "Failed to register handler", event, handler

        self.torrents = self.transport.torrent_status(None, self.torrent_keys)
        return True

    def disconnect(self):
        if self.transport:
            self.torrents = {}
            self.transport.close()

        self.transport = None

    def update(self):
        updates = self.transport.torrent_status(None, self.torrent_keys)

        if updates:
            for torr_id, vals in updates.iteritems():
                try:
                    #self.torrents.setdefault(torr_id, {}).update(vals)
                    self.torrents[torr_id].update(vals)
                except KeyError:
                    print "Receiving updates for unexpected torrent", torr_id
        else:
            print "Update checking failed"

        return self.torrents

    def add_torrent(self, filename):
        torrent_id = None

        try:
            with open(filename, 'rb') as f:
                data = base64.b64encode(f.read())
        except IOError, e:
            print "Failed to open torrent file:", e
            xbmcgui.Dialog().ok("Failed", "Failed to add: %s" % filename)
        else:
            torrent_id = self.transport.send('core.add_torrent_file', filename, data, None)

        return torrent_id

    def remove_torrent(self, torrent_id, with_data = False):
        ret = self.transport.send('core.remove_torrent', torrent_id, with_data)

        print "Remove returned", ret

        if ret:
            try:
                del self.torrents[torrent_id]
                print "Successfully removed torrent id", torrent_id
            except KeyError:
                pass
                print "Failed to remove torrent_id", torrent_id
        else:
            xbmcgui.Dialog().ok("Failed", "Failed to remove: %s" % self.torrents[torrent_id]['name'])

        return ret

    def _on_torrent_state_changed(self, torrent_id, state):
        print "torrent state changed", torrent_id, state

    def _on_torrent_added(self, torrent_id):
        print "torrent added", torrent_id
        self.torrents[torrent_id] = {}

    def _on_torrent_removed(self, torrent_id):
        print "torrent removed", torrent_id
        try:
            del self.torrents[torrent_id]
        except KeyError:
            pass

