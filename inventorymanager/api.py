"""
This module instantiates the Api object and adds to it all the endpoints for the resources
"""

from flask import Blueprint
from flask_restful import Api

from inventorymanager.resources.item import ItemCollection, ItemItem
from inventorymanager.resources.warehouse import WarehouseCollection, WarehouseItem
from inventorymanager.resources.catalogueEntry import CatalogueCollection, CatalogueItem, ItemList, SupplierItemList
from inventorymanager.resources.Stock import StockCollection, StockItem, ItemLookUp, WarehouseLookUp
from inventorymanager.resources.location import (LocationCollection,
                                                 LocationItem)

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api.add_resource(ItemCollection, "/items/")
api.add_resource(ItemItem, "/items/<item:item>/")

api.add_resource(WarehouseCollection, 
                 "/warehouses/")
api.add_resource(WarehouseItem, 
                 "/warehouses/<int:warehouse>/")

api.add_resource(CatalogueCollection, 
                 "/catalogueEntries/")
api.add_resource(CatalogueItem, 
                 "/catalogueEntries/supplier/<string:supplier>/item/<string:item>/")
api.add_resource(ItemList, 
                 "/catalogueEntries/item/<string:item>/")
api.add_resource(SupplierItemList, 
                 "/catalogueEntries/supplier/<string:supplier>/")

api.add_resource(StockCollection, 
                 "/stocks/")
api.add_resource(StockItem, 
                 "/stocks/<int:warehouse>/item/<string:item>/")
api.add_resource(ItemLookUp, 
                 "/stocks/item/<string:item>/")
api.add_resource(WarehouseLookUp, 
                 "/stocks/warehouse/<int:warehouse>/")

api.add_resource(LocationCollection, "/locations/")
api.add_resource(LocationItem, "/locations/<int:location_id>/")

