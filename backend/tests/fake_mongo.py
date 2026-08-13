"""Small async Mongo substitute for repository tests.

It intentionally implements only the Motor operations exercised by these tests.
"""

from copy import deepcopy
import re

from bson import ObjectId


def _get(document, dotted_key):
    value = document
    for key in dotted_key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _set(document, dotted_key, value):
    keys = dotted_key.split(".")
    target = document
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    target[keys[-1]] = value


def _matches(document, query):
    for key, expected in query.items():
        if key == "$or":
            if not any(_matches(document, condition) for condition in expected):
                return False
            continue
        value = _get(document, key)
        if isinstance(expected, dict) and "$regex" in expected:
            values = value if isinstance(value, list) else [value]
            flags = re.IGNORECASE if "i" in expected.get("$options", "") else 0
            if not any(item is not None and re.search(expected["$regex"], str(item), flags) for item in values):
                return False
        elif value != expected:
            return False
    return True


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, documents):
        self._documents = documents

    def __aiter__(self):
        self._iterator = iter(self._documents)
        return self

    def sort(self, key, direction=1):
        self._documents.sort(key=lambda item: _get(item, key) or "", reverse=direction < 0)
        return self

    async def __anext__(self):
        try:
            return deepcopy(next(self._iterator))
        except StopIteration:
            raise StopAsyncIteration from None


class FakeCollection:
    def __init__(self):
        self.documents = []
        self.indexes = []

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))

    async def insert_one(self, document):
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return FakeInsertResult(stored["_id"])

    async def find_one(self, query):
        return next((deepcopy(item) for item in self.documents if _matches(item, query)), None)

    def find(self, query):
        return FakeCursor([item for item in self.documents if _matches(item, query)])

    async def update_one(self, query, update, upsert=False):
        document = next((item for item in self.documents if _matches(item, query)), None)
        if document is None and upsert:
            document = dict(query)
            self.documents.append(document)
        if document is not None:
            for key, value in update["$set"].items():
                _set(document, key, deepcopy(value))

    async def find_one_and_update(self, query, update, return_document=True):
        document = next((item for item in self.documents if _matches(item, query)), None)
        if document is None:
            return None
        for key, value in update["$set"].items():
            _set(document, key, deepcopy(value))
        return deepcopy(document)

    async def count_documents(self, query):
        return sum(_matches(item, query) for item in self.documents)


class FakeDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, FakeCollection())
