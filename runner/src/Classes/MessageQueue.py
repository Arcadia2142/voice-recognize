import sys
from multiprocessing.connection import Connection
from collections import deque

class MessageQueue(object):
    MESSAGE_GET = 1
    MESSAGE_CLEAR = 2

    def __init__(self, listener_pipe: Connection, resolver_pipe: Connection) -> None:
        self._resolver_waiting = False

        self._listener_pipe = listener_pipe
        self._resolver_pipe = resolver_pipe
        self._queue = deque()

    def _process_listener(self, data):
        if self._resolver_waiting:
            self._resolver_pipe.send(data)
            self._resolver_waiting = False
        else:
            self._queue.append(data)

    def _process_resolver(self, data):
        if data == self.MESSAGE_GET:
            if len(self._queue) > 0:
                message = self._queue.popleft()
                self._resolver_pipe.send(message)
            else:
                self._resolver_waiting = True

        elif data == self.MESSAGE_CLEAR:
            self._queue.clear()

    def run(self) -> None:
        while True:
            if self._listener_pipe.poll(0.01):
                self._process_listener(self._listener_pipe.recv())

            if self._resolver_pipe.poll(0.01):
                self._process_resolver(self._resolver_pipe.recv())

