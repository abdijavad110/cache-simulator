from storage.cache import Cache
from storage.storageManager import StgMgr


class Manager:
    def __init__(self):
        self.cache = Cache()
        self.stg_mgr = StgMgr()

    def issue_request(self, addr, length):
        self.cache.issue_request(addr, length)

