import threading
from conf import conf
from storage.storageManager import Storage


class CacheElem:
    def __init__(self, addr, typ, idle_time=0):
        self.addr = addr
        self.typ = typ
        self.idle_time = idle_time
        self.accesses = 0


class Consts:
    read = conf.rSym
    write = conf.wSym
    ram_blk = 0
    ssd_blk = 1
    hdd_blk = 2


class Cache:
    def __init__(self, manager):
        self.__cache = []
        self.presence = [False]*(conf.maxAddr//conf.minReqLen+1)
        self.miss_cnt = 0
        self.hit_cnt = 0
        self.write_cnt = 0
        self.manager = manager

        self.__WCQ = []
        self.__SPQ = []
        self.ram_blk_cnt = 0
        self.requests_cnt = 0
        self.thread = None
        # fixme fix qt update
        self.qt = 100
        self.promotion_tsh = 100

    def issue_request(self, addr, length, typ):
        self.requests_cnt += 1
        if self.requests_cnt == conf.ssdUpdateInterval:
            self.requests_cnt = 0
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self.update_ssd, daemon=True)
                self.thread.start()

        if typ == Consts.write:
            # case 2
            for i, blk in enumerate(self.__WCQ):
                if blk.addr == addr:
                    del self.__WCQ[i]
                    return True
            for i, blk in enumerate(self.__SPQ):
                if blk.addr == addr:
                    del self.__SPQ[i]
                    return True

        else:
            # case 1
            # todo use presence to accelerate search
            # search WCQ
            for i, blk in enumerate(self.__WCQ):
                if blk.addr == addr:
                    if blk.typ == Consts.hdd_blk:
                        # case 1.2
                        self.miss_cnt += 1
                        blk.typ = Consts.ram_blk
                        self.ram_blk_cnt += 1
                        del self.__WCQ[i]
                        self.__WCQ.insert(0, blk)
                        self._ram_replace()
                    else:
                        # case 1.1
                        self.hit_cnt += 1
                        print(blk.addr)
                        del self.__WCQ[i]
                        print(blk.addr)
                        self.__WCQ.insert(0, blk)
                    return True

            # search SPQ
            for i, blk in enumerate(self.__SPQ):
                if blk.addr == addr:
                    # case 1.3
                    self.hit_cnt += 1
                    del self.__SPQ[i]
                    self.__WCQ.insert(0, blk)
                    self.wcq_evict()
                    return True

            # case 1.4
            self.miss_cnt += 1
            new_blk = CacheElem(addr, Consts.ram_blk)
            self.__WCQ.insert(0, new_blk)
            self._ram_replace()
            self.wcq_evict()

    def wcq_evict(self):
        # FixMe find and evict block y
        y = CacheElem()
        for blk in self.__SPQ:
            blk.idle_time += 1
        if y.typ == Consts.ssd_blk:
            y.idle_time = len(self.__WCQ)
            self.__SPQ.insert(0, y)

    def _ram_replace(self):
        if self.ram_blk_cnt > conf.ramCapacity:
            for blk in reversed(self.__WCQ):
                if blk.typ == Consts.ram_blk:
                    blk.typ = Consts.hdd_blk
                    break
            self.ram_blk_cnt -= 1

    def update_ssd(self, addr):
        d = 0
        for i in range(len(self.__SPQ)):
            if self.__SPQ[i-d].idle_time > self.qt:
                del self.__SPQ[i-d]
                d += 1
        if d == 0:
            return

        r = 0
        for i in range(len(self.__WCQ)):
            # todo break when pulled blocks are enough
            if self.__WCQ[i].typ != Consts.ssd_blk and self.__WCQ[i].accesses > self.promotion_tsh:
                self.__WCQ[i].typ = Consts.ssd_blk
                self.write_cnt += 1

    def promote(self, addr, length):
        # fixme promotion policy
        if len(self.__cache) == conf.cacheSize:
            free_addr = self.__evict(addr)
        else:
            free_addr = len(self.__cache)

        self.__cache.insert(free_addr, CacheElem(addr))
        self.presence[addr//conf.minReqLen] = True
        # fixme set presence True for all 4096B not 512B

    def __evict(self, addr):
        # LRU
        self.evict_cnt += 1
        evicted = self.__cache.pop()
        self.presence[evicted.addr//conf.minReqLen] = False
        return conf.cacheSize - 1
