import json

from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.models import Item, Stock, Warehouse
from inventorymanager.utils import create_error_response


class StockCollection(Resource):
    """
    Resource for the collection of stocks, provides GET and POST methods
    /stocks/
    """

    def get(self):
        """Returns a list of all stocks in the database

        :return: Response
        """
        body = []
        for stock in Stock.query.all():
            stock_json = stock.serialize()
            stock_json["uri"] = url_for(
                "api.stockitem", warehouse=stock.warehouse, item=stock.item
            )
            body.append(stock_json)

        return Response(json.dumps(body), 200)

    def post(self):
        """Adds a new stock to the database

        :return: Response
        """
        try:
            validate(request.json, Stock.get_schema())
            item_name = request.json["item_name"]
            item_entry = Item.query.filter_by(name=item_name).first()
            if not item_entry:
                return create_error_response(404, "Item doesn't exist")
            warehouse_id = request.json["warehouse_id"]
            warehouse_entry = Warehouse.query.filter_by(
                warehouse_id=warehouse_id
            ).first()
            stock = Stock(item=item_entry, warehouse=warehouse_entry)
            stock.deserialize(request.json)

            db.session.add(stock)
            db.session.commit()

        except SQLAlchemyError as e:
            error = str(e.__dict__["orig"])
            return abort(400, error)
        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "stock already exists")
        # if api fails after this line, resource will be added to db anyway
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

    def get(self, warehouse: Warehouse, item: Item):
        """returns a single stock in the database

        :param warehouse: warehouse id of the stock to return
        :param item: item name of the stock to return
        :return: Response
        """

        stock_entry = Stock.query.filter_by(warehouse=warehouse, item=item).first()
        if not stock_entry:
            return create_error_response(404, "Stock entry not found ")
        stock_json = stock_entry.serialize()
        stock_json["uri"] = url_for("api.stockitem", warehouse=warehouse, item=item)
        return Response(json.dumps(stock_json), 200)

    def put(self, warehouse: Warehouse, item: Item):
        """Updates a stock in the database

        :param warehouse: warehouse id of the stock to update
        :param item: item name of the stock to update
        :return: Response
        """

        stock_entry = Stock.query.filter_by(item=item, warehouse=warehouse).first()
        if not stock_entry:
            return create_error_response(404, "Stock entry not found ")
        try:
            validate(request.json, Stock.get_schema())
            stock_entry.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        except IntegrityError:
            return create_error_response(
                409,
                "Already exists",
                "stock with name '{}' already exists.".format(request.json["name"]),
            )

        return Response(status=204)

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

    def get(self, item: Item):
        """Returns a list of stocks in the database filtered by item name

        :param item: item name to filter stocks with
        :return: Response
        """

        body = []
        for stock_entry in Stock.query.filter_by(item=item).all():
            stock_json = stock_entry.serialize()
            stock_json["uri"] = url_for(
                "api.stockitem", warehouse=stock_entry.warehouse, item=item
            )
            body.append(stock_json)
        return Response(json.dumps(body), 200)


class StockWarehouseCollection(Resource):
    """
    Resource for the collection of stocks filtered by name, provides GET method
    /stocks/warehouse/<warehouse:warehouse>/
    """

    def get(self, warehouse: Warehouse):
        """Returns a list of stocks in the database filtered by warehouse id

        :param warehouse: warehouse id to filter stocks with
        :return: Response
        """
        body = []
        for stock in Stock.query.filter_by(warehouse=warehouse).all():
            stock_json = stock.serialize()
            stock_json["uri"] = url_for(
                "api.stockitem", warehouse=stock.warehouse, item=stock.item
            )
            body.append(stock_json)
        return Response(json.dumps(body), 200)
