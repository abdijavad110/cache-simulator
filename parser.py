from json import loads as jsn_ld


class Parser:
    def __init__(self):
        jsn_file = open("configuration.json", 'r').read()
        conf = jsn_ld(jsn_file)

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
