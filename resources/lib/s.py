import sys

from repeater import Repeater
from client import Client 

client = Client('192.168.1.2', 58846, 'jamie', '55588688')
repeater = Repeater(1.0, client.update)

try: 
    repeater.start(threaded = False) 
except KeyboardInterrupt: 
    pass

client.close()

