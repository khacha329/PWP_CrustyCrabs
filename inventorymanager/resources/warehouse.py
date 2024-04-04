"""
This module contains the resources for the warehouse endpoints.
"""

import json
import os

from flasgger import swag_from
from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db, cache
from inventorymanager.builder import InventoryManagerBuilder
from inventorymanager.models import Warehouse
from inventorymanager.constants import DOC_FOLDER
from inventorymanager.utils import create_error_response, request_path_cache_key
from inventorymanager.constants import (
    NAMESPACE,
    LINK_RELATIONS_URL,
    WAREHOUSE_PROFILE,
    MASON
)

class WarehouseCollection(Resource):
    """
    Resource for the collection of warehouses, provides GET and POST methods
    /warehouses/
    """
    
    @swag_from(os.getcwd() + f"{DOC_FOLDER}warehouse/collection/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        """Returns a list of all warehouses in the database

        :return: Response
        """
        self_url = url_for("api.warehousecollection")
        body = InventoryManagerBuilder(warehouses=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        
        for warehouse_object in Warehouse.query.all():
            warehouse = InventoryManagerBuilder(warehouse_object.serialize())
            warehouse.add_control("self", url_for("api.warehouseitem", warehouse=warehouse_object))
            warehouse.add_control("profile", WAREHOUSE_PROFILE)
            warehouse.add_control_all_stock_warehouse(warehouse=warehouse_object)
            body["warehouses"].append(warehouse)
        
        body.add_control_post(
            "add-warehouse", 
            "Add new warehouse", 
            url_for("api.warehousecollection"),
            Warehouse.get_schema()
        )

        body.add_control_all_locations()
        body.add_control_all_items()
        

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}warehouse/collection/post.yml")
    def post(self):
        """Adds a new warehouse to the database

        :return: Response
        """
        try:
            validate(request.json, Warehouse.get_schema())
            warehouse = Warehouse()
            warehouse.deserialize(request.json)

            db.session.add(warehouse)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return abort(409, "Warehouse already exists")

        self._clear_cache()
        return Response(
            status=201,
            headers={"Location": url_for("api.warehouseitem", warehouse=warehouse)},
        )

    def _clear_cache(self):
        cache.delete(
            request.path
        )

class WarehouseItem(Resource):
    """
    Resource for a single warehouse, provides GET, PUT and DELETE methods
    /warehouses/<warehouse:warehouse>/
    """
    
    @swag_from(os.getcwd() + f"{DOC_FOLDER}warehouse/item/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, warehouse: Warehouse):
        """returns a single warehouse in the database with its location details

        :param warehouse: warehouse id of the warehouse to return
        :return: Response
        """

        # location = warehouse.location
        # location_json = location.serialize()
        # # Retrieve the stock entry based on warehouse ID and item ID
        # warehouse_json = warehouse.serialize()

        self_url = url_for("api.warehouseitem", warehouse=warehouse)
        body = InventoryManagerBuilder(warehouse.serialize())
        
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", WAREHOUSE_PROFILE)
        body.add_control("collection", url_for("api.warehousecollection"))
        body.add_control_put("Modify this warehouse", self_url, Warehouse.get_schema())
        body.add_control_delete("Delete this warehouse", self_url)
        body.add_control_all_stock_warehouse(warehouse=warehouse)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}warehouse/item/put.yml")
    def put(self, warehouse: Warehouse):
        """updates a single warehouse in the database

        :param warehouse: warehouse
        :return: Response
        """
        try:
            validate(request.json, Warehouse.get_schema())
            warehouse.deserialize(request.json)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                "Already exists",
                "warehouse with id '{}' already exists.".format(
                    request.json["warehouse_id"]
                ),
            )

        self._clear_cache()
        return Response(status=204)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}warehouse/item/delete.yml")
    def delete(self, warehouse: Warehouse):
        """deletes a single warehouse in the database

        :param warehouse: warehouse id of the warehouse to delete
        :return: Response
        """
        db.session.delete(warehouse)
        db.session.commit()

        self._clear_cache()
        return Response(status=204)

    def _clear_cache(self):
        collection_path = url_for("api.warehousecollection ")
        cache.delete_many(
            collection_path,
            request.path
        )