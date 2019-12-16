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
        # self.presence = [False]*(conf.maxAddr//conf.minReqLen+1)
        self.miss_cnt = 0
        self.hit_cnt = 0
        self.ram_hit_cnt = 0
        self.write_cnt = 0
        self.manager = manager

        self.WCQ = []
        self.SPQ = []
        self.ram_blk_cnt = 0
        self.ssd_blk_cnt = 0
        self.requests_cnt = 0
        self.thread = None
        # fixme fix qt update
        self.qt = (((conf.ssdCapacity+conf.ramCapacity) // conf.storageCapacity) ** 0.5) * conf.storageCapacity
        self.promotion_tsh = 2
        self.WCQ_max_size = conf.ssdCapacity + conf.ramCapacity

    def issue_request(self, addr, length, typ):
        self.requests_cnt += 1
        if self.requests_cnt == conf.ssdUpdateInterval:
            self.requests_cnt = 0
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self.update_ssd, daemon=True)
                self.thread.start()

        if typ == Consts.write:
            # case 2
            self.miss_cnt += 1
            for i, blk in enumerate(self.WCQ):
                if blk.addr == addr:
                    del self.WCQ[i]
                    return True
            for i, blk in enumerate(self.SPQ):
                if blk.addr == addr:
                    del self.SPQ[i]
                    return True

        else:
            # case 1
            # todo use presence to accelerate search
            # search WCQ
            for i, blk in enumerate(self.WCQ):
                if blk.addr == addr:
                    blk.accesses += 1
                    if blk.typ == Consts.hdd_blk:
                        # case 1.2
                        self.miss_cnt += 1
                        blk.typ = Consts.ram_blk
                        self.ram_blk_cnt += 1
                        del self.WCQ[i]
                        self.WCQ.insert(0, blk)
                        self._ram_replace()
                    else:
                        # case 1.1
                        if blk.typ == Consts.ram_blk:
                            self.ram_hit_cnt += 1
                        else:
                            self.hit_cnt += 1

                        del self.WCQ[i]
                        self.WCQ.insert(0, blk)
                    return True

            # search SPQ
            for i, blk in enumerate(self.SPQ):
                if blk.addr == addr:
                    # case 1.3
                    # write misses
                    self.hit_cnt += 1
                    del self.SPQ[i]
                    self.WCQ.insert(0, blk)
                    self.wcq_evict()
                    return True

            # case 1.4
            self.miss_cnt += 1
            new_blk = CacheElem(addr, Consts.ram_blk)
            self.WCQ.insert(0, new_blk)
            self._ram_replace()
            self.wcq_evict()

    def wcq_evict(self):
        while len(self.WCQ) > self.WCQ_max_size and len(self.WCQ) != 0:
            y = self.WCQ.pop()

            for blk in self.SPQ:
                blk.idle_time += 1
            if y.typ == Consts.ssd_blk:
                y.idle_time = len(self.WCQ)
                self.SPQ.insert(0, y)

    def _ram_replace(self):
        if self.ram_blk_cnt > conf.ramCapacity:
            for blk in reversed(self.WCQ):
                if blk.typ == Consts.ram_blk:
                    blk.typ = Consts.hdd_blk
                    break
            self.ram_blk_cnt -= 1

    def update_ssd(self):
        d = 0
        for i in range(len(self.SPQ)):
            if self.SPQ[i - d].idle_time > self.qt:
                del self.SPQ[i - d]
                self.ssd_blk_cnt -= 1
                d += 1

        candidates_need_total = conf.ssdCapacity - self.ssd_blk_cnt
        candidates_available = len(self.WCQ) - self.ssd_blk_cnt + len(self.SPQ)     # available in RAM or SSD

        found = 0
        for blk in self.WCQ:
            if found == candidates_need_total:
                break

            if blk.typ != Consts.ssd_blk and blk.accesses > self.promotion_tsh:
                found += 1
                self.write_cnt += 1
                self.ssd_blk_cnt += 1
                blk.typ = Consts.ssd_blk

        # fixme now minimum is ram + ssd candidates need
        diff = candidates_available - candidates_need_total + conf.ramCapacity
        if diff < 0:
            self.WCQ_max_size += diff
            return
        evicted = []
        for blk in reversed(self.WCQ):
            if diff == 0:
                break
            if blk.typ == Consts.hdd_blk:
                evicted.append(self.WCQ.index(blk))
        self.WCQ_max_size -= len(evicted)
        for e in evicted:
            self.WCQ.remove(e)

    def promote(self, addr, length):
        # deprecated
        pass

    def __evict(self, addr):
        # deprecated
        pass
