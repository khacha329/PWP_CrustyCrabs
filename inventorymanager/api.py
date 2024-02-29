"""
This module instantiates the Api object and adds to it all the endpoints for the resources
"""
from flask import Blueprint
from flask_restful import Api

from inventorymanager import create_app
from inventorymanager.resources.item import ItemCollection, ItemItem
from inventorymanager.resources.warehouse import WarehouseCollection, WarehouseManagement
from inventorymanager.resources.catalogueEntry import CatalogueCollection, CatalogueManagement
from inventorymanager.resources.Stock import StockCollection, StockManagement

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api.add_resource(ItemCollection, "/items/")
api.add_resource(ItemItem, "/items/<item:item>/")
api.add_resource(WarehouseCollection, 
                 "/warehouses/")
#find a way to change warehouse location
api.add_resource(WarehouseManagement, 
                 "/warehouses/<warehouse:warehouse>/")
#find a way to request items in which supplier and vise verca
api.add_resource(CatalogueCollection, 
                 "/catalogueEntries/")
api.add_resource(CatalogueManagement, 
                 "/catalogueEntries/<catalogue:catalogue>/")

api.add_resource(StockCollection, 
                 "/stocks/")
api.add_resource(StockManagement, 
                 "/stocks/<stock:stock>/")

# api.add_resource(MeasurementCollection, "/sensors/<sensor:sensor>/measurements/")
# api.add_resource(LocationSensorPairing, "/locations/<location>/<sensor>/")