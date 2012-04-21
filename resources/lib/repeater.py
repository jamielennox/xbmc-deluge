# -*- coding: utf-8 -*-
# Copyright (c) 2010 Correl J. Roush

import threading

class Repeater(object):
    def __init__(self, interval, action, arguments = []):
        self.interval = interval
        self.action = action
        self.arguments = arguments
        self.thread = None
        self.event = None

    def start(self, threaded = True, daemon = False):
        if self.event:
            return

        self.event = threading.Event()

        if threaded: 
            self.thread = threading.Thread(target=Repeater.repeat, args=(self.event, self.interval, self.action, self.arguments))
            self.thread.daemon = daemon
            self.thread.start()

        else: 
            Repeater.repeat(self.event, self.interval, self.action, self.arguments)

    def stop(self):
        if not self.event:
            return

        self.event.set()

        if self.thread:
            self.thread.join()

        self.event = None
        self.thread = None

    def join(self): 
        if self.thread: 
            self.thread.join() 

    @staticmethod
    def repeat(event, interval, action, arguments = []):
        while True:
            event.wait(interval)

            if event.isSet():
                break;

            action(*arguments)


if __name__ == '__main__':
    import time

    def foo(a, b):
        print a, b

#    r = Repeater(1.0, foo, ['foo', 'bar'])
#    r.start()
#    time.sleep(10)
#    r.stop()

    r = Repeater(1.0, foo, ['foo', 'bar'])
    r.start(threaded = False)
