"""
Entity schema validation
"""

# pylint: disable=invalid-name

# stdlib
import re
from typing import Callable

# library
import rollbar
from voluptuous import All, Coerce, In, Invalid, Length, Range, Required

# module
from avwx import Station
from avwx.exceptions import BadStation
from avwx.flight_path import to_coordinates
from avwx.structs import Coord


FORMATS = ("json", "xml", "yaml")
BLOCKED_COUNTRIES = {"RU": "Russia", "BY": "Belarus"}


HELP_TEXT = {
    "format": f"Accepted response formats {FORMATS}",
    "remove": "Remove unused keys. Ex: repr,spoken",
    "filter": "Only include these keys. Ex: wind_speed,value,raw",
}


def station_for(code: str) -> Station:
    """Returns the Station object for a code passing availability checks"""
    try:
        station = Station.from_code(code)
        if station.country in BLOCKED_COUNTRIES:
            blocked = ", ".join(BLOCKED_COUNTRIES.values())
            raise Invalid(
                f"AVWX is currently blocking requests for airports in: {blocked}"
            )
        return station
    except BadStation as exc:
        raise Invalid(f"{code} is not a valid ICAO, IATA, or GPS code") from exc


Latitude = All(Coerce(float), Range(-90, 90))
Longitude = All(Coerce(float), Range(-180, 180))


def Split(values: str) -> list[str]:
    """Splits a comma-separated string"""
    return values.split(",") if values else []


def SplitIn(values: tuple[str]) -> Callable:
    """Returns a validator to check for given values in a comma-separated string"""

    def validator(csv: str) -> str:
        if not csv:
            return []
        split = csv.split(",")
        for val in split:
            if val not in values:
                raise Invalid(f"'{val}' could not be found in {values}")
        return split

    return validator


def MatchesRE(name: str, pattern: str) -> Callable:
    """Returns a validation function that checks if a string matches a regex pattern"""
    expr = re.compile(pattern)

    def mre(txt: str) -> str:
        """Raises an exception if a string doesn't match the required format"""
        if expr.fullmatch(txt) is None:
            raise Invalid(f"'{txt}' is not a valid {name}")
        return txt

    return mre


Token = All(
    str,
    Length(min=10),
    lambda x: x.strip().split()[-1],
    MatchesRE("token", r"[A-Za-z0-9\-\_]+"),
)


def FlightRoute(values: str) -> list[Coord]:
    """Validates a semicolon-separated string of coordinates or navigation markers"""
    path_str = values
    values = values.upper().split(";")
    if not values:
        raise Invalid("Could not find any route components in the request")
    for i, val in enumerate(values):
        if "," in val:
            loc = val.split(",")
            values[i] = Coord(lat=Latitude(loc[0]), lon=Longitude(loc[1]), repr=val)
    try:
        return to_coordinates(values)
    except BadStation as exc:
        rollbar.report_exc_info(exc, extra_data={"path": path_str})
        raise Invalid(str(exc)) from exc


required = {
    Required("format", default="json"): In(FORMATS),
    Required("remove", default=""): Split,
    Required("filter", default=""): Split,
}
