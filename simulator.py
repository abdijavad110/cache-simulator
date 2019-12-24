from time import sleep
from storage.manager import Manager
from parser import Parser
import threading
import sys
import tqdm

# fixme shouldn't be in manager?
req_Q = []
Q_lock = threading.Lock()
manager = Manager()
parser = Parser()


def new_request(addr, length, typ):
    Q_lock.acquire()
    req_Q.append([addr, length, typ])
    Q_lock.release()


def poll_q():
    while True:
        while len(req_Q) == 0:
            sleep(2 / 1000000)
        Q_lock.acquire()
        manager.issue_request(req_Q[0][0], req_Q[0][1], req_Q[0][2])
        req_Q.pop(0)
        Q_lock.release()


if __name__ == "__main__":
    parse_trd = threading.Thread(
        target=parser.start_sending_requests,
        args=(new_request,),
        daemon=True
    )
    stg_trd = threading.Thread(
        target=poll_q,
        daemon=True
    )
    parse_trd.start()
    stg_trd.start()
    # monitoring:
    print("\n\n\n\n")
    hits, ram_hits, misses, writes, ttt, tt = 0, 0, 0, 0, 0, 0
    try:
        while parse_trd.is_alive() or len(req_Q) != 0:
            for i in range(4):
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
            sleep(0.5)
            print("trace:\t", parser.currentRequest, "/", parser.cnt, end='   ')
            for _ in range(int(parser.currentRequest / parser.cnt * 100)):
                print(u'\u2588', end='')
            for _ in range(int(parser.currentRequest / parser.cnt * 100), 100):
                print(u'\u2591', end='')
            print('')

            print("requests len:\t", len(req_Q), " WCQ len:", len(manager.cache.WCQ), "/", manager.cache.WCQ_max_size
                  , " SPQ len:", len(manager.cache.SPQ), " QT: %.1f" % manager.cache.qt)
            hits = manager.cache.hit_cnt
            misses = manager.cache.miss_cnt
            writes = manager.cache.write_cnt
            ram_hits = manager.cache.ram_hit_cnt
            tt = writes if writes != 0 else 1
            ttt = hits + ram_hits + misses if hits + ram_hits + misses != 0 else 1

            print("case1.1 %d\tcase1.2 %d\tcase1.3 %d\tcase1.4 %d\tcase2 %d" % (
            manager.cache.case11, manager.cache.case12, manager.cache.case13, manager.cache.case14,
            manager.cache.case2))

            print("cache:: hits:", hits, " ram hits:", ram_hits, " misses:", misses, " writes:", writes,
                  ' hit ratio: %.4f' % ((hits + ram_hits) / ttt * 100), ' WE: %.4f' % (hits / tt), " RE:",
                  manager.cache.ram_write_evict_cnt, ' SE:', manager.cache.ssd_write_evict_cnt)
    except KeyboardInterrupt:
        pass

    print("\ntrace:\t", parser.currentRequest, "/", parser.cnt, "\nfinal result:\nhits: ", hits, "\nram hits:",
          ram_hits, "\nmisses: ", misses, "\nwrites: ", writes,
          "\nhit ratio: ", (hits + ram_hits) / ttt * 100, " WE:", hits / tt)
