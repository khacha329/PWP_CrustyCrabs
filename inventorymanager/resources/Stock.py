import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from inventorymanager.models import Stock
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


    def post(self):
        try:
            validate(request.json, Stock.get_schema())
            stock = Stock()
            Stock.deserialize(request.json)
        
            db.session.add(stock)
            db.session.commit()
            
        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "stock already exists")
        #if api fails after this line, resource will be added to db anyway
        return Response(status=201, headers={
            "Location": url_for("api.stockcollection", stock=stock)
        })
    



class StockManagement(Resource):
    
    def get(self, stock):
        pass
        #This queries stock by id. maybe change it to query by name or smthg?
    def put(self, stock : Stock):
        try:
            validate(request.json, Stock.get_schema())
            Stock.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "stock with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    def delete(self, stock : Stock):
        db.session.delete(stock)
        db.session.commit()

        return Response(status=204) 