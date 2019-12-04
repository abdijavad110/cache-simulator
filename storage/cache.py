import threading
from conf import conf


class CacheElem:
    def __init__(self, addr):
        self.addr = addr


class Cache:
    def __init__(self):
        self.__cache = []
        self.presence = [False]*conf['maxAddr']
        # todo add requests queue
        self.miss_cnt = 0
        self.hit_cnt = 0
        self.evict_cnt = 0

    def issue_request(self, addr, length):
        # divide big requests
        # todo use better division
        sub_req = [
            addr + l*conf['blkSize'] for l in range(1, length//conf['blkSize'])
                   ]
        map(lambda q: self.issue_request(q, conf['blkSize']), sub_req)

        # check hit
        if self.presence[addr]:
            self.hit_cnt += 1
            # LRU
            for i, v in enumerate(self.__cache):
                if v.addr == addr:
                    self.__cache[0], self.__cache[i] = self.__cache[i], self.__cache[0]
                    break
            return

        # miss occurred
        self.miss_cnt += 1
        if len(self.__cache) == conf['cacheSize']:
            free_addr = self.evict(addr)
        else:
            free_addr = len(self.__cache)

        self.__cache.insert(free_addr, CacheElem(addr))

    def evict(self, addr):
        # LRU
        self.evict_cnt += 1
        self.__cache.pop()
        return conf['cacheSize']
