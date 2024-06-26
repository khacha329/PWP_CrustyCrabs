"""
This module contains the resources for the stock endpoints. 
"""

import json
import os

from flasgger import swag_from
from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db
from inventorymanager.builder import InventoryManagerBuilder
from inventorymanager.constants import (DOC_FOLDER, LINK_RELATIONS_URL, MASON,
                                        NAMESPACE, STOCK_PROFILE)
from inventorymanager.models import Item, Stock, Warehouse
from inventorymanager.utils import create_error_response


class StockCollection(Resource):
    """
    Resource for the collection of stocks, provides GET and POST methods
    /stocks/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/collection/get.yml")
    def get(self):
        """Returns a list of all stocks in the database

        :return: Response
        """

        body = InventoryManagerBuilder(items=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.stockcollection"))

        for stock in Stock.query.all():
            item = InventoryManagerBuilder(stock.serialize())
            item.add_control(
                "self",
                url_for("api.stockitem", warehouse=stock.warehouse, item=stock.item),
            )
            item.add_control("profile", STOCK_PROFILE)
            body["items"].append(item)

        body.add_control_post(
            "add-stock",
            "Add new stock",
            url_for("api.stockcollection"),
            Stock.get_schema(),
        )
        body.add_control_all_items()
        body.add_control_all_warehouses()

        return Response(json.dumps(body), 200)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/collection/post.yml")
    def post(self):
        """Adds a new stock to the database

        :return: Response
        """
        try:
            validate(request.json, Stock.get_schema())
            item_id = request.json["item_id"]
            item_entry = Item.query.filter_by(item_id=item_id).first()
            if not item_entry:
                return create_error_response(404, "Item doesn't exist")
            warehouse_id = request.json["warehouse_id"]
            warehouse_entry = Warehouse.query.filter_by(
                warehouse_id=warehouse_id
            ).first()
            if not warehouse_entry:
                return create_error_response(404, "Warehouse doesn't exist")
            stock = Stock()
            stock.deserialize(request.json)

            db.session.add(stock)
            db.session.commit()

        except ValidationError as e:
            db.session.rollback()
            return abort(400, e.message)

        except IntegrityError:
            db.session.rollback()
            return abort(409, "stock already exists")
        return Response(
            status=201,
            headers={
                "Location": url_for(
                    "api.stockitem", warehouse=stock.warehouse, item=stock.item
                )
            },
        )


class StockItem(Resource):
    """
    Resource for a single stock, provides GET, PUT and DELETE methods
    /stocks/<warehouse:warehouse>/item/<item:item>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/item/get.yml")
    def get(self, warehouse: Warehouse, item: Item):
        """returns a single stock in the database

        :param warehouse: warehouse id of the stock to return
        :param item: item name of the stock to return
        :return: Response
        """

        stock = Stock.query.filter_by(warehouse=warehouse, item=item).first()

        self_url = url_for("api.stockitem", warehouse=warehouse, item=item)
        body = InventoryManagerBuilder(stock.serialize())

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", STOCK_PROFILE)
        body.add_control("collection", url_for("api.stockcollection"))
        body.add_control_put("Modify this stock", self_url, Stock.get_schema())
        body.add_control_delete("Delete this stock", self_url)
        body.add_control_get_warehouse(warehouse)
        body.add_control_get_item(item)
        body.add_control_all_stock_item(item)
        body.add_control_all_stock_warehouse(warehouse)

        return Response(json.dumps(body), 200, mimetype=MASON)

        # return Response(json.dumps(stock_json), 200)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/item/put.yml")
    def put(self, warehouse: Warehouse, item: Item):
        """Updates a stock in the database

        :param warehouse: warehouse id of the stock to update
        :param item: item name of the stock to update
        :return: Response
        """
        item_entry = Item.query.filter_by(item_id=request.json["item_id"]).first()
        if not item_entry:
            return create_error_response(404, "Item doesn't exist")
        warehouse_entry = Warehouse.query.filter_by(
            warehouse_id=request.json["warehouse_id"]
        ).first()
        if not warehouse_entry:
            return create_error_response(404, "Warehouse doesn't exist")
        try:
            validate(request.json, Stock.get_schema())
            stock_entry = Stock.query.filter_by(
                item_id=item.item_id, warehouse_id=warehouse.warehouse_id
            ).first()
            stock_entry.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            db.session.rollback()
            return create_error_response(400, "Invalid JSON document", str(e))

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                "Already exists",
                "stock with item '{}' in warehouse with id '{}'already exists.".format(
                    request.json["item_id"], request.json["warehouse_id"]
                ),
            )
        except AttributeError:
            return create_error_response(404, "Stock not found")

        return Response(status=204)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/item/delete.yml")
    def delete(self, warehouse: Warehouse, item: Item):
        """Deletes a stock in the database

        :param warehouse: warehouse id of the stock to delete
        :param item: item name of the stock to delete
        :return: Response
        """

        stock_entry = Stock.query.filter_by(item=item, warehouse=warehouse).first()
        if not stock_entry:
            return create_error_response(404, "Stock entry not found ")
        db.session.delete(stock_entry)
        db.session.commit()

        return Response(status=204)


class StockItemCollection(Resource):
    """
    Resource for the collection of stocks filtered by item, provides GET method
    /stocks/item/<item:item>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/itemcollection/get.yml")
    def get(self, item: Item):
        """Returns a list of stocks in the database filtered by item name

        :param item: item name to filter stocks with
        :return: Response
        """

        body = InventoryManagerBuilder(items=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.stockitemcollection", item=item))
        for stock in Stock.query.filter_by(item=item):
            item = InventoryManagerBuilder(stock.serialize())
            item.add_control(
                "self",
                url_for("api.stockitem", warehouse=stock.warehouse, item=stock.item),
            )
            item.add_control("profile", STOCK_PROFILE)
            body["items"].append(item)

        body.add_control_all_stock()

        return Response(json.dumps(body), 200)


class StockWarehouseCollection(Resource):
    """
    Resource for the collection of stocks filtered by name, provides GET method
    /stocks/warehouse/<warehouse:warehouse>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}stock/warehousecollection/get.yml")
    def get(self, warehouse: Warehouse):
        """Returns a list of stocks in the database filtered by warehouse id

        :param warehouse: warehouse id to filter stocks with
        :return: Response
        """

        body = InventoryManagerBuilder(items=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control(
            "self", url_for("api.stockwarehousecollection", warehouse=warehouse)
        )
        for stock in Stock.query.filter_by(warehouse=warehouse):
            item = InventoryManagerBuilder(stock.serialize())
            item.add_control(
                "self",
                url_for("api.stockitem", warehouse=stock.warehouse, item=stock.item),
            )
            item.add_control("profile", STOCK_PROFILE)
            body["items"].append(item)

        body.add_control_all_stock()

        return Response(json.dumps(body), 200)
