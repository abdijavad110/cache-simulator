from json import loads as jsn_ld
from collections import namedtuple


jsn_file = open("configuration.json", 'r').read()
conf = jsn_ld(jsn_file, object_hook=lambda d: namedtuple('configuration', d.keys())(*d.values()))
