"""
MongoDB document cache management
"""

# stdlib
from copy import copy
from datetime import datetime, timedelta, timezone
from typing import Any

# library
from pymongo import UpdateOne
from quart import Quart

# module
from avwx_api_core.util.handler import mongo_handler


# Table expiration in minutes
EXPIRES = {"token": 15, "airsigmet": 15}
DEFAULT_EXPIRES = 2


def _replace_keys(data: dict | None, key: str, by_key: str) -> dict | None:
    """Replaces recursively the keys equal to 'key' by 'by_key'

    Some keys in the report data are '$' and this is not accepted by MongoDB
    """
    if data is None:
        return None
    for d_key, d_val in list(data.items()):
        if d_key == key:
            data[by_key] = data.pop(key)
        if isinstance(d_val, dict):
            data[d_key] = _replace_keys(d_val, key, by_key)
    return data


def _process_data(data: dict) -> dict:
    data = _replace_keys(copy(data), "$", "_$")
    data["timestamp"] = datetime.now(tz=timezone.utc)
    return data


class CacheManager:
    """Handles expiring updates to/from the document cache"""

    _app: Quart
    expires: dict

    def __init__(self, app: Quart, expires: dict = None):
        self._app = app
        self.expires = copy(EXPIRES)
        if expires:
            self.expires.update(expires)

    def has_expired(self, time: datetime, table: str) -> bool:
        """Returns True if a datetime is older than the number of minutes given"""
        if not time:
            return True
        if time.tzinfo is None:
            time = time.replace(tzinfo=timezone.utc)
        minutes = self.expires.get(table, DEFAULT_EXPIRES)
        return datetime.now(tz=timezone.utc) > time + timedelta(minutes=minutes)

    def _include_item(self, item: Any, table: str) -> bool:
        return isinstance(item, dict) and not self.has_expired(
            item.get("timestamp"), table
        )

    async def all(self, table: str, force: bool = False) -> list[dict]:
        """Returns all cached data for a report type

        By default, will only return items where the cache timestamp has not been exceeded
        Can force the cache to return all if force is True
        """
        if self._app.mdb is None:
            return []

        async def search():
            return [i async for i in self._app.mdb.cache[table.lower()].find()]

        data = await mongo_handler(search())
        data = [_replace_keys(i, "_$", "$") for i in data]
        return data if force else [i for i in data if self._include_item(i, table)]

    async def get(self, table: str, key: str, force: bool = False) -> dict | None:
        """Returns the current cached data for a report type and station

        By default, will only return if the cache timestamp has not been exceeded
        Can force the cache to return if force is True
        """
        if self._app.mdb is None:
            return
        search = self._app.mdb.cache[table.lower()].find_one({"_id": key})
        data = await mongo_handler(search)
        data = _replace_keys(data, "_$", "$")
        if force:
            return data
        if self._include_item(data, table):
            return data
        return

    async def update(self, table: str, key: str, data: dict) -> None:
        """Update the cache"""
        if self._app.mdb is None:
            return
        update = self._app.mdb.cache[table.lower()].update_one(
            {"_id": key}, {"$set": _process_data(data)}, upsert=True
        )
        await mongo_handler(update)

    async def update_many(self, table: str, keys: list[str], data: list[dict]) -> None:
        """Update many items in the cache"""
        if self._app.mdb is None or not data:
            return
        updates = [
            UpdateOne({"_id": k}, {"$set": _process_data(d)}, upsert=True)
            for k, d in zip(keys, data)
        ]
        update = self._app.mdb.cache[table.lower()].bulk_write(updates, ordered=False)
        await mongo_handler(update)
