import threading


class StgMgr:
    def __init__(self):
        # real implementation:
        # self.__cache_miss_queue = []
        # self.__cache_lock = threading.Lock()
        # self.__storage_queue = []
        # self.__storage_lock = threading.Lock()

        # simplified:
        self.IO_cnt = 0
        pass

    def issue_request(self, addr, length):
        self.fulfilled_requests += 1
        return True
