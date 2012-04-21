import socket 
import rencode
import zlib
import time

class RPC: 
    Response = 1
    Error = 2
    Event = 3

class Transport(object): 

    last_sent = 0

    def __init__(self, host, port, request_id = 0): 

        self.request_id = request_id

        self.host = host
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

        self.ssl = socket.ssl(self.sock)
        self.event_handlers = {} 

    def receive(self): 
        data = ""
        while True:
            chunk = self.ssl.read(4096)
            data += chunk

            if len(chunk) == 0: 
                print "FAILING"
                break

            dobj = zlib.decompressobj()

            try: 
                response = rencode.loads(dobj.decompress(data))
            except Exception, e: 
                print "Failed to decompress chunk", e
            else: 
                if not (type(response) == tuple and len(response) >= 3):
                    print "Invalid response type", response
                else:
                    # response[0] is the response type see RPC class

                    if response[0] == RPC.Response: 
                        # response[1] is the triggering message_id
                        if response[1] != Transport.last_sent:
                            print "Last sent inconsistent", response[1], "not", Transport.last_sent

                        return response[2]
                    
                    elif response[0] == RPC.Error: 
                        # response[1] is the triggering message_id
                        # response[2] is the exception type
                        # response[3] is the exception args
                        # response[4] is the exception kwargs
                        print "exception", response

                    elif response[0] == RPC.Event: 
                        # response[1] is the event type
                        # response[2] is the event arguments
                        try: 
                            handlers = self.event_handlers[response[1]]
                        except KeyError: 
                            # there is no event de-register so this may happen
                            pass
                        else: 
                            for handler in handlers:
                                handler(*response[2])

                        data = ""
                        continue

                    else: 
                        print "Unknown response code", response

                break

        return None

    def send(self, method, *args, **kwargs): 
        self.request_id += 1
        
        Transport.last_sent = self.request_id

        rpc = zlib.compress(rencode.dumps(
                ((self.request_id, method, args, kwargs),)))

        self.ssl.write(rpc)
        return self.receive()
        
    def register_event_handler(self, event, handler): 
        if not event in self.event_handlers: 
            if not self.set_event_interest(event): 
                print "Failed to register event interest for", event
                return False 
        
        self.event_handlers.setdefault(event, set()).add(handler)
        return True
 
    def deregister_event_handler(self, event, handler): 
        # There is no rpc for deregister

        try: 
            handlers = self.event_handlers[event]
        except KeyError: 
            print "No handler", handler, "for event" 
        else:
            try:
                handlers.remove(handler)
            except KeyError: 
                print "Handler", handler, "does not exist for", event

    def login(self, username, password): 
        return self.send('daemon.login', username, password)

    def daemon_info(self):
        return self.send('daemon.info')

    def session_state(self): 
        return self.send('core.get_session_state')

    def set_event_interest(self, event):
        if not type(event) is list:
            event = [event]
        elif type(event) is tuple: 
            event = list(event)

        return self.send('daemon.set_event_interest', event)

    def torrent_status(self, torrent_id, keys): 
        method = 's' if torrent_id is None or type(torrent_id) is dict else ''
        return self.send("core.get_torrent%s_status" % method,
                torrent_id, keys, True)

    def close(self): 
        self.ssl.shutdown()
        self.ssl.close()
        
        self.sock = None 
        self.ssl = None 
        self.ctx = None
        self.host = None 
        self.port = None


