import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from inventorymanager.models import Stock, Item, Warehouse
from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response


class StockCollection(Resource):
    

    def get(self):
        body = []
        for stock in Stock.query.all():
            stock_json = stock.serialize()
            stock_json["uri"] = url_for("api.stockcollection", stock=stock)
            body.append(stock_json)

        return Response(json.dumps(body), 200)
    



class StockManagement(Resource):
    
    def get(self, warehouse, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        if not item:
            return create_error_response(400, "Item doesn't exist")

    # Retrieve the stock entry based on warehouse ID and item ID
        stock_entry = Stock.query.filter_by(warehouse=warehouse, item_id=item.item_id).first()
        if not stock_entry:
            return create_error_response(400, "Stock entry not found ")
        stock_json = stock_entry.serialize()
        stock_json["uri"] = url_for("api.stockcollection", stock=stock_entry)
        return Response(json.dumps(stock_entry), 200)
    
    def post(self, warehouse, item):
        item_name = item.replace('_', ' ')
        item_entry = Item.query.filter_by(name=item_name).first()
        if not item_entry:
            return create_error_response(400, "Item doesn't exist")
        warehouse_entry = Warehouse.query.get(warehouse.warehouse_id)
        try:
            validate(request.json, Stock.get_schema())
            stock = Stock(item_id = item_entry.item_id, warehouse_id = warehouse_entry.warehouse_id)
            stock.deserialize(request.json)
        
            db.session.add(stock)
            db.session.commit()

        except SQLAlchemyError as e:
            error = str(e.__dict__['orig'])
            return abort(400, error)     
        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "stock already exists")
        #if api fails after this line, resource will be added to db anyway
        return Response(status=201, headers={
            "Location": url_for("api.stockmanagement", warehouse=warehouse_entry, item=item_entry.name)
        })
    def put(self, warehouse: int, item: str):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        if not item:
            return create_error_response(400, "Item doesn't exist")

        # Retrieve the stock entry based on warehouse ID and item ID
        stock_entry = Stock.query.filter_by( item_id=item.item_id, warehouse=warehouse).first()
        try:
            validate(request.json, Stock.get_schema())
            stock_entry.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "stock with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    def delete(self, warehouse: int, item: str):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        if not item:
            return create_error_response(400, "Item doesn't exist")

        # Retrieve the stock entry based on warehouse ID and item ID
        stock_entry = Stock.query.filter_by( item_id=item.item_id, warehouse=warehouse).first()
        db.session.delete(stock_entry)
        db.session.commit()

        return Response(status=204) 
    
class ItemLookUp(Resource):
    def get(self, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()

        if not item:
            return create_error_response(400, "Item doesn't exist")
        body = []
        for stock_entry in Stock.query.filter_by(item_id=item.item_id).all():
            stock_json = stock_entry.serialize()
            stock_json["uri"] = url_for("api.itemlookup", item=item.name)
            body.append(stock_json)
        return Response(json.dumps(body), 200)
    
class WarehouseLookUp(Resource):
    def get(self, warehouse):
        body = []
        for stock_entry in Stock.query.filter_by(warehouse=warehouse.warehouse_id).all():
            stock_json = stock_entry.serialize()
            stock_json["uri"] = url_for("api.warehouselookup", warehouse=warehouse.warehouse_id)
            body.append(stock_json)
        return Response(json.dumps(body), 200)