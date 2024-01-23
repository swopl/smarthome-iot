from collections import defaultdict
from exterior_interacting.publisher.publisher import Publisher


class PublisherDict(defaultdict):
    def __missing__(self, key):
        ret = self[key] = Publisher(key)
        return ret
