from transport import Transport
import base64

import xbmc
import xbmcgui


class Client:

    def __init__(self):
        self.transport = None
        self.torrents = {}
        self.torrent_keys = ['queue', 'name', 'total_size',
                'state', 'progress', 'num_seeds', 'files',
                'download_payload_rate', 'upload_payload_rate']
        self.session_keys = ['download_rate', 'payload_download_rate',
                'upload_rate', 'payload_upload_rate']

    def connect(self, host="127.0.0.1", port=58846, username="", password=""):
        self.transport = Transport(host, port)

        try:
            r = self.transport.login(username, password)
        except Exception, e:
            print "login failed", e
            self.transport = None
            return False

        print "login infor is r", r
        print "Protocol version", self.transport.daemon_info()

        for event, handler in [
                ('TorrentStateChangedEvent', self._on_torrent_state_changed),
                ('TorrentRemovedEvent', self._on_torrent_removed),
                ('TorrentAddedEvent', self._on_torrent_added)]:

            if not self.transport.register_event_handler(event, handler):
                print "Failed to register handler", event, handler

        self.torrents = self.transport.torrent_status(None, self.torrent_keys)
        return True

    def disconnect(self):
        if self.transport:
            self.torrents = {}
            self.transport.close()

        self.transport = None

    def update_torrents(self):
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

    def update_session(self):
        return self.transport.session_status(self.session_keys)

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

    def remove_torrent(self, torrent_id, with_data=False):
        ret = self.transport.send('core.remove_torrent', torrent_id, with_data)

        # I'm not sure what happens here. It appears that the server
        # is not returning data after a remove_torrent event

        if not ret:
            try:
                name = self.torrents[torrent_id]['name']
            except KeyError:
                name = torrent_id

            xbmcgui.Dialog().ok("Failed", "Failed to remove: %s" % name)

        return ret

    def resume_torrent(self, torrent_id):
        xbmc.log("Resume torrent: %s" % torrent_id, xbmc.LOGDEBUG)
        return self.transport.send('core.resume_torrent', [torrent_id])

    def pause_torrent(self, torrent_id):
        xbmc.log("Pause torrent: %s" % torrent_id, xbmc.LOGDEBUG)
        return self.transport.send('core.pause_torrent', [torrent_id])

    def _on_torrent_state_changed(self, torrent_id, state):
        xbmc.log("torrent state changed: %s -> state" % (torrent_id, state),
                xbmc.LOGDEBUG)

    def _on_torrent_added(self, torrent_id):
        xbmc.log("torrent added: %s" % torrent_id, xbmc.LOGDEBUG)
        if not torrent_id in self.torrents:
            self.torrents[torrent_id] = {}

    def _on_torrent_removed(self, torrent_id):
        xbmc.log("torrent removed: %s" % torrent_id, xbmc.LOGDEBUG)

        try:
            del self.torrents[torrent_id]
        except KeyError:
            xbmc.log("Failed to remove torrent_id: %s" % torrent_id,
                    xbmc.LOGWARNING)

