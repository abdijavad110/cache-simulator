import threading


class Storage:
    def __init__(self):
        self.__cache_miss_queue = []
        self.__cache_lock = threading.Lock()
        self.__storage_queue = []
        self.__storage_lock = threading.Lock()
