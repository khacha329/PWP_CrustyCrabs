"""
This module contains utility functions and classes that are used in the
application. The functions and classes in this module are used to create
responses, convert objects to and from url strings, and to create Mason
objects.
"""

import json

from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound
from flask import url_for, request, Response
from inventorymanager.constants import *
from inventorymanager.models import Item, Location, Warehouse, Catalogue, Stock


# from https://github.com/enkwolf/pwp-course-sensorhub-api-example/tree/master
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title: str, details: str) -> None:
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        :param title: Short title for the error
        :param details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns: str, uri: str) -> None:
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        :param ns: the namespace prefix
        :param uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {"name": uri}

    def add_control(self, ctrl_name: str, href: str, **kwargs) -> None:
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        :param ctrl_name: name of the control (including namespace if any)
        :param href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


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
        return value.warehouse_id


class ItemConverter(BaseConverter):
    """
    Convenience class for converting item id's to item objects and
    vice versa.
    """

    def to_python(self, value: int) -> Item:
        """Converts the item id to a item object.

        :param value: item id
        :raises NotFound: raises NotFound exception if the item is not found
        :return: item object
        """

        item = Item.query.filter_by(name=value).first()
        if item is None:
            raise NotFound
        return item

    def to_url(self, value):
        return value.name
    
class CatalogueConverter(BaseConverter):
    
    def to_python(self, value):
        catalogue = Catalogue.query.filter_by(supplier_name=value).first()
        if catalogue is None:
            raise NotFound
        return catalogue
        
    def to_url(self, value):
        return value.supplier_name
    
class StockConverter(BaseConverter):
    
    def to_python(self, value):
        stock = Stock.query.filter_by(item_id=value).first()
        if stock is None:
            raise NotFound
        return stock
        
    def to_url(self, value):
        return value.supplier_name


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
