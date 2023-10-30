"""
API App Management
"""

# stdlib
from dataclasses import asdict, is_dataclass
from datetime import date, datetime

# library
from motor.motor_asyncio import AsyncIOMotorClient
from quart.json.provider import DefaultJSONProvider
from quart_openapi import Pint


class CustomJSONProvider(DefaultJSONProvider):

    @staticmethod
    def default(object_):
        if is_dataclass(object_):
            return asdict(object_)
        if hasattr(object_, "__html__"):
            return str(object_.__html__())
        if isinstance(object_, datetime):
            new_object_ = object_.replace(tzinfo=None)
            return f"{new_object_.isoformat()}Z"
        if isinstance(object_, date):
            return object_.isoformat()
        raise TypeError(f"Object of type {type(object_).__name__} is not JSON serializable")


CORS_HEADERS = ["Authorization", "Content-Type"]


def add_cors(response):
    """Add missing CORS headers

    Fixes CORS bug where headers are not included in OPTIONS
    """
    for key, value in (
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Headers", CORS_HEADERS),
        ("Access-Control-Allow-Methods", list(response.allow)),
    ):
        if key not in response.headers:
            if isinstance(value, list):
                value = ",".join(value)
            response.headers.add(key, value)
    return response


def create_app(name: str, mongo_uri: str = None) -> Pint:
    """Create the core API app. Supply URIs as necessary"""
    Pint.json_provider_class = CustomJSONProvider
    app = Pint(name)

    @app.before_serving
    async def _startup():
        app.mdb = AsyncIOMotorClient(mongo_uri) if mongo_uri else None

    app.after_request(add_cors)
    return app
