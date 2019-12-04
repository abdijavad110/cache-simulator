from json import loads as jsn_ld


jsn_file = open("configuration.json", 'r').read()
conf = jsn_ld(jsn_file)
