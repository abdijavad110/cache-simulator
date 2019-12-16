from time import sleep
from storage.manager import Manager
from parser import Parser
import threading
import sys

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
            sleep(5 / 1000000)
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
    print("\n\n\n")
    hits, ram_hits, misses, writes, ttt, tt = 0, 0, 0, 0, 0, 0
    try:
        while parse_trd.is_alive() or len(req_Q) != 0:
            for i in range(3):
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
            sleep(0.5)
            print("trace:\t", parser.currentRequest, "/", parser.cnt)
            print("requests len:\t", len(req_Q), " WCQ len:", len(manager.cache.WCQ), " SPQ len:",
                  len(manager.cache.SPQ))
            hits = manager.cache.hit_cnt
            misses = manager.cache.miss_cnt
            writes = manager.cache.write_cnt
            ram_hits = manager.cache.ram_hit_cnt
            tt = writes if writes != 0 else 1
            ttt = hits + ram_hits + misses if hits + ram_hits + misses != 0 else 1
            print("cache:: hits:", hits, " ram hits:", ram_hits, " misses:", misses, " writes:", writes, ", hit ratio:",
                  (hits + ram_hits) / ttt * 100, " WE:", hits / tt)
    except KeyboardInterrupt:
        pass

    print("\ntrace:\t", parser.currentRequest, "/", parser.cnt, "\nfinal result:\nhits: ", hits, "\nram hits:", ram_hits, "\nmisses: ", misses, "\nwrites: ", writes,
          "\nhit ratio: ", (hits + ram_hits) / ttt * 100, " WE:", hits / tt)
