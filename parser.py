from conf import conf
from time import sleep, time


class Parser:
    def __init__(self, file_path=conf.traceFilePath):
        trace = open(file_path).read().split("\n")
        trace = list(map(lambda q: q.split(conf.traceDil), trace))
        trace = [e for e in trace if len(e) == conf.indicesCnt]

        self.requests = list(map(
            lambda q: [(float(q[conf.timeInd])-float(trace[0][conf.timeInd]))*conf.delayFactor,
                       q[conf.RWInd], int(q[conf.addrInd]), int(q[conf.sizeInd])],
            trace))
        self.cnt = len(self.requests)
        self.currentRequest = 0

    def start_sending_requests(self, dest):
        start = time()
        for req in self.requests:
            while time() - start < req[0]:
                sleep(2/1000000)
            dest(req[2], req[3], req[1])
            self.currentRequest += 1
