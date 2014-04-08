from threading import Lock


class PickleLock(object):

    def __init__(self):
        self._lock = Lock()

    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, traceback):
        self.release()

    def __reduce__(self):
        return (self.__class__, ())
