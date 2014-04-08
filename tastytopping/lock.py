# -*- coding: utf-8 -*-

"""
.. module: lock
    :platform: Unix, Windows
    :synopsis: Provides a picklable Lock.

.. moduleauthor:: Christian Boelsen <christian.boelsen@hds.com>
"""


__all__ = ('PickleLock', )


from threading import Lock


class PickleLock(object):
    """A standard threading Lock that can be pickled."""

    def __init__(self):
        self._lock = Lock()

    def acquire(self):
        """threading.Lock.acquire"""
        self._lock.acquire()

    def release(self):
        """threading.Lock.release"""
        self._lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, *args):
        self.release()

    def __reduce__(self):
        return (self.__class__, ())
