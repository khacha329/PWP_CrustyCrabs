import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from inventorymanager.models import Warehouse
from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response


class WarehouseCollection(Resource):
    

    def get(self):
        body = []
        for warehouse in Warehouse.query.all():
            warehouse_json = warehouse.serialize()
            warehouse_json["uri"] = url_for("api.warehousewarehouse", warehouse=warehouse)
            body.append(warehouse_json)

        return Response(json.dumps(body), 200)


    def post(self):
        try:
            validate(request.json, Warehouse.get_schema())
            warehouse = Warehouse()
            warehouse.deserialize(request.json)
        
            db.session.add(warehouse)
            db.session.commit()

        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "Warehouse already exists")

        return Response(status=201, headers={
            "Location": url_for("api.warehouseitem", warehouse=warehouse)
        })
    



class WarehouseManagement(Resource):
    
    def get(self, warehouse):
        pass

    def put(self, warehouse : Warehouse):
        try:
            validate(request.json, Warehouse.get_schema())
            warehouse.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "warehouse with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    def delete(self, warehouse : Warehouse):
        db.session.delete(warehouse)
        db.session.commit()

        return Response(status=204) 