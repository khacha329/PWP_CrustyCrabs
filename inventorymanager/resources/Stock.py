import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from inventorymanager.models import Stock, Item, Warehouse, require_warehouse_key
from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response


class StockCollection(Resource):
    

    def get(self):
        body = []
        for stock in Stock.query.all():
            item = Item.query.filter_by(item_id=stock.item_id).first()
            stock_json = stock.serialize()
            stock_json["uri"] = url_for("api.stockitem", warehouse=stock.warehouse_id, item=item.name)
            body.append(stock_json)

        return Response(json.dumps(body), 200)
    
    @require_warehouse_key
    def post(self):

        try:
            validate(request.json, Stock.get_schema())
            item_name = request.json['item_name']
            item_entry = Item.query.filter_by(name=item_name).first()
            if not item_entry:
                return create_error_response(404, "Item doesn't exist")
            warehouse_id = request.json['warehouse_id']
            stock = Stock(item_id = item_entry.item_id, warehouse_id = warehouse_id)
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
            "Location": url_for("api.stockitem", warehouse=warehouse_id, item=item_entry.name)
        })
    
class StockItem(Resource):
    
    def get(self, warehouse, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        if not item:
            return create_error_response(404, "Item doesn't exist")

    # Retrieve the stock entry based on warehouse ID and item ID
        stock_entry = Stock.query.filter_by(warehouse=warehouse, item_id=item.item_id).first()
        if not stock_entry:
            return create_error_response(404, "Stock entry not found ")
        stock_json = stock_entry.serialize()
        stock_json["uri"] = url_for("api.stockitem", warehouse=warehouse.warehouse_id, item=item_name)
        return Response(json.dumps(stock_json), 200)
    
    @require_warehouse_key
    def put(self, warehouse: int, item: str):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        if not item:
            return create_error_response(404, "Item doesn't exist")

        # Retrieve the stock entry based on warehouse ID and item ID
        stock_entry = Stock.query.filter_by( item_id=item.item_id, warehouse=warehouse).first()
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
                409, "Already exists",
                "stock with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    @require_warehouse_key
    def delete(self, warehouse: int, item: str):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        if not item:
            return create_error_response(404, "Item doesn't exist")

        # Retrieve the stock entry based on warehouse ID and item ID
        stock_entry = Stock.query.filter_by( item_id=item.item_id, warehouse=warehouse).first()
        if not stock_entry:
            return create_error_response(404, "Stock entry not found ")
        db.session.delete(stock_entry)
        db.session.commit()

        return Response(status=204) 
    
class ItemLookUp(Resource):
    def get(self, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()

        if not item:
            return create_error_response(404, "Item doesn't exist")
        body = []
        for stock_entry in Stock.query.filter_by(item_id=item.item_id).all():
            stock_json = stock_entry.serialize()
            stock_json["uri"] = url_for("api.stockitem", warehouse=stock_entry.warehouse_id, item=item.name)
            body.append(stock_json)
        return Response(json.dumps(body), 200)
    
class WarehouseLookUp(Resource):
    def get(self, warehouse:int):
        warehouse_entry = Warehouse.query.filter_by(warehouse_id=warehouse.warehouse_id).first()
        if not warehouse_entry:
            return create_error_response(404, "Warehouse entry not found ")
        body = []
        for stock_entry in Stock.query.filter_by(warehouse_id=warehouse_entry.warehouse_id).all():
            item = Item.query.filter_by(item_id=stock_entry.item_id).first()
            stock_json = stock_entry.serialize()
            stock_json["uri"] = url_for("api.stockitem", warehouse=stock_entry.warehouse_id, item=item.name)
            body.append(stock_json)
        return Response(json.dumps(body), 200)