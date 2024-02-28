"""
This module instantiates the Api object and adds to it all the endpoints for the resources
"""
from flask import Blueprint
from flask_restful import Api

from inventorymanager import create_app
from inventorymanager.resources.item import ItemCollection, ItemItem
from inventorymanager.resources.warehouse import WarehouseCollection, WarehouseManagement

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api.add_resource(ItemCollection, "/items/")
api.add_resource(ItemItem, "/items/<item:item>/")
api.add_resource(WarehouseCollection, 
                 "/warehouses/")
api.add_resource(WarehouseManagement, 
                 "/warehouses/<warehouse:warehouse>/")
# api.add_resource(MeasurementCollection, "/sensors/<sensor:sensor>/measurements/")
# api.add_resource(LocationSensorPairing, "/locations/<location>/<sensor>/")