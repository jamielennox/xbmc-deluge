import socket
import ssl
import select
import deluge.rencode as rencode
import zlib
import xbmc
import time
import threading
import datetime

class RPC:
    Response = 1
    Error = 2
    Event = 3

class Transport(object):

    read_size = 4096

    def __init__(self, host, port, request_id = 0):

        self.request_id = request_id

        self.host = host
        self.port = port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock = ssl.wrap_socket(s)
        self.sock.connect((self.host, self.port))

        self.event_handlers = {}
        self.last_sent = 0

        self.rlock = threading.RLock()

    def receive(self):

        data = ""
        while True:
            #read, write, err = select.select([self.sock], [], [], 5.0)

            #if not (read or write or err):
            #    print "Receive Timed Out"
            #    break

            try:
                chunk = self.sock.read(Transport.read_size)
            except ssl.SSLError, e:
                xbmc.log("Deluge: Read Error: %s" % e,
                        xbmc.LOGWARNING)
                break

            dobj = zlib.decompressobj()

            if len(chunk) == 0:
                xbmc.log("Deluge: Read Socket Closed", xbmc.LOGSEVERE)
                break
            else:
                data += chunk

            try:
                response = rencode.loads(dobj.decompress(data))
            except Exception, e:
                # this probably just means that the sock recv was smaller
                # than the message size and so didn't get enought data to
                # decode. Get more data.

                if len(chunk) != Transport.read_size:
                    xbmc.log("Deluge: Failed to decompress chunk: %s" % e,
                            xbmc.LOGWARNING)

                continue

            else:
                data = dobj.unused_data

                if not (type(response) == tuple and len(response) >= 3):
                    xbmc.log("Deluge: Invalid response type: %s" % response,
                            xbmc.LOGWARNING)
                else:
                    # response[0] is the response type see RPC class

                    if response[0] == RPC.Response:
                        # response[1] is the triggering message_id
                        if response[1] != self.last_sent:
                            xbmc.log("Deluge: Last sent inconsistent %s not %s" % (response[1], self.last_sent),
                                    xbmc.LOGNOTICE)

                        return response[2]

                    elif response[0] == RPC.Error:
                        # response[1] is the triggering message_id
                        # response[2] is the exception type
                        # response[3] is the exception args
                        # response[4] is the exception kwargs
                        exc_type, exc_msg, exc_tb = response[2]
                        xbmc.log("Deluge: Received Exception - %s: %s" % (exc_type, exc_msg), xbmc.LOGWARNING)
                        xbmc.log("Deluge: %s" % exc_tb, xbmc.LOGWARNING)

                    elif response[0] == RPC.Event:
                        # response[1] is the event type
                        # response[2] is the event arguments
                        try:
                            handlers = self.event_handlers[response[1]]
                        except KeyError:
                            # there is no event de-register so this may happen
                            xbmc.log("Deluge: Undefined event handler for %s" % response[1],
                                    xbmc.LOGWARNING)
                        else:
                            for handler in handlers:
                                try:
                                    handler(*response[2])
                                except Exception, e:
                                    # log it but don't let it interrupt the flow
                                    print "Exception handler error", e

                        continue

                    else:
                        xbmc.log("Deluge: Unknown response code: %s" % response,
                                xbmc.LOGWARNING)

                break

        return None

    def send(self, method, *args, **kwargs):
        self.rlock.acquire()
        self.request_id += 1

        self.last_sent = self.request_id

        rpc = zlib.compress(rencode.dumps(
                ((self.request_id, method, args, kwargs),)))

        self.sock.write(rpc)
        recv = self.receive()

        self.rlock.release()

        return recv

    def register_event_handler(self, event, handler):
        if not event in self.event_handlers:
            if not self.set_event_interest(event):
                xbmc.log("Deluge: Failed to register event interest for %s" % event,
                        xbmc.LOGWARNING)
                return False

        self.event_handlers.setdefault(event, set()).add(handler)
        return True

    def deregister_event_handler(self, event, handler):
        # There is no rpc for deregister
        try:
            handlers = self.event_handlers[event]
        except KeyError:
            xbmc.log("Deluge: No handler %s for event" % handler, xbmc.LOGWARNING)
        else:
            try:
                handlers.remove(handler)
            except KeyError:
                xbmc.log("Deluge: Handler %s does not exist for %s" % (handler, event),
                        xbmc.LOGWARNING)

    def login(self, username, password):
        # daemon.login returns auth level on success
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
        self.sock.close()

        self.sock = None
        self.host = None
        self.port = None

