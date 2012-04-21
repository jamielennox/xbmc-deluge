from transport import Transport 

class Client(Transport): 
    def __init__(self, host, port, user, password): 
        Transport.__init__(self, host, port) 

        r = self.login(user, password)
        print "Protocol version", self.daemon_info()

        for event, handler in [
                ('TorrentStateChangedEvent', self._on_torrent_state_changed),
                ('TorrentRemovedEvent', self._on_torrent_removed),
                ('TorrentAddedEvent', self._on_torrent_added) ]:

            if not self.register_event_handler(event, handler): 
                print "Failed to register handler", event, handler

        self.torrent_keys = [ 'queue', 'name', 'total_size',
                'state', 'progress', 'num_seeds' ]

        self.torrents = self.torrent_status(None, self.torrent_keys)
   
    def update(self):  
        print "updating"
        self.torrent_status(None, self.torrent_keys)

    def _on_torrent_state_changed(self, torrent_id, state): 
        print "torrent state changed", torrent_id, state

    def _on_torrent_added(self, torrent_id, state): 
        print "torrent added", torrent_id, state

    def _on_torrent_removed(self, torrent_id): 
        print "torrent removed", torrent_id


