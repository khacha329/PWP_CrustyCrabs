import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from inventorymanager.models import Warehouse, Location, require_admin_key, require_warehouse_key
from inventorymanager import db
from inventorymanager import cache
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response, request_path_cache_key


class WarehouseCollection(Resource):
    

    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        body = []
        for warehouse in Warehouse.query.all():
            warehouse_json = warehouse.serialize()
            warehouse_json["uri"] = url_for("api.warehouseitem", warehouse=warehouse.warehouse_id)
            body.append(warehouse_json)

        return Response(json.dumps(body), 200)

    # @require_admin_key
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
        #if api fails after this line, resource will be added to db anyway
        return Response(status=201, headers={
            "Location": url_for("api.warehouseitem", warehouse=warehouse.warehouse_id)
        })
    



class WarehouseItem(Resource):
    
    def get(self, warehouse):
        warehouse = Warehouse.query.get(warehouse)
        if not warehouse:
            return create_error_response(404, "Warehouse doesn't exist")
        location = Location.query.get(warehouse.location_id)
        location_json = location.serialize()
    # Retrieve the stock entry based on warehouse ID and item ID
        warehouse_json = warehouse.serialize()
        warehouse_json["uri"] = url_for("api.warehouseitem", warehouse=warehouse.warehouse_id)
        body = []
        body.append(warehouse_json)
        body.append(location_json)
        return Response(json.dumps(body), 200)
        #This queries warehouse by id. maybe change it to query by name or smthg?
    
    @require_warehouse_key
    def put(self, warehouse : Warehouse):
        warehouse = Warehouse.query.get(warehouse)
        if not warehouse:
            return create_error_response(404, "Warehouse doesn't exist")
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

    @require_warehouse_key
    def delete(self, warehouse : Warehouse):
        warehouse = Warehouse.query.get(warehouse)
        if not warehouse:
            return create_error_response(404, "Warehouse doesn't exist")
        db.session.delete(warehouse)
        db.session.commit()

        return Response(status=204) 