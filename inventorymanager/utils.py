from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound
import json
from flask import url_for, request, Response

from inventorymanager.constants import *
from inventorymanager.models import Item, Warehouse, Catalogue, Stock

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)



class WarehouseConverter(BaseConverter):
    
    def to_python(self, value):
        warehouse = Warehouse.query.filter_by(warehouse_id=value).first()
        if warehouse is None:
            raise NotFound
        return warehouse
        
    def to_url(self, value):
        return value.warehouse_id
    

class ItemConverter(BaseConverter):
    
    def to_python(self, value):
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
