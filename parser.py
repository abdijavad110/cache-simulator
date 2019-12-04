from simulator import conf


class Parser:
    def __init__(self):
        trace = open(conf['traceFilePath']).read().split("\n")
        trace = list(map(lambda q: q.split(), trace))
        trace = [e for e in trace if len(e) == conf['indicesCnt']]

        self.requests = list(map(
            lambda q: [q[conf['timeInd']], q[conf['RWInd']], q[conf['addrInd']], q[conf['sizeInd']]],
            trace))
        self.cnt = len(self.requests)
        self.currentRequest = 0

    def start_sending_requests(self, destination):
        pass
