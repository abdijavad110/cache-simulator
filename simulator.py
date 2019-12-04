from json import loads as jsn_ld
from time import sleep
from storage.manager import Manager
from parser import Parser
import threading


jsn_file = open("configuration.json", 'r').read()
conf = jsn_ld(jsn_file)

# fixme shouldn't be in manager?
req_Q = []
Q_lock = threading.Lock()
manager = Manager()
parser = Parser()


def new_request(addr, length):
    Q_lock.acquire()
    req_Q.append([addr, length])
    Q_lock.release()


def poll_q():
    while True:
        if len(req_Q) == 0:
            sleep(5/1000000)
        manager.issue_request(req_Q[0], req_Q[1])


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
    while parse_trd.is_alive():
        pass
