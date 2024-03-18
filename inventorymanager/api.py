"""
This module instantiates the Api object and adds to it all the endpoints for the resources
"""

from flask import Blueprint
from flask_restful import Api

from inventorymanager.resources.catalogue import (CatalogueCollection,
                                                  CatalogueItem,
                                                  CatalogueItemCollection,
                                                  CatalogueSupplierCollection)
from inventorymanager.resources.item import ItemCollection, ItemItem
from inventorymanager.resources.location import (LocationCollection,
                                                 LocationItem)
from inventorymanager.resources.stock import (StockCollection, StockItem,
                                              StockItemCollection,
                                              StockWarehouseCollection)
from inventorymanager.resources.warehouse import (WarehouseCollection,
                                                  WarehouseItem)

api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(api_bp)

api.add_resource(ItemCollection, "/items/")
api.add_resource(ItemItem, "/items/<item:item>/")

api.add_resource(WarehouseCollection, "/warehouses/")
api.add_resource(WarehouseItem, "/warehouses/<warehouse:warehouse>/")

api.add_resource(CatalogueCollection, "/catalogue/")
api.add_resource(
    CatalogueItem, "/catalogue/supplier/<string:supplier>/item/<item:item>/"
)
api.add_resource(CatalogueItemCollection, "/catalogue/item/<item:item>/")
api.add_resource(CatalogueSupplierCollection, "/catalogue/supplier/<string:supplier>/")

api.add_resource(StockCollection, "/stocks/")
api.add_resource(StockItem, "/stocks/<warehouse:warehouse>/item/<item:item>/")
api.add_resource(StockItemCollection, "/stocks/item/<item:item>/")
api.add_resource(StockWarehouseCollection, "/stocks/warehouse/<warehouse:warehouse>/")

api.add_resource(LocationCollection, "/locations/")
api.add_resource(LocationItem, "/locations/<location:location>/")
