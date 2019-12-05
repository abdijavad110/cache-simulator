import threading
from conf import conf


class CacheElem:
    def __init__(self, addr):
        self.addr = addr


class Cache:
    def __init__(self):
        self.__cache = []
        self.presence = [False]*(conf['maxAddr']//conf['minReqLen'])
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
        if self.presence[addr//conf['minReqLen']]:
            self.hit_cnt += 1
            self.__some_thing_unnamed(addr)
            return

        # miss occurred
        self.miss_cnt += 1
        self.promote(addr)

    def __some_thing_unnamed(self, addr):
        # LRU
        for i, v in enumerate(self.__cache):
            if v.addr == addr:
                # fixme promote instead of replacement
                self.__cache[0], self.__cache[i] = self.__cache[i], self.__cache[0]
                break

    def promote(self, addr):
        if len(self.__cache) == conf['cacheSize']:
            free_addr = self.__evict(addr)
        else:
            free_addr = len(self.__cache)

        self.__cache.insert(free_addr, CacheElem(addr))
        self.presence[addr//conf['minReqLen']] = True

    def __evict(self, addr):
        # LRU
        self.evict_cnt += 1
        self.__cache.pop()
        self.presence[addr//conf['minReqLen']] = False
        return conf['cacheSize'] - 1
