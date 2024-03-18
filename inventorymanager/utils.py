"""
This module contains utility functions and classes that are used in the
application. The functions and classes in this module are used to create
responses, convert objects to and from url strings, and to create Mason
objects.
"""

import json

from flask import Response, request
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from inventorymanager.builder import MasonBuilder
from inventorymanager.constants import ERROR_PROFILE, MASON
from inventorymanager.models import Item, Location, Warehouse


# from https://github.com/enkwolf/pwp-course-sensorhub-api-example/tree/master
def create_error_response(
    status_code: int, title: str, message: str = None
) -> Response:
    """Creates an error response with the given status code, title and message.

    :param status_code: HTTP status code
    :param title: Short title for the error
    :param message: Long version of the error, defaults to None
    :return: Response that contains everything
    """

    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


class WarehouseConverter(BaseConverter):
    """
    Convenience class for converting warehouse id's to warehouse objects and
    vice versa.
    """

    def to_python(self, value: int) -> Warehouse:
        """Converts the warehouse id to a warehouse object.

        :param value: Warehouse id
        :raises NotFound: raises NotFound exception if the warehouse is not found
        :return: Warehouse object
        """
        warehouse = Warehouse.query.filter_by(warehouse_id=value).first()
        if warehouse is None:
            raise NotFound
        return warehouse

    def to_url(self, value: Warehouse) -> str:
        """Converts Warehouse object to a string used in url.

        :param value: Warehouse object
        :return: Warehouse id
        """
        return str(value.warehouse_id)


class ItemConverter(BaseConverter):
    """
    Convenience class for converting item id's to item objects and
    vice versa.
    """

    def to_python(self, value: int) -> Item:
        """Converts the item id to an item object.

        :param value: item id
        :raises NotFound: raises NotFound exception if the item is not found
        :return: item object
        """

        item = Item.query.filter_by(name=value).first()
        if item is None:
            raise NotFound
        return item

    def to_url(self, value):
        """
        Converts an item object into a string value used in the URI.

        :param value: item name
        :return: The item name.
        """
        return value.name


class LocationConverter(BaseConverter):
    """
    URLConverter for a location resource.
    to_python takes a location_id and returns a Location object.
    to_url takes a Location object and returns the corresponding location_id
    """

    def to_python(self, value):
        """
        Converts a location_id in a location object with information from database
        :parameter value: str representing the location id
        raises a NotFound error if it is impossible to convert the string in an int or if the
        location is not found.
        :return: a Location object corresponding to the location_id.
        """
        try:
            int_id = int(value)
        except ValueError:
            raise NotFound(description="Location ID must be an integer.")

        location = Location.query.filter_by(location_id=int_id).first()
        if location is None:
            raise NotFound(description=f"Location with ID {int_id} not found.")
        return location

    def to_url(self, value: Location) -> str:
        """
        Converts a Location object into a string value used in the URI.

        :param value: Location Object.
        :return: The location_id as a string.
        """
        return str(value.location_id)
