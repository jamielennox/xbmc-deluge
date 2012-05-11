from transport import Transport 

class Client: 

    class AlreadyConnected(Exception): 
        def __init__(self, host, port, username): 
            self.host = host
            self.port = port 
            self.username = username 

        def __repr__(self): 
            return "Exception: Already connected to %s@%s:%d" % (self.username, self.host, self.port)

    class NoConnection(Exception): 
        pass

    def __init__(self): 
        self.transport = None 
        self.torrents = {}
        self.torrent_keys = [ 'queue', 'name', 'total_size',
                'state', 'progress', 'num_seeds' ]

    def connect(self, host="127.0.0.1", port=58846, username="", password=""):
        if self.transport: 
            raise Client.AlreadyConnected(self.transport.host, self.transport.port, self.transport.username)

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
        if not self.transport: 
            raise Client.NoConnection() 

        for torr_id, vals in self.transport.torrent_status(None, self.torrent_keys).iteritems():
            self.torrents.setdefault(torr_id, {}).update(vals)

    def _on_torrent_state_changed(self, torrent_id, state): 
        print "torrent state changed", torrent_id, state

    def _on_torrent_added(self, torrent_id, state): 
        print "torrent added", torrent_id, state

    def _on_torrent_removed(self, torrent_id): 
        print "torrent removed", torrent_id


