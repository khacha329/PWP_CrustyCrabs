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

api.add_resource(ItemCollection, "api/items/")
api.add_resource(ItemItem, "api/items/<item:item>/")
api.add_resource(WarehouseCollection, "api/warehouses/<warehouse:warehouse>/")
api.add_resource(WarehouseManagement, "api/warehouses/<warehouse:warehouse>/locations/<location>/")
# api.add_resource(MeasurementCollection, "/sensors/<sensor:sensor>/measurements/")
# api.add_resource(LocationSensorPairing, "/locations/<location>/<sensor>/")