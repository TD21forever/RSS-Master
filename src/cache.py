import atexit
import logging
import pickle


class CacheKit:
    def __init__(self, file_path):
        self.file_path = file_path
        self.cache = {}
        self.logger = logging.getLogger()
        atexit.register(self.save_cache)

    def load_cache(self):
        self.logger.debug(f"load cache: {self.file_path}")
        try:
            with open(self.file_path, 'rb') as f:
                self.cache = pickle.load(f)
        except FileNotFoundError:
            self.cache = {}

    def save_cache(self):
        self.logger.debug(f"save cache: {self.cache}")
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.cache, f)

    def get(self, key) -> str :
        self.logger.debug(f"get cache: {key}")
        return self.cache.get(key, "")

    def set(self, key, value):
        self.logger.debug(f"set cache: {key} => {value}")
        self.cache[key] = value

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
    def has(self, key):
        return key in self.cache

    def clear(self):
        self.logger.debug(f"clear cache: {self.cache}")
        self.cache = {}