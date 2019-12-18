import threading
from conf import conf
from storage.storageManager import Storage


class CacheElem:
    def __init__(self, addr, typ, idle_time=0):
        self.addr = addr
        self.typ = typ
        self.idle_time = idle_time
        self.writes = 0
        self.reads = 0

    @property
    def accesses(self):
        return self.reads + self.writes


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
        self.WCQ_lck = threading.Lock()
        self.SPQ = []
        self.SPQ_lck = threading.Lock()
        self.ram_blk_cnt = 0
        self.ssd_blk_cnt = 0
        self.requests_cnt = 0
        self.ram_write_evict_cnt = 0
        self.ssd_write_evict_cnt = 0
        self.thread = None
        # fixme fix qt update
        self.qt = (((conf.ssdCapacity + conf.ramCapacity) / conf.storageCapacity) ** 0.5) * conf.storageCapacity
        self.promotion_tsh = conf.promotionTsh
        self.WCQ_max_size = conf.ssdCapacity + conf.ramCapacity
        self.WCQ_max_size = 1000

        self.temp = 0
        self.case11 = 0
        self.case12 = 0
        self.case13 = 0
        self.case14 = 0
        self.case2 = 0

    def issue_request(self, addr, length, typ):

        # self.temp+=1
        # if self.temp > 5030:
        #     print("here")

        self.requests_cnt += 1
        if self.requests_cnt == conf.ssdUpdateInterval:
            self.requests_cnt = 0
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self.update_ssd, daemon=True)
                self.thread.start()

        if typ == Consts.write:
            # case 2
            self.case2 += 1
            self.WCQ_lck.acquire()

            try:
                idx = [blk.addr for blk in self.WCQ].index(addr)
                blk = self.WCQ[idx]

                if blk.typ != Consts.ssd_blk:
                    if blk.typ == Consts.ram_blk:
                        self.ram_write_evict_cnt += 1
                        self.ram_blk_cnt -= 1
                        self.miss_cnt += 1
                    del self.WCQ[idx]
                else:
                    if blk.accesses > 5 and blk.writes / blk.reads < 0.25:
                        blk.writes += 1
                        self.hit_cnt += 1
                    else:
                        self.ssd_write_evict_cnt += 1
                        self.miss_cnt += 1
                        del self.WCQ[idx]

                self.WCQ_lck.release()
                return True
            except ValueError:
                self.WCQ_lck.release()

            self.SPQ_lck.acquire()
            for i, blk in enumerate(self.SPQ):
                if blk.addr == addr:
                    if blk.accesses > 5 and blk.writes / blk.reads < 0.25:
                        blk.writes += 1
                        self.hit_cnt += 1
                    else:
                        del self.SPQ[i]
                        self.ssd_write_evict_cnt += 1
                        self.SPQ_lck.release()
                    return True
            self.SPQ_lck.release()

        else:
            # case 1
            # todo use presence to accelerate search
            # search WCQ
            self.WCQ_lck.acquire()
            try:
                idx = [blk.addr for blk in self.WCQ].index(addr)
                blk = self.WCQ[idx]
                blk.reads += 1
                if blk.typ == Consts.hdd_blk:
                    # case 1.2
                    self.case12 += 1
                    self.miss_cnt += 1
                    blk.typ = Consts.ram_blk
                    self.ram_blk_cnt += 1
                    del self.WCQ[idx]
                    self.WCQ.insert(0, blk)
                    self.WCQ_lck.release()
                    self._ram_replace()
                else:
                    # case 1.1
                    self.case11 += 1
                    if blk.typ == Consts.ram_blk:
                        self.ram_hit_cnt += 1
                    else:
                        self.hit_cnt += 1

                    del self.WCQ[idx]
                    self.WCQ.insert(0, blk)
                    self.WCQ_lck.release()
                return True
            except ValueError:
                self.WCQ_lck.release()

            # search SPQ
            self.SPQ_lck.acquire()
            for i, blk in enumerate(self.SPQ):
                if blk.addr == addr:
                    # case 1.3
                    self.case13 += 1
                    blk.reads += 1
                    self.hit_cnt += 1
                    del self.SPQ[i]
                    self.WCQ.insert(0, blk)
                    self.SPQ_lck.release()
                    self.wcq_evict()
                    return True
            self.SPQ_lck.release()

            # case 1.4
            self.case14 += 1
            self.miss_cnt += 1
            new_blk = CacheElem(addr, Consts.ram_blk)
            new_blk.reads += 1
            self.ram_blk_cnt += 1
            self.WCQ_lck.acquire()
            self.WCQ.insert(0, new_blk)
            self.WCQ_lck.release()
            self._ram_replace()
            self.wcq_evict()

    def wcq_evict(self):
        self.WCQ_lck.acquire()
        while len(self.WCQ) > self.WCQ_max_size and len(self.WCQ) != 0:
            y = self.WCQ.pop()

            self.SPQ_lck.acquire()
            for blk in self.SPQ:
                blk.idle_time += 1
            if y.typ == Consts.ssd_blk:
                y.idle_time = len(self.WCQ)
                self.SPQ.insert(0, y)
            self.SPQ_lck.release()
        self.WCQ_lck.release()

    def _ram_replace(self):
        self.WCQ_lck.acquire()
        for blk in reversed(self.WCQ):
            if self.ram_blk_cnt <= conf.ramCapacity:
                break
            if blk.typ == Consts.ram_blk:
                blk.typ = Consts.hdd_blk
                self.ram_blk_cnt -= 1
                break
        self.WCQ_lck.release()

    def update_ssd(self):

        # ff = open('log', 'a')

        self.SPQ_lck.acquire()
        self.WCQ_lck.acquire()
        d = 0
        for i in range(len(self.SPQ)):
            if self.SPQ[i - d].idle_time > self.qt:
                del self.SPQ[i - d]
                self.ssd_blk_cnt -= 1
                d += 1

        candidates_need_total = conf.ssdCapacity - self.ssd_blk_cnt
        candidates_capacity = self.WCQ_max_size - self.ssd_blk_cnt + len(self.SPQ)  # available in RAM or SSD

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

        # ff.write("avai %d need %d ram %d rbc %d/%d sbc %d ==> " % (
        #     candidates_capacity, candidates_need_total, conf.ramCapacity, self.ram_blk_cnt, conf.ramCapacity,
        #     self.ssd_blk_cnt))

        diff = candidates_capacity - candidates_need_total
        if diff < 0:
            # fixme make WCQ size dynamic
            self.WCQ_max_size -= diff

            # ff.write("I %d\n" % diff)

            self.WCQ_lck.release()
            self.SPQ_lck.release()
            return
        evicted = []
        for blk in reversed(self.WCQ):
            if diff == 0:
                break
            if blk.typ != Consts.ssd_blk:
                diff -= 1
                evicted.append(blk)

        # ff.write("D %d\n" % len(evicted))

        # fixme make WCQ size dynamic
        self.WCQ_max_size -= len(evicted)
        for e in evicted:
            if len(self.WCQ) <= self.WCQ_max_size:
                break
            self.WCQ.remove(e)

        self.WCQ_lck.release()
        self.SPQ_lck.release()

        # ff.close()

    def promote(self, addr, length):
        # deprecated
        pass

    def __evict(self, addr):
        # deprecated
        pass
