from cache import Cache
from storageManager import Storage


class Manager:
    def __init__(self):
        self.storage = Storage(self)
        self.cache = Cache(self)

    def issue_request(self, addr, length, typ):
        self.cache.issue_request(addr, length, typ)

