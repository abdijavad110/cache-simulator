from conf import conf
from time import sleep, time


class Parser:
    def __init__(self):
        trace = open(conf['traceFilePath']).read().split("\n")
        trace = list(map(lambda q: q.split(conf['traceDil']), trace))
        trace = [e for e in trace if len(e) == conf['indicesCnt']]

        self.requests = list(map(
            lambda q: [float(q[conf['timeInd']])*conf['delayFactor'], q[conf['RWInd']], q[conf['addrInd']], q[conf['sizeInd']]],
            trace))
        self.cnt = len(self.requests)
        self.currentRequest = 0

    def start_sending_requests(self, dest):
        start = time()
        for req in self.requests:
            now = time() - start
            while now < req[0]:
                sleep(10/1000000)
            dest(req[2], req[3])
