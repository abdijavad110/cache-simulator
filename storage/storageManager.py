import threading


class Storage:
    def __init__(self, manager):
        # real implementation:
        # self.__cache_miss_queue = []
        # self.__cache_lock = threading.Lock()
        # self.__storage_queue = []
        # self.__storage_lock = threading.Lock()

        # simplified:
        self.IO_cnt = 0
        self.manager = manager

    def issue_request(self, addr, length, redirect):
        self.IO_cnt += 1
        if redirect:
            self.manager.cache.promote(addr, length)
        return True
