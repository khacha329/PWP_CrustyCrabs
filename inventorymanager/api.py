"""
This module instantiates the Api object and adds to it all the endpoints for the resources
"""

from flask import Blueprint
from flask_restful import Api

from inventorymanager.resources.item import ItemCollection, ItemItem
from inventorymanager.resources.location import LocationCollection, LocationItem

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api.add_resource(ItemCollection, "/items/")
api.add_resource(ItemItem, "/items/<item:item>/")
api.add_resource(LocationCollection, "/locations/locations/")
api.add_resource(LocationItem, '/api/locations/<int:location_id>')
# api.add_resource(SensorItem, "/sensors/<sensor:sensor>/")
# api.add_resource(LocationItem, "/locations/<location>/")
# api.add_resource(MeasurementCollection, "/sensors/<sensor:sensor>/measurements/")
# api.add_resource(LocationSensorPairing, "/locations/<location>/<sensor>/")
